"""Request-level journeys and failure paths supplementing the existing AJAX suite."""
from datetime import timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Education, Event
from .test_models_forms import education_payload, event_payload

AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class ContentWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser('journey-admin', password='test-password')
        cls.reader = get_user_model().objects.create_user('journey-reader')

    def test_plain_html_crud_journeys_show_persisted_changes_and_validation(self):
        self.client.force_login(self.admin)
        for kind, model, payload in (
            ('event', Event, event_payload), ('education', Education, education_payload),
        ):
            with self.subTest(kind=kind):
                list_url = reverse(f'events:{kind}_list')
                create_url = reverse(f'events:{kind}_create')
                create = self.client.get(create_url)
                self.assertTemplateUsed(create, 'events/form.html')
                invalid = self.client.post(create_url, payload(title=''))
                self.assertEqual(invalid.status_code, 200)
                self.assertFormError(invalid.context['form'], 'title', 'This field is required.')
                self.assertEqual(model.objects.count(), 0)
                created = self.client.post(create_url, payload(), follow=True)
                obj = model.objects.get()
                detail_url = reverse(f'events:{kind}_detail', args=[obj.pk])
                self.assertEqual(created.redirect_chain, [(detail_url, 302)])
                self.assertTemplateUsed(created, 'events/detail.html')
                self.assertContains(created, obj.title)
                self.assertContains(self.client.get(list_url), obj.title)

                edit_url = reverse(f'events:{kind}_edit', args=[obj.pk])
                old_title = obj.title
                for headers, expected in (({}, 200), (AJAX, 400)):
                    rejected = self.client.post(edit_url, payload(title=''), **headers)
                    self.assertEqual(rejected.status_code, expected)
                    if headers:
                        self.assertEqual(set(rejected.json()), {'error', 'errors'})
                        self.assertEqual(rejected.json()['errors']['title'][0]['code'], 'required')
                    else:
                        self.assertTrue(rejected.context['form'].has_error('title', 'required'))
                        self.assertContains(rejected, 'aria-invalid="true"')
                    obj.refresh_from_db()
                    self.assertEqual(obj.title, old_title)

                changed = 'Kebiasaan baru berkelanjutan'
                updated = self.client.post(edit_url, payload(title=changed), follow=True)
                self.assertEqual(updated.redirect_chain, [(detail_url, 302)])
                self.assertContains(updated, changed)
                obj.refresh_from_db()
                self.assertEqual(obj.title, changed)
                self.assertContains(self.client.get(list_url), changed)
                json_detail = self.client.get(detail_url, {'format': 'json'}).json()
                self.assertEqual(json_detail['title'], changed)
                confirmation = self.client.get(reverse(f'events:{kind}_delete_confirm', args=[obj.pk]))
                self.assertTemplateUsed(confirmation, 'events/confirm_delete.html')
                deleted = self.client.post(reverse(f'events:{kind}_delete', args=[obj.pk]), follow=True)
                self.assertEqual(deleted.redirect_chain, [(list_url, 302)])
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())
                self.assertNotContains(deleted, changed)
                self.assertEqual(self.client.get(detail_url).status_code, 404)

    def test_all_object_endpoints_return_404_without_mutating_other_content(self):
        self.client.force_login(self.admin)
        for kind in ('event', 'education'):
            for action, method in (('detail', 'get'), ('edit', 'get'), ('edit', 'post'),
                                   ('delete_confirm', 'get'), ('delete', 'post')):
                for headers in ({}, AJAX):
                    with self.subTest(kind=kind, action=action, method=method, ajax=bool(headers)):
                        response = getattr(self.client, method)(
                            reverse(f'events:{kind}_{action}', args=[uuid4()]), **headers,
                        )
                        self.assertEqual(response.status_code, 404)
        for name in ('comment_add', 'comment_delete', 'event_participation'):
            self.assertEqual(self.client.post(reverse(f'events:{name}', args=[uuid4()])).status_code, 404)
        self.assertFalse(Event.objects.exists())
        self.assertFalse(Education.objects.exists())

    def test_empty_ajax_contract_and_invalid_filter_parameters_match_html(self):
        for kind in ('event', 'education'):
            url = reverse(f'events:{kind}_list')
            for params in ({}, {'q': '<script>evil</script>', 'category': 'unknown',
                               'page': 'not-a-number', 'status': 'unknown'}):
                html = self.client.get(url, params)
                data = self.client.get(url, params, **AJAX).json()
                explicit = self.client.get(url, {**params, 'format': 'json'}).json()
                self.assertEqual(data, explicit)
                self.assertEqual(set(data), {'results', 'html', 'page', 'pages'})
                self.assertEqual((data['results'], data['page'], data['pages']), ([], 1, 1))
                self.assertEqual(html.context['page'].paginator.count, len(data['results']))
                self.assertNotContains(html, '<script>evil</script>')
                self.assertNotIn('<script>evil</script>', data['html'])

    def test_unknown_status_is_ignored_and_long_search_is_bounded(self):
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            creator=self.admin, title='x' * 200, category='reuse', description='Materi',
            location='Depok', starts_at=start, ends_at=start,
        )
        url = reverse('events:event_list')
        response = self.client.get(url, {'q': '  ' + 'x' * 220 + '  ', 'status': 'invalid'})
        self.assertEqual(response.context['query'], 'x' * 200)
        self.assertEqual(list(response.context['page']), [event])
        self.assertEqual(self.client.get(url, {'status': 'invalid'}, **AJAX).json()['results'][0]['id'], str(event.pk))

    def test_invalid_plain_participation_action_shows_feedback_without_registration(self):
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            creator=self.admin, title='Aksi', category='reuse', description='Materi',
            location='Depok', starts_at=start, ends_at=start,
        )
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse('events:event_participation', args=[event.pk]), {'action': 'grant-admin'}, follow=True,
        )
        self.assertEqual(response.redirect_chain, [(reverse('events:event_detail', args=[event.pk]), 302)])
        self.assertContains(response, 'Pilihan pendaftaran tidak valid.')
        self.assertFalse(event.registrations.exists())

    def test_list_banners_have_distinct_meaningful_alternative_text(self):
        for kind, asset, alt in (
            ('event', 'banner.svg', 'Ilustrasi kalender kegiatan lingkungan dan partisipasi komunitas'),
            ('education', 'education-banner.svg', 'Ilustrasi buku terbuka, daun, dan ide untuk belajar hidup berkelanjutan'),
        ):
            response = self.client.get(reverse(f'events:{kind}_list'))
            self.assertContains(response, f'/static/events/illustrations/{asset}')
            self.assertContains(response, f'alt="{alt}"')
            self.assertContains(response, 'class="ee-banner"', count=1)
