"""Safety guards for uploads, demo data and Django admin permissions."""
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command, CommandError
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone
from PIL import Image

from .comment_images import square_comment_image
from .forms import EventCommentForm
from .models import Education, Event, EventComment
from .templatetags.education_text import structured_text


class UploadGuardTests(SimpleTestCase):
    def test_animated_png_is_rejected_and_input_is_rewound(self):
        output = BytesIO()
        frames = [Image.new('RGB', (10, 10), color) for color in ('red', 'blue')]
        frames[0].save(output, format='PNG', save_all=True, append_images=frames[1:], duration=100, loop=0)
        upload = SimpleUploadedFile('animated.png', output.getvalue(), content_type='image/png')
        with self.assertRaises(ValidationError) as error:
            square_comment_image(upload)
        self.assertEqual(error.exception.code, 'image_animation')
        self.assertEqual(upload.tell(), 0)
        form = EventCommentForm(data={'body': 'Animasi'}, files={'image': upload})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['image'][0].code, 'image_animation')

    def test_pillow_decompression_warning_becomes_validation_error(self):
        output = BytesIO()
        Image.new('RGB', (11, 10)).save(output, format='PNG')
        upload = SimpleUploadedFile('large.png', output.getvalue(), content_type='image/png')
        with patch('PIL.Image.MAX_IMAGE_PIXELS', 100), self.assertRaises(ValidationError) as error:
            square_comment_image(upload)
        self.assertEqual(error.exception.code, 'invalid_image')
        self.assertEqual(upload.tell(), 0)

    def test_blank_article_and_switching_text_blocks_remain_safe(self):
        self.assertEqual(str(structured_text(None)), '')
        self.assertEqual(str(structured_text(' \n\n')), '')
        result = str(structured_text('One line\nnext line\n\n- <img onerror=evil>\n1. Step\n### Note\nDone'))
        self.assertIn('<p>One line next line</p>', result)
        self.assertIn('<ul><li>&lt;img onerror=evil&gt;</li></ul>', result)
        self.assertIn('<ol><li>Step</li></ol>', result)
        self.assertIn('<h3>Note</h3>', result)
        self.assertTrue(result.endswith('<p>Done</p>'))


class AdminAndSeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        cls.admin = user.objects.create_superuser('admin-contracts', password='test-password')
        cls.other_admin = user.objects.create_superuser('other-admin-contracts')
        cls.reader = user.objects.create_user('reader-contracts')
        cls.staff = user.objects.create_user('staff-contracts', is_staff=True)

    def request_for(self, actor):
        request = RequestFactory().get('/admin/')
        request.user = actor
        return request

    def test_all_registered_admin_permission_hooks_require_superuser(self):
        for model in (Event, Education, EventComment):
            registered = admin.site._registry[model]
            for actor in (self.reader, self.staff, self.admin):
                for hook in ('has_module_permission', 'has_view_permission', 'has_add_permission',
                             'has_change_permission', 'has_delete_permission'):
                    with self.subTest(model=model.__name__, actor=actor.username, hook=hook):
                        self.assertEqual(getattr(registered, hook)(self.request_for(actor)), actor.is_superuser)

    def test_admin_save_assigns_owners_and_preserves_them_on_edit(self):
        start = timezone.now() + timedelta(days=1)
        event = Event(title='Aksi', category='reuse', description='Materi', location='Taman',
                      starts_at=start, ends_at=start)
        article = Education(title='Panduan', category='reuse', summary='Ringkas', body='Isi')
        for obj, owner_field in ((event, 'creator'), (article, 'author')):
            registered = admin.site._registry[type(obj)]
            registered.save_model(self.request_for(self.admin), obj, form=None, change=False)
            obj.refresh_from_db()
            self.assertEqual(getattr(obj, owner_field), self.admin)
            obj.title = 'Updated by another superuser'
            registered.save_model(self.request_for(self.other_admin), obj, form=None, change=True)
            obj.refresh_from_db()
            self.assertEqual(getattr(obj, owner_field), self.admin)
            self.assertEqual(obj.title, 'Updated by another superuser')
        comment = EventComment(event=event, body='Moderasi')
        registered = admin.site._registry[EventComment]
        registered.save_model(self.request_for(self.admin), comment, form=None, change=False)
        self.assertEqual(comment.user, self.admin)
        comment.body = 'Diperbarui'
        registered.save_model(self.request_for(self.other_admin), comment, form=None, change=True)
        comment.refresh_from_db()
        self.assertEqual(comment.user, self.admin)
        self.assertEqual(comment.body, 'Diperbarui')

    def test_seed_rejects_missing_or_non_superuser_without_creating_data(self):
        for username in ('does-not-exist', self.reader.username, self.staff.username):
            with self.subTest(username=username), self.assertRaises(CommandError):
                call_command('seed_events', username=username, stdout=StringIO())
            self.assertFalse(Event.objects.exists())
            self.assertFalse(Education.objects.exists())
