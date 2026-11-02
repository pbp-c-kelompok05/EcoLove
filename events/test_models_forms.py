"""Domain constraints and public form contracts, independent of view success paths."""
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from .forms import EducationForm, EventCommentForm, EventForm
from .models import Education, Event, EventComment, EventRegistration


def event_payload(**changes):
    return {
        'title': 'Aksi lingkungan', 'description': 'Belajar bersama',
        'category': 'reuse', 'location': 'Depok',
        'starts_at': '2027-01-10T09:00', 'ends_at': '2027-01-10T11:00',
        **changes,
    }


def education_payload(**changes):
    return {
        'title': 'Panduan kompos', 'summary': 'Langkah sederhana',
        'body': '## Mulai\nGunakan sisa dapur.', 'category': 'waste', **changes,
    }


class ContentModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('domain-owner')
        cls.reader = get_user_model().objects.create_user('domain-reader')
        cls.start = timezone.now() + timedelta(days=1)
        cls.event = Event.objects.create(
            title='Bersih taman', description='Bersama warga', category='community',
            location='Taman', starts_at=cls.start, ends_at=cls.start + timedelta(hours=2),
            creator=cls.owner,
        )
        cls.article = Education.objects.create(
            title='Panduan', summary='Ringkas', body='Materi', category='waste', author=cls.owner,
        )

    def test_content_persists_uuid_defaults_ownership_and_timestamps(self):
        for obj, related in ((self.event, 'created_events'), (self.article, 'education_articles')):
            with self.subTest(model=type(obj).__name__):
                obj.refresh_from_db()
                self.assertIsInstance(obj.pk, UUID)
                self.assertEqual(str(obj), obj.title)
                self.assertFalse(obj.image)
                self.assertTrue(timezone.is_aware(obj.created_at))
                self.assertGreaterEqual(obj.updated_at, obj.created_at)
                self.assertIn(obj, getattr(self.owner, related).all())
                created = obj.created_at
                later = obj.updated_at + timedelta(seconds=1)
                with patch('django.utils.timezone.now', return_value=later):
                    obj.title = 'Diperbarui'
                    obj.save()
                obj.refresh_from_db()
                self.assertEqual(obj.created_at, created)
                self.assertEqual(obj.updated_at, later)
        self.assertFalse(self.event.is_online)
        self.assertEqual(self.event.organizer_contact, '')
        self.assertEqual(self.event.meeting_link, '')
        self.assertEqual(self.event.get_category_display(), 'Komunitas')

    def test_model_required_fields_and_invalid_category(self):
        for obj, required in ((self.event, ('title', 'description', 'location', 'category')),
                              (self.article, ('title', 'summary', 'body', 'category'))):
            for field in required:
                with self.subTest(model=type(obj).__name__, field=field):
                    original = getattr(obj, field)
                    setattr(obj, field, '')
                    with self.assertRaises(ValidationError) as error:
                        obj.full_clean()
                    self.assertIn(field, error.exception.message_dict)
                    setattr(obj, field, original)
            obj.category = 'unknown'
            with self.assertRaises(ValidationError) as error:
                obj.full_clean()
            self.assertIn('category', error.exception.message_dict)

    def test_database_rejects_reversed_dates_even_when_validation_is_bypassed(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.filter(pk=self.event.pk).update(ends_at=self.start - timedelta(seconds=1))
        self.event.refresh_from_db()
        self.assertGreaterEqual(self.event.ends_at, self.event.starts_at)

    def test_equal_dates_are_valid_and_status_boundaries_are_explicit(self):
        self.event.ends_at = self.event.starts_at
        self.event.full_clean()
        for instant, label, open_ in (
            (self.start - timedelta(microseconds=1), 'Mendatang', True),
            (self.start, 'Berlangsung', False),
            (self.start + timedelta(microseconds=1), 'Selesai', False),
        ):
            with self.subTest(instant=instant), patch('events.models.timezone.now', return_value=instant):
                self.assertEqual(self.event.status_label, label)
                self.assertEqual(self.event.registration_open, open_)

    def test_content_owners_are_protected_from_deletion(self):
        with self.assertRaises(ProtectedError):
            self.owner.delete()
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        self.assertTrue(Education.objects.filter(pk=self.article.pk).exists())

    def test_deleting_reader_cascades_only_their_comments_and_registrations(self):
        EventComment.objects.create(event=self.event, user=self.reader, body='Ikut')
        EventRegistration.objects.create(event=self.event, user=self.reader)
        kept = EventComment.objects.create(event=self.event, user=self.owner, body='Tetap')
        self.reader.delete()
        self.assertEqual(list(self.event.comments.all()), [kept])
        self.assertFalse(self.event.registrations.exists())
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        self.assertTrue(Education.objects.filter(pk=self.article.pk).exists())


class ContentFormTests(TestCase):
    def test_valid_forms_save_without_accepting_ownership_from_input(self):
        owner = get_user_model().objects.create_user('form-owner')
        for form, owner_field in (
            (EventForm(data=event_payload(creator=999)), 'creator'),
            (EducationForm(data=education_payload(author=999)), 'author'),
        ):
            with self.subTest(form=type(form).__name__):
                self.assertTrue(form.is_valid(), form.errors)
                self.assertNotIn(owner_field, form.fields)
                obj = form.save(commit=False)
                setattr(obj, owner_field, owner)
                obj.save()
                obj.refresh_from_db()
                self.assertEqual(getattr(obj, owner_field), owner)
                self.assertEqual(obj.title, form.cleaned_data['title'])

    def test_missing_required_fields_have_errors_and_accessible_feedback(self):
        for form_class, names in (
            (EventForm, ('title', 'description', 'category', 'location', 'starts_at', 'ends_at')),
            (EducationForm, ('title', 'summary', 'body', 'category')),
            (EventCommentForm, ('body',)),
        ):
            form = form_class(data={})
            self.assertFalse(form.is_valid())
            self.assertEqual(set(form.errors), set(names))
            for name in names:
                self.assertEqual(form.errors.as_data()[name][0].code, 'required')
                self.assertEqual(form.fields[name].widget.attrs['aria-invalid'], 'true')
                self.assertIn(f'id_{name}_errors', form.fields[name].widget.attrs['aria-describedby'])

    def test_invalid_dates_and_reverse_range_are_rejected(self):
        for changes, field in (
            ({'starts_at': 'not-a-date'}, 'starts_at'),
            ({'ends_at': '2027-02-30T10:00'}, 'ends_at'),
            ({'ends_at': '2027-01-10T08:59'}, 'ends_at'),
        ):
            with self.subTest(changes=changes):
                form = EventForm(data=event_payload(**changes))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_datetime_conversion_uses_wib_even_under_another_active_timezone(self):
        with timezone.override('America/New_York'):
            form = EventForm(data=event_payload(ends_at='2027-01-10T09:00'))
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['starts_at'], datetime(2027, 1, 10, 2, tzinfo=dt_timezone.utc))
            self.assertEqual(form.cleaned_data['ends_at'], form.cleaned_data['starts_at'])

    def test_text_length_boundaries_and_category_choices(self):
        for form_class, payload, field, limit in (
            (EventForm, event_payload, 'title', 200),
            (EventForm, event_payload, 'location', 255),
            (EventForm, event_payload, 'organizer_contact', 255),
            (EducationForm, education_payload, 'title', 200),
            (EducationForm, education_payload, 'summary', 500),
            (EventCommentForm, lambda **kw: {'body': 'Komentar', **kw}, 'body', 2000),
        ):
            with self.subTest(form=form_class.__name__, field=field):
                self.assertTrue(form_class(data=payload(**{field: 'x' * limit})).is_valid())
                invalid = form_class(data=payload(**{field: 'x' * (limit + 1)}))
                self.assertFalse(invalid.is_valid())
                self.assertEqual(invalid.errors.as_data()[field][0].code, 'max_length')
        for form_class, payload in ((EventForm, event_payload), (EducationForm, education_payload)):
            invalid = form_class(data=payload(category='invented'))
            self.assertFalse(invalid.is_valid())
            self.assertEqual(invalid.errors.as_data()['category'][0].code, 'invalid_choice')

    def test_meeting_links_accept_only_valid_http_and_https(self):
        for value in ('https://example.test/meet', 'http://example.test/meet', ''):
            self.assertTrue(EventForm(data=event_payload(meeting_link=value)).is_valid())
        for value in ('not a URL', 'javascript:alert(1)', 'ftp://example.test/file', 'data:text/html,evil'):
            with self.subTest(value=value):
                form = EventForm(data=event_payload(meeting_link=value))
                self.assertFalse(form.is_valid())
                self.assertIn('meeting_link', form.errors)

    def test_plain_text_is_trimmed_and_remains_escaped_when_form_is_redisplayed(self):
        script = '<script>alert("x")</script>'
        form = EducationForm(data=education_payload(title='  Panduan  ', body=script))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['title'], 'Panduan')
        self.assertEqual(form.cleaned_data['body'], script)
        self.assertNotIn(script, form.as_p())
        self.assertIn('&lt;script&gt;', form.as_p())

    def test_optional_images_reject_disguised_non_images(self):
        for form_class, payload in ((EventForm, event_payload), (EducationForm, education_payload)):
            with self.subTest(form=form_class.__name__):
                form = form_class(data=payload(), files={
                    'image': SimpleUploadedFile('photo.png', b'<script>evil</script>', content_type='image/png'),
                })
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors.as_data()['image'][0].code, 'invalid_image')

    def test_prefixed_forms_and_forms_without_ids_render_accessibly(self):
        form = EducationForm(prefix='article')
        self.assertIn('id_article-body_helptext', form.fields['body'].widget.attrs['aria-describedby'])
        self.assertIn('id_article-body_errors', form.fields['body'].widget.attrs['aria-describedby'])
        no_ids = EducationForm(auto_id=False)
        self.assertTrue(no_ids.as_p())
        self.assertNotIn('aria-describedby', no_ids.fields['title'].widget.attrs)
