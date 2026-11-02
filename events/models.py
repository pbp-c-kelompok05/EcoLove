import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

CATEGORIES = [('reuse', 'Reuse & Repair'), ('waste', 'Minim Sampah'), ('community', 'Komunitas'), ('lifestyle', 'Gaya Hidup')]

class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Judul', max_length=200)
    category = models.CharField('Kategori', max_length=20, choices=CATEGORIES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

class Event(Content):
    description = models.TextField('Deskripsi umum')
    starts_at = models.DateTimeField('Mulai (WIB)')
    ends_at = models.DateTimeField('Selesai (WIB)')
    location = models.CharField('Lokasi umum / platform', max_length=255)
    is_online = models.BooleanField('Acara online', default=False)
    organizer_contact = models.CharField('Kontak penyelenggara (khusus pengguna login)', max_length=255, blank=True)
    meeting_link = models.URLField(
        'Link pertemuan (khusus pengguna login)', blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )
    image = models.ImageField('Gambar', upload_to='event_images/', blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_events')

    class Meta:
        ordering = ['starts_at', 'id']
        constraints = [models.CheckConstraint(condition=Q(ends_at__gte=F('starts_at')), name='event_end_after_start')]

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({'ends_at': 'Waktu selesai tidak boleh sebelum waktu mulai.'})

    @property
    def safe_meeting_link(self):
        """Render only HTTP(S), even for legacy/imported rows bypassing forms."""
        if not self.meeting_link:
            return ''
        try:
            URLValidator(schemes=['http', 'https'])(self.meeting_link)
        except ValidationError:
            return ''
        return self.meeting_link

    @property
    def registration_open(self):
        return self.starts_at > timezone.now()

    @property
    def status_label(self):
        now = timezone.now()
        if self.ends_at < now:
            return 'Selesai'
        return 'Mendatang' if self.starts_at > now else 'Berlangsung'

class Education(Content):
    summary = models.TextField('Ringkasan', max_length=500)
    body = models.TextField('Isi artikel')
    image = models.ImageField('Gambar', upload_to='education_images/', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='education_articles')

    class Meta:
        ordering = ['-created_at', 'id']

class EventComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_comments')
    body = models.TextField('Komentar', max_length=2000)
    image = models.ImageField('Foto (opsional)', upload_to='event_images/comments/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']


class EventRegistration(models.Model):
    """One participation per account; no extra personal data is collected."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['event', 'user'], name='unique_event_participant')]
