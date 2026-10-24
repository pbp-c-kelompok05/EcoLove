Nama Anggota & NPM:
   - Maurilla Maharani Nur Abdul (2506588374)
   - David Mesakh (2506604503)
   - Qanita Syafika (2506551996)
   - Karen Lim (2506623982)
   - Sayyid Aqil Kusuma (2506596331)


Nama aplikasi:
   EcoLove


Deskripsi Aplikasi:
    EcoLove adalah aplikasi marketplace berbasis web yang mempertemukan masyarakat untuk menjual, membeli, dan menemukan barang maupun kegiatan yang mendukung gaya hidup berkelanjutan.

    Melalui EcoLove, pengguna dapat memberikan kesempatan kedua kepada barang-barang yang masih layak digunakan, seperti pakaian preloved, perabot, buku, alat elektronik, wadah pakai ulang, produk upcycle, serta berbagai barang ramah lingkungan lainnya. Konsep tersebut direpresentasikan melalui tagline “Love Me Again”, yaitu mengajak pengguna untuk kembali menghargai dan memperpanjang masa pakai suatu barang.

    Berbeda dari marketplace umum, EcoLove berfokus pada barang dan aktivitas yang memiliki nilai keberlanjutan. Setiap barang dapat dilengkapi dengan kategori dan sustainability tags, seperti preloved, reusable, recycled, upcycled, refillable, repairable, locally made, dan low-waste.

    Selain marketplace, EcoLove menyediakan informasi kegiatan bertema lingkungan, seperti acara pertukaran barang, workshop perbaikan, bazar barang bekas, kegiatan bersih-bersih, dan webinar. Pengguna juga dapat membaca serta membagikan konten edukasi mengenai konsumsi sadar, perawatan barang, daur ulang, dan gaya hidup minim sampah.

    EcoLove mengusung konsep “From the people, by the people, for the people” karena konten dan aktivitas di dalam aplikasi berasal dari kontribusi masyarakat. Pengguna dapat menjadi pembeli, penjual, penyelenggara kegiatan, pemberi ulasan, maupun kontributor konten edukasi dalam satu akun yang sama.
   
Sumber Public API:
   https://github.com/emsifa/api-wilayah-indonesia.git


User Role & Target User:
   
    User Role: 
        Guest / Anonymous : Hanya bisa melihat katalog produk berdasarkan lokasi, membaca artikel edukasi, dan melihat jadwal acara.
        Buyer (User) : Dapat mengelola profil, membeli barang bekas menggunakan pembayaran Midtrans, dan memberikan ulasan pesanan. 
        Seller (User) : Dapat mengunggah foto produk bekas, menetapkan harga, menentukan lokasi penjemputan, dan mengatur status barang. 
        Event + Education : Hanya superuser yang boleh membuat, mengedit, dan menghapus event/artikel. Pengguna login boleh berkomentar pada event; artikel hanya dibaca.
        Admin : Memegang kendali penuh untuk memoderasi produk, memantau transaksi Midtrans, mengelola akun, dan memvalidasi konten. 
    Target User:
        Gen Z & Thrifter : Anak muda berusia 18–35 tahun yang mencari barang bekas berkualitas 
        Penjual :  Individu yang ingin menjual barang layak pakai di rumahnya secara mudah dan aman. 



Perbandingan: 
    
    Compared to existing secondhand marketplaces, EcoLove combines marketplace functionality with features that support sustainable living.

    OLX provides **User & Profile, Item, Transaction & Payment, and Reviews**, but does not include **Events** or **Education** features.

    Facebook Marketplace provides **User & Profile, Item, Transaction & Payment, Reviews, and Events**, but does not specifically provide an **Education** feature.

    EcoLove includes all of these features: **User & Profile, Item, Transaction & Payment, Reviews, Events, and Education**. The combination is designed to support not only secondhand transactions, but also community engagement and awareness of sustainable living.


Daftar Modul & PIC:
    Auth-Profile-User = 
    Event+Education = David Mesakh (2506604503)
    Item = 
    Review = 
    Transaction+Payment =


## Modul Event + Education

PIC: **David Mesakh (2506604503)**. App: `events`.

- Halaman: `/events/` dan `/events/education/`, dilengkapi pencarian/filter AJAX dan pagination.
- Superuser mengelola event/artikel; pengguna login dapat berkomentar pada event dan menghapus komentar sendiri. Superuser dapat memoderasi semua komentar. Artikel hanya dibaca.
- Guest dapat membaca informasi umum. Kontak, link pertemuan, dan komentar event hanya tersedia setelah login, termasuk pada JSON.
- Mendukung gambar opsional, validasi tanggal, waktu WIB, CSRF, escaping XSS, dan tampilan responsif Pure CSS 3.0.0 (grid lokal beserta lisensi BSD).

### Menjalankan lokal

Pastikan `.env` memakai `PRODUCTION=False` dan database lokal sendiri.

```powershell
.\env\Scripts\Activate.ps1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Seed opsional dan idempotent (3 event + 3 artikel sintetis), hanya untuk database lokal:

```powershell
python manage.py seed_events --username NAMA_SUPERUSER_LOKAL
```

### Pengujian

Gunakan database test terisolasi. `test_settings` memaksa SQLite in-memory, hasher MD5 khusus test, dan media uji; auth/middleware/form/migration tetap sama. Test runner menonaktifkan DEBUG, sehingga route development juga diuji dengan DEBUG aktif. PostgreSQL dan konfigurasi hosting belum diuji:

```powershell
python manage.py check --settings=EcoLove.test_settings
python manage.py makemigrations --check --dry-run --settings=EcoLove.test_settings
python manage.py test --settings=EcoLove.test_settings
```

Hasil: check dan konsistensi migrasi lulus; 24 test lulus, mencakup CRUD, akses, komentar, validasi, filter, CSRF, XSS, dan privasi HTML/JSON. Browser: akses guest/user, komentar, serta create/update event sudah dicoba. DOM desktop/mobile diperiksa, tetapi screenshot dan kelanjutan alur dialog hapus timeout; review visual lengkap dan CRUD Education lewat UI masih diperlukan.

Uji sebagai guest untuk informasi publik, user untuk komentar, dan superuser untuk CRUD/moderasi. Login saat ini mengarah ke Marketplace; buka Events melalui navbar setelah login.

### Catatan integrasi

- Kategori awal: Reuse & Repair, Minim Sampah, Komunitas, Gaya Hidup. Kontak/link boleh kosong; hindari menulis informasi privat di deskripsi publik.
- Koordinasikan kategori final, migrasi deployment, dan pembagian requirement 50 data lintas modul.
- Konfigurasi storage lama dipertahankan: tanpa MEDIA_ROOT eksplisit, upload berada di `item_images/`, `event_images/`, dan `education_images/` relatif direktori kerja. Route development dibatasi ke folder tersebut. Tidak ada gambar dipindahkan/dihapus; file lama dari percobaan konfigurasi `media/` perlu dikoordinasikan jika ada. Hosting perlu mengatur persistensi dan penyajian media.
- Database lokal/deployment belum dimigrasikan atau di-seed selama implementasi. Warning WhiteNoise tentang `staticfiles/` ditangani melalui `collectstatic` saat integrasi hosting.
