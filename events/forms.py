from zoneinfo import ZoneInfo
from django import forms
from django.utils import timezone
from .models import Event, Education, EventComment

WIB = ZoneInfo('Asia/Jakarta')

class WIBDateTimeField(forms.DateTimeField):
    def prepare_value(self, value):
        with timezone.override(WIB):
            return super().prepare_value(value)

    def to_python(self, value):
        with timezone.override(WIB):
            return super().to_python(value)

class EventForm(forms.ModelForm):
    starts_at = WIBDateTimeField(label='Mulai (WIB, UTC+7)', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))
    ends_at = WIBDateTimeField(label='Selesai (WIB, UTC+7)', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))

    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'starts_at', 'ends_at', 'location', 'is_online', 'organizer_contact', 'meeting_link', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 6})}
        help_texts = {'description': 'Informasi publik: jangan tulis kontak atau link pertemuan di sini.', 'location': 'Nama tempat/kota atau platform; simpan link privat di kolom link pertemuan.'}

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['title', 'summary', 'body', 'category', 'image']
        widgets = {'summary': forms.Textarea(attrs={'rows': 3}), 'body': forms.Textarea(attrs={'rows': 12})}

class EventCommentForm(forms.ModelForm):
    class Meta:
        model = EventComment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tulis komentar dengan sopan'})}
