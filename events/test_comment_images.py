from datetime import timedelta
from io import BytesIO
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .forms import EventCommentAdminForm
from .models import Event, EventComment


class CommentImageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('photo-admin', password='password')
        cls.user = User.objects.create_user('photo-user', password='password')
        cls.other = User.objects.create_user('photo-other', password='password')
        cls.event = Event.objects.create(
            title='Workshop foto', category='reuse', creator=cls.admin,
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=2),
            location='Depok', description='Contoh kegiatan.',
        )

    def setUp(self):
        self.uploads = tempfile.TemporaryDirectory()
        self.addCleanup(self.uploads.cleanup)
        settings = override_settings(MEDIA_ROOT=self.uploads.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.client.force_login(self.user)
        self.url = reverse('events:comment_add', args=[self.event.pk])

    def upload(self, size=(300, 100), fmt='PNG', exif=None, transparent=False):
        image = Image.new('RGBA' if transparent else 'RGB', size, (0, 0, 0, 0) if transparent else 'green')
        if not transparent:
            # Only the central square should survive a 3:1 center crop.
            image.paste('red', (0, 0, size[0] // 3, size[1]))
            image.paste('blue', (size[0] * 2 // 3, 0, size[0], size[1]))
        output = BytesIO()
        image.save(output, format=fmt, **({'exif': exif} if exif is not None else {}))
        return SimpleUploadedFile('photo.' + fmt.lower(), output.getvalue(), content_type='image/' + fmt.lower())

    def submit(self, image=None, body='Foto kegiatan', **extra):
        return self.client.post(self.url, {'body': body, **({'image': image} if image else {}), **extra})

    def test_landscape_is_really_stored_as_center_cropped_square(self):
        response = self.submit(self.upload())
        self.assertEqual(response.status_code, 201)
        comment = EventComment.objects.get()
        self.assertEqual(comment.user, self.user)
        self.assertTrue(comment.image.name.startswith('event_images/comments/'))
        self.assertTrue(comment.image.name.endswith('.jpg'))
        self.assertContains(self.client.get(reverse('events:event_detail', args=[self.event.pk])), comment.image.url)
        self.assertIn('ee-comment-photo', response.json()['html'])
        with comment.image.open('rb') as stored, Image.open(stored) as image:
            self.assertEqual(image.size, (100, 100))
            self.assertEqual(image.format, 'JPEG')
            for point in ((5, 50), (50, 50), (95, 50)):
                red, green, blue = image.getpixel(point)
                self.assertGreater(green, red + 60)
                self.assertGreater(green, blue + 60)

    def test_portrait_large_upload_is_bounded_and_square(self):
        response = self.submit(self.upload(size=(1200, 1800)))
        self.assertEqual(response.status_code, 201)
        with EventComment.objects.get().image.open('rb') as stored, Image.open(stored) as image:
            self.assertEqual(image.size, (1024, 1024))

    def test_exif_rotation_is_applied_and_metadata_is_removed(self):
        source = Image.new('RGB', (160, 80), 'red')
        source.paste('blue', (80, 0, 160, 80))
        exif = Image.Exif()
        exif[274] = 6  # Rotate 90 degrees clockwise for display.
        exif[315] = 'SHOULD-NOT-BE-STORED'
        raw = BytesIO()
        source.save(raw, format='JPEG', exif=exif)
        response = self.submit(SimpleUploadedFile('rotated.jpg', raw.getvalue(), content_type='image/jpeg'))
        self.assertEqual(response.status_code, 201)
        with EventComment.objects.get().image.open('rb') as stored, Image.open(stored) as image:
            self.assertEqual(image.size, (80, 80))
            self.assertGreater(image.getpixel((40, 5))[0], 200)
            self.assertGreater(image.getpixel((40, 75))[2], 200)
            self.assertFalse(image.getexif())

    def test_transparent_png_has_off_white_background(self):
        self.assertEqual(self.submit(self.upload((80, 100), transparent=True)).status_code, 201)
        with EventComment.objects.get().image.open('rb') as stored, Image.open(stored) as image:
            self.assertEqual(image.mode, 'RGB')
            self.assertEqual(image.size, (80, 80))
            expected = (250, 248, 241)
            self.assertTrue(all(abs(actual - target) <= 2 for actual, target in zip(image.getpixel((40, 40)), expected)))

    def test_text_only_comments_still_work_and_caption_is_required(self):
        self.assertEqual(self.submit(body='Tanpa foto').status_code, 201)
        self.assertFalse(EventComment.objects.get().image)
        response = self.submit(self.upload(), body=' ')
        self.assertEqual(response.status_code, 400)
        self.assertIn('body', response.json()['errors'])
        self.assertEqual(EventComment.objects.count(), 1)

    def test_invalid_format_corruption_and_oversized_upload_are_rejected(self):
        invalid = [
            SimpleUploadedFile('bad.jpg', b'not an image', content_type='image/jpeg'),
            SimpleUploadedFile('script.svg', b'<svg onload="alert(1)"/>', content_type='image/svg+xml'),
            self.upload(fmt='GIF'),
            SimpleUploadedFile('large.jpg', b'x' * (5 * 1024 * 1024 + 1), content_type='image/jpeg'),
        ]
        for upload in invalid:
            with self.subTest(name=upload.name):
                response = self.submit(upload)
                self.assertEqual(response.status_code, 400)
                self.assertIn('image', response.json()['errors'])
        self.assertFalse(EventComment.objects.exists())

    def test_pixel_limit_is_checked_before_decoding_full_image(self):
        # Use a small threshold to exercise the resource guard without allocating
        # a 20-megapixel image inside the test runner.
        with patch('events.comment_images.MAX_IMAGE_PIXELS', 99):
            response = self.submit(self.upload(size=(10, 10)))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors']['image'][0]['code'], 'image_resolution')
        self.assertFalse(EventComment.objects.exists())

    def test_auth_csrf_and_ownership_are_preserved_with_uploads(self):
        self.client.logout()
        self.assertEqual(self.submit(self.upload()).status_code, 401)
        self.client.force_login(self.user)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post(self.url, {'body': 'Foto', 'image': self.upload()}).status_code, 403)
        self.assertFalse(EventComment.objects.exists())
        self.assertEqual(self.submit(self.upload(), user=self.other.pk).status_code, 201)
        comment = EventComment.objects.get()
        self.assertEqual(comment.user, self.user)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('events:comment_delete', args=[comment.pk])).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('events:comment_delete', args=[comment.pk])).status_code, 200)

    def test_guest_responses_omit_comment_photos_and_authenticated_json_includes_them(self):
        self.submit(self.upload())
        comment = EventComment.objects.get()
        url = reverse('events:event_detail', args=[self.event.pk])
        data = self.client.get(url, {'format': 'json'}).json()
        self.assertEqual(data['comments'][0]['image'], comment.image.url)
        self.client.logout()
        self.assertNotContains(self.client.get(url), comment.image.url)
        self.assertNotIn('comments', self.client.get(url, {'format': 'json'}).json())

    def test_admin_form_uses_the_same_crop_and_preserves_existing_image(self):
        form = EventCommentAdminForm(
            data={'body': 'Admin upload', 'event': self.event.pk, 'user': self.user.pk},
            files={'image': self.upload()},
        )
        self.assertTrue(form.is_valid(), form.errors)
        comment = form.save()
        original = comment.image.name
        with comment.image.open('rb') as stored, Image.open(stored) as image:
            self.assertEqual(image.size, (100, 100))
        edited = EventCommentAdminForm(
            data={'body': 'Teks diperbarui', 'event': self.event.pk, 'user': self.user.pk}, instance=comment,
        )
        self.assertTrue(edited.is_valid(), edited.errors)
        self.assertEqual(edited.save().image.name, original)
