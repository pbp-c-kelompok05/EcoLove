from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from events.models import Event, Education

class Command(BaseCommand):
    help = 'Contoh sintetis lokal yang idempotent (3 event + 3 artikel). Tidak membuat akun.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Superuser lokal yang sudah dibuat')

    @transaction.atomic
    def handle(self, *args, **options):
        author = get_user_model().objects.filter(username=options['username'], is_superuser=True).first()
        if not author:
            raise CommandError('Username harus milik superuser yang sudah ada.')
        for number, topic in enumerate(['Repair pakaian', 'Kompos rumahan', 'Komunitas isi ulang'], 1):
            start = timezone.now() + timedelta(days=number)
            Event.objects.get_or_create(title=f'[DEMO] {topic}', creator=author, defaults={
                'description': 'Data sintetis untuk latihan EcoLove, bukan kegiatan sungguhan.',
                'category': 'community', 'starts_at': start, 'ends_at': start + timedelta(hours=2),
                'location': 'Ruang komunitas contoh', 'organizer_contact': 'Panitia demo (sintetis)',
            })
            Education.objects.get_or_create(title=f'[DEMO] Panduan {topic.lower()}', author=author, defaults={
                'summary': 'Materi sintetis untuk latihan sustainable living.', 'category': 'lifestyle',
                'body': 'Mulai dengan barang yang sudah dimiliki. Rawat, gunakan kembali, dan bagikan kebiasaan baik bersama komunitas.',
            })
        self.stdout.write(self.style.SUCCESS('Contoh tersedia: 3 event + 3 artikel per superuser; pemanggilan ulang tidak menggandakan data.'))
