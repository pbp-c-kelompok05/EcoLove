from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from .models import Education, Event, EventRegistration


class ModuleExtensionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('manager', password='password')
        cls.reader = User.objects.create_user('reader', password='password')
        cls.other = User.objects.create_user('another', password='password')
        cls.staff = User.objects.create_user('staff-member', password='password', is_staff=True)
        cls.event = Event.objects.create(
            title='Clothing Swap Jakarta', category='reuse', creator=cls.admin,
            starts_at=timezone.now() + timedelta(days=3),
            ends_at=timezone.now() + timedelta(days=3, hours=2),
            location='Jakarta Selatan', description='Mari berbagi pakaian.',
        )
        cls.article = Education.objects.create(
            title='Rawat linen', category='reuse', author=cls.admin,
            summary='Pakai lebih lama.', body='## Pilah pakaian\nPisahkan warna.\n\n- Cuci lembut\n- Jemur di tempat teduh',
        )

    def participation_url(self, event=None):
        return reverse('events:event_participation', args=[(event or self.event).pk])

    def test_registration_requires_auth_and_post(self):
        url = self.participation_url()
        self.assertRedirects(self.client.post(url), reverse('login'))
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 401)
        self.client.force_login(self.reader)
        for method in ('get', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        self.assertFalse(EventRegistration.objects.exists())

    def test_registration_is_idempotent_and_cannot_spoof_another_user(self):
        self.client.force_login(self.reader)
        for _ in range(2):
            response = self.client.post(self.participation_url(), {'user': self.other.pk}, follow=True)
            self.assertContains(response, 'Kamu sudah terdaftar.')
            self.assertContains(response, 'Batalkan keikutsertaan')
        registration = EventRegistration.objects.get()
        self.assertEqual(registration.user, self.reader)
        data = self.client.get(reverse('events:event_detail', args=[self.event.pk]), {'format': 'json'}).json()
        self.assertTrue(data['is_registered'])
        self.assertNotIn('registrations', data)
        self.client.force_login(self.other)
        self.assertContains(self.client.get(reverse('events:event_detail', args=[self.event.pk])), 'Daftar kegiatan')

    def test_registration_unique_constraint(self):
        EventRegistration.objects.create(event=self.event, user=self.reader)
        with self.assertRaises(IntegrityError), transaction.atomic():
            EventRegistration.objects.create(event=self.event, user=self.reader)

    def test_cancel_is_idempotent_and_only_affects_current_user(self):
        EventRegistration.objects.create(event=self.event, user=self.reader)
        EventRegistration.objects.create(event=self.event, user=self.other)
        self.client.force_login(self.reader)
        for _ in range(2):
            response = self.client.post(self.participation_url(), {'action': 'cancel'}, follow=True)
            self.assertContains(response, 'Keikutsertaan dibatalkan.')
        self.assertEqual(list(EventRegistration.objects.values_list('user_id', flat=True)), [self.other.pk])

    def test_closed_events_reject_new_registration_and_keep_existing_state(self):
        self.client.force_login(self.reader)
        for end_delta in (timedelta(hours=1), -timedelta(hours=1)):
            Event.objects.filter(pk=self.event.pk).update(
                starts_at=timezone.now() - timedelta(hours=2), ends_at=timezone.now() + end_delta)
            response = self.client.post(self.participation_url(), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 409)
            self.assertFalse(EventRegistration.objects.exists())
            response = self.client.get(reverse('events:event_detail', args=[self.event.pk]))
            self.assertContains(response, 'disabled>Pendaftaran ditutup')
        EventRegistration.objects.create(event=self.event, user=self.reader)
        response = self.client.post(self.participation_url(), follow=True)
        self.assertContains(response, 'Kamu sudah terdaftar.')
        self.assertEqual(EventRegistration.objects.count(), 1)
        self.client.post(self.participation_url(), {'action': 'cancel'})
        self.assertFalse(EventRegistration.objects.exists())

    def test_registration_boundary_is_start_time(self):
        from unittest.mock import patch
        self.client.force_login(self.reader)
        with patch('events.models.timezone.now', return_value=self.event.starts_at):
            self.assertFalse(self.event.registration_open)
            self.assertEqual(self.client.post(self.participation_url(), HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 409)

    def test_invalid_action_missing_event_and_csrf(self):
        import uuid
        self.client.force_login(self.reader)
        self.assertEqual(self.client.post(self.participation_url(), {'action': 'grant-admin'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 400)
        self.assertEqual(self.client.post(reverse('events:event_participation', args=[uuid.uuid4()])).status_code, 404)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.reader)
        self.assertEqual(client.post(self.participation_url()).status_code, 403)
        client.get(reverse('events:event_detail', args=[self.event.pk]))
        token = client.cookies['csrftoken'].value
        response = client.post(self.participation_url(), HTTP_X_CSRFTOKEN=token, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EventRegistration.objects.count(), 1)
        self.assertEqual(client.post(self.participation_url(), {'action': 'cancel'}).status_code, 403)

    def test_management_and_confirmation_permissions(self):
        for actor, expected in ((None, 401), (self.reader, 403), (self.staff, 403), (self.admin, 200)):
            self.client.logout()
            if actor:
                self.client.force_login(actor)
            for kind, obj in (('event', self.event), ('education', self.article)):
                self.assertEqual(self.client.get(reverse(f'events:{kind}_manage')).status_code, expected)
                self.assertEqual(self.client.get(reverse(f'events:{kind}_delete_confirm', args=[obj.pk])).status_code, expected)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        self.assertTrue(Education.objects.filter(pk=self.article.pk).exists())

    def test_management_search_and_confirmed_delete(self):
        self.client.force_login(self.admin)
        for kind, obj in (('event', self.event), ('education', self.article)):
            listing = reverse(f'events:{kind}_manage')
            response = self.client.get(listing, {'q': obj.title})
            self.assertContains(response, obj.title)
            self.assertContains(response, reverse(f'events:{kind}_edit', args=[obj.pk]))
            self.assertNotContains(self.client.get(listing, {'q': 'no-such-title'}), f'>{obj.title}</a>')
            confirmation = reverse(f'events:{kind}_delete_confirm', args=[obj.pk])
            self.assertContains(self.client.get(confirmation), 'Ya, hapus')
            self.assertEqual(self.client.post(confirmation).status_code, 405)
            self.assertEqual(self.client.post(listing).status_code, 405)
            if kind == 'event':
                EventRegistration.objects.create(event=obj, user=self.reader)
            response = self.client.post(reverse(f'events:{kind}_delete', args=[obj.pk]), follow=True)
            self.assertContains(response, 'berhasil dihapus.')
            self.assertFalse(type(obj).objects.filter(pk=obj.pk).exists())
        self.assertFalse(EventRegistration.objects.exists())
        self.assertTrue(User.objects.filter(pk=self.reader.pk).exists())

    def test_location_search_and_guest_registration_prompt(self):
        result = self.client.get(reverse('events:event_list'), {'q': 'Jakarta Selatan', 'format': 'json'}).json()
        self.assertEqual([entry['id'] for entry in result['results']], [str(self.event.pk)])
        html = self.client.get(reverse('events:event_detail', args=[self.event.pk]))
        self.assertContains(html, 'Masuk untuk mendaftar')
        self.assertNotContains(html, 'Batalkan keikutsertaan')

    def test_structured_article_supports_lists_headings_and_escapes_html(self):
        self.article.body += '\n\n1. Mulai pelan\n2. Ulangi\n\n### Catatan\n<script>alert(1)</script>'
        self.article.save()
        response = self.client.get(reverse('events:education_detail', args=[self.article.pk]))
        for snippet in ('<h2>Pilah pakaian</h2>', '<ul><li>Cuci lembut</li>', '<ol><li>Mulai pelan</li>', '<h3>Catatan</h3>', '&lt;script&gt;'):
            self.assertContains(response, snippet)
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_module_links_and_local_static_assets_resolve(self):
        class Assets(HTMLParser):
            def __init__(self):
                super().__init__()
                self.paths = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                for key in ('href', 'src', 'action'):
                    if attrs.get(key):
                        self.paths.append(attrs[key])

        self.client.force_login(self.admin)
        for kind, obj in (('event', self.event), ('education', self.article)):
            for action, args in (('list', []), ('detail', [obj.pk]), ('create', []), ('edit', [obj.pk]), ('manage', []), ('delete_confirm', [obj.pk])):
                response = self.client.get(reverse(f'events:{kind}_{action}', args=args))
                self.assertEqual(response.status_code, 200)
                parser = Assets()
                parser.feed(response.content.decode())
                for path in parser.paths:
                    parsed = urlsplit(path)
                    if parsed.netloc or not parsed.path:
                        continue
                    if parsed.path.startswith('/static/'):
                        self.assertIsNotNone(finders.find(parsed.path.removeprefix('/static/')), path)
                    else:
                        resolve(parsed.path)
