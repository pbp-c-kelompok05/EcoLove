from zoneinfo import ZoneInfo
from django import forms
from django.utils import timezone
from .models import Event, Education, EventComment
from .comment_images import square_comment_image

WIB = ZoneInfo('Asia/Jakarta')

class AccessibleForm(forms.ModelForm):
    """Keep server-rendered and AJAX validation tied to the same field hints."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field_id = self[name].auto_id
            if field_id:
                described_by = [f'{field_id}_errors']
                if field.help_text:
                    described_by.insert(0, f'{field_id}_helptext')
                field.widget.attrs['aria-describedby'] = ' '.join(described_by)
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput, forms.Select)):
                field.widget.attrs.setdefault('placeholder', field.label)
            if self.is_bound and name in self.errors:
                field.widget.attrs['aria-invalid'] = 'true'

class WIBDateTimeField(forms.DateTimeField):
    def prepare_value(self, value):
        with timezone.override(WIB):
            return super().prepare_value(value)

    def to_python(self, value):
        with timezone.override(WIB):
            return super().to_python(value)

class EventForm(AccessibleForm):
    starts_at = WIBDateTimeField(label='Mulai (WIB, UTC+7)', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))
    ends_at = WIBDateTimeField(label='Selesai (WIB, UTC+7)', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))

    class Meta:
        model = Event
        fields = ['title', 'category', 'location', 'starts_at', 'ends_at', 'description', 'is_online', 'organizer_contact', 'meeting_link', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 6})}
        help_texts = {'description': 'Informasi publik: jangan tulis kontak atau link pertemuan di sini.', 'location': 'Nama tempat/kota atau platform; simpan link privat di kolom link pertemuan.'}

class EducationForm(AccessibleForm):
    class Meta:
        model = Education
        fields = ['title', 'summary', 'body', 'category', 'image']
        widgets = {'summary': forms.Textarea(attrs={'rows': 3}), 'body': forms.Textarea(attrs={'rows': 12})}
        help_texts = {'body': 'Pisahkan paragraf dengan baris kosong. Gunakan ## untuk judul bagian, - untuk daftar, atau 1. untuk langkah berurutan. HTML ditampilkan sebagai teks.'}

class CommentImageField(forms.ImageField):
    def to_python(self, value):
        if value is None or value is False:
            return super().to_python(value)
        return super().to_python(square_comment_image(value))


class EventCommentForm(AccessibleForm):
    image = CommentImageField(
        label='Foto (opsional)', required=False,
        help_text='JPG, PNG, atau WebP, maksimal 5 MB dan 20 megapiksel. Foto otomatis dipotong dari tengah menjadi persegi 1:1.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = EventComment
        fields = ['body', 'image']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tulis komentar dengan sopan'})}


class EventCommentAdminForm(EventCommentForm):
    class Meta(EventCommentForm.Meta):
        fields = '__all__'
