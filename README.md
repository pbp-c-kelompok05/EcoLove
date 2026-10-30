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
    Transaction+Payment = Maurilla Maharani Nur Abdul (2506588374)


## Modul Event + Education

PIC: **David Mesakh (2506604503)**. App: `events`.

- Halaman: `/events/` dan `/events/education/`, dilengkapi pencarian/filter AJAX dan pagination.
- Superuser mengelola event/artikel melalui `/events/manage/` dan `/events/education/manage/`; pengguna login dapat berkomentar pada event dan menghapus komentar sendiri. Superuser dapat memoderasi semua komentar. Artikel hanya dibaca.
- Pengguna login dapat mendaftar event satu kali per akun, melihat status terdaftar, dan membatalkan keikutsertaan. Pendaftaran baru ditutup saat event dimulai; aturan ini diperiksa di server dan dilindungi unique constraint database.
- Komentar event mendukung satu foto opsional dengan preview 1:1. Upload JPG/PNG/WebP maksimal 5 MB dan 20 megapiksel dipotong dari tengah menjadi persegi, mengikuti orientasi foto, lalu disimpan sebagai JPEG maksimal 1024 × 1024. Teks komentar tetap wajib; komentar tanpa foto tetap didukung.
- Tampilan mengikuti PNG EcoLove baru: banner SVG, kartu, detail dua kolom, artikel, form, tabel pengelolaan, dan konfirmasi hapus. CSS dibatasi ke modul ini; login dan Marketplace tetap memakai tampilan bersama yang sudah ada.
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

Hasil implementasi PNG dan foto komentar: check dan konsistensi migrasi lulus; 50 test lulus, mencakup CRUD, akses, komentar, validasi, filter, CSRF, XSS, privasi HTML/JSON, pendaftaran, pembatalan, pengelolaan, serta crop/validasi upload foto komentar. Browser dengan database preview terisolasi: pencarian/filter, akses guest/user/admin, pendaftaran, create/update Events dan Education, serta halaman konfirmasi hapus diperiksa. Screenshot desktop, tablet, dan mobile juga diperiksa. Detail perubahan, batasan visual, dan langkah integrasi tersedia di [laporan implementasi](docs/events-education.md).

Uji sebagai guest untuk informasi publik, user untuk komentar, dan superuser untuk CRUD/moderasi. Login saat ini mengarah ke Marketplace; buka Events melalui navbar setelah login.

### Catatan integrasi

- Kategori awal: Reuse & Repair, Minim Sampah, Komunitas, Gaya Hidup. Kontak/link boleh kosong; hindari menulis informasi privat di deskripsi publik.
- Koordinasikan kategori final, migrasi deployment, dan pembagian requirement 50 data lintas modul.
- Konfigurasi storage lama dipertahankan: tanpa MEDIA_ROOT eksplisit, upload berada di `item_images/`, `event_images/`, dan `education_images/` relatif direktori kerja. Route development dibatasi ke folder tersebut. Tidak ada gambar dipindahkan/dihapus; file lama dari percobaan konfigurasi `media/` perlu dikoordinasikan jika ada. Hosting perlu mengatur persistensi dan penyajian media.
- Migrasi `events.0003_eventregistration` hanya menambah tabel pendaftaran dan unique constraint. Migrasi sudah diterapkan pada SQLite lokal setelah backup di folder sementara; data lama tidak dihapus atau di-seed. Database deployment tidak disentuh. Jalankan `python manage.py migrate` saat menyiapkan database lain. Warning WhiteNoise tentang `staticfiles/` ditangani melalui `collectstatic` saat integrasi hosting.
- Migrasi `events.0004_eventcomment_image` menambah foto opsional pada komentar lama tanpa menghapus isinya. File disimpan di `event_images/comments/`, mengikuti storage/media proyek. Migrasi lokal sudah diterapkan setelah backup; database deployment tidak disentuh.

## Modul Payments + Transactions

PIC: **Maurilla Maharani Nur Abdul (2506588374)**. App: `payments`.

- **Checkout dan integrasi Midtrans Snap Sandbox.** Pengguna yang login dapat memulai pembelian item Marketplace melalui halaman checkout. Sistem membuat order dengan UUID sebagai ID unik yang dikirim ke Midtrans sebagai `order_id`, kemudian meminta Snap token untuk membuka proses pembayaran. Jika order masih berstatus `PENDING` dan sudah memiliki Snap token, sistem menggunakan kembali token tersebut agar pengguna dapat melanjutkan pembayaran yang belum selesai.

- **Pengelolaan status transaksi.** Model `Order` menyimpan item yang dibeli, pembeli, nominal pembayaran, status transaksi, Snap token, waktu pembuatan, alamat pengiriman, dan catatan untuk penjual. Status yang didukung adalah `PENDING`, `PAID`, `FAILED`, `EXPIRED`, dan `CANCELLED`. Status diperbarui berdasarkan notifikasi Midtrans atau melalui sinkronisasi status langsung ke Midtrans.

- **Notifikasi pembayaran dan verifikasi signature.** Endpoint `/payments/midtrans/notification/` menerima notifikasi transaksi dari Midtrans. Sistem memverifikasi `signature_key` menggunakan SHA-512 dan perbandingan signature yang aman sebelum memperbarui status order. Status pembayaran berhasil ditetapkan untuk transaksi `settlement` atau `capture` dengan `fraud_status` bernilai `accept`. Status yang sudah `PAID` atau `CANCELLED` tidak diubah oleh fungsi pembaruan status.

- **Pembatalan pembayaran.** Pembeli dapat membatalkan order miliknya melalui endpoint pembatalan. Sistem terlebih dahulu meminta status terbaru dari Midtrans. Order yang sudah dibayar tidak dapat dibatalkan melalui alur ini. Untuk order yang masih menunggu pembayaran, sistem meminta pembatalan ke Midtrans dan menghapus order lokal jika pembatalan berhasil atau transaksi belum memiliki pembayaran yang dapat dibatalkan. Order yang sudah berstatus gagal atau kedaluwarsa juga dapat dibersihkan dari database lokal.

- **My Purchases.** Pengguna yang login dapat melihat daftar pembelian berstatus `PAID` melalui `/payments/my-purchases/`. Daftar menampilkan informasi item jika masih tersedia, nominal pembayaran, tanggal pembuatan order, dan status transaksi. Jika item sudah dihapus, riwayat tetap dapat menampilkan order dengan keterangan bahwa item tidak lagi tersedia.

- **Validasi pembelian dan akses.** Endpoint pembuatan pembayaran hanya menerima metode POST dan mengharuskan pengguna login. Pengguna tidak dapat membeli item miliknya sendiri. Halaman checkout mengarahkan pengguna kembali ke detail item jika item tersebut dimiliki pengguna atau sudah terjual. Endpoint sinkronisasi status dan pembatalan membatasi akses ke order milik pembeli yang sedang login.

- **Alamat pengiriman dan catatan penjual.** `OrderForm` menyediakan kolom alamat pengiriman dan catatan opsional untuk penjual. Alamat menggunakan textarea dan catatan menggunakan input teks. Form ini tersedia untuk kebutuhan checkout; penyimpanan nilai form ke order perlu dipastikan melalui implementasi JavaScript atau view checkout yang digunakan. Namun form ini masih belum di-develop lebih lanjut.

- **Integrasi dengan Marketplace.** Aplikasi `payments` menggunakan model `Item` dari app `items`. Order berstatus `PAID` digunakan oleh Marketplace untuk mengecualikan item terjual dari hasil pencarian JSON dan menandai item sebagai terjual di marketplace pribadi. Detail item juga menampilkan tombol untuk memulai atau melanjutkan pembayaran, serta tombol pembatalan ketika pembeli memiliki order `PENDING`.

### Menjalankan lokal

Pastikan virtual environment aktif, `.env` menggunakan konfigurasi development lokal, dan database yang digunakan memang database lokal. Konfigurasi Midtrans harus memakai kredensial **Sandbox**, bukan Production. Jangan commit server key atau secret ke Git.

source .env/bin/activate

python3 manage.py migrate
python3 manage.py runserver

Untuk Windows PowerShell, perintah aktivasi virtual environment dapat berbeda sesuai nama dan lokasi environment yang digunakan.

Pastikan konfigurasi Midtrans di `EcoLove/settings.py` atau sumber environment yang digunakan menyediakan nilai yang sesuai untuk:

- `MIDTRANS_SERVER_KEY`
- `MIDTRANS_CLIENT_KEY`
- `MIDTRANS_SNAP_URL`
- `MIDTRANS_STATUS_URL`
- `MIDTRANS_CANCEL_URL`
- `MIDTRANS_SNAP_JS`

Alamat endpoint harus mengarah ke lingkungan Sandbox yang sesuai. Untuk pengujian notifikasi di localhost, gunakan mekanisme tunnel atau sinkronisasi status langsung yang sudah tersedia.

### Pengujian

Pengujian pada modul Payments + Transactions dilakukan menggunakan Django Test Framework untuk memeriksa fungsionalitas pembayaran, pengelolaan transaksi, dan kontrol akses pengguna. Pengujian integrasi dengan Midtrans menggunakan mock response agar dapat dijalankan tanpa membuat transaksi pembayaran sungguhan.

**Cakupan pengujian:**
1. **Pembuatan pembayaran:** Memastikan endpoint pembayaran hanya menerima request POST, order dibuat dengan status awal `PENDING`, dan Snap token dikembalikan ketika Midtrans merespons dengan sukses.
2. **Pencegahan pembayaran duplikat:** Memastikan pembayaran pending yang masih memiliki Snap token dapat digunakan kembali.
3. **Validasi pembeli:** Memastikan pengguna tidak dapat membeli barang miliknya sendiri.
4. **Penanganan kegagalan pembayaran:** Memastikan kegagalan respons Midtrans ditangani dan status order diperbarui menjadi `FAILED`.
5. **Notifikasi Midtrans:** Memastikan notifikasi dengan signature yang valid dapat memperbarui status order, sedangkan signature yang tidak valid ditolak.
6. **Pemetaan status transaksi:** Memeriksa pembaruan status berdasarkan respons Midtrans, termasuk `PAID`, `CANCELLED`, `FAILED`, `EXPIRED`, dan `PENDING`.
7. **Riwayat pembelian:** Memastikan halaman My Purchases hanya menampilkan transaksi berstatus `PAID` milik pengguna yang sedang login.
8. **Kontrol akses transaksi:** Memastikan pengguna tidak dapat memeriksa status pembayaran milik pengguna lain.

**Cara menjalankan pengujian:**

Aktifkan virtual environment dan jalankan perintah berikut dari direktori proyek Django:

python3 manage.py test payments

Django akan menjalankan test case pada aplikasi `payments` menggunakan test database sementara.

Pengecekan tambahan dapat dilakukan menggunakan perintah:

python3 manage.py check
python3 manage.py makemigrations --check
python3 manage.py migrate --plan

Perintah tersebut digunakan untuk memeriksa konfigurasi proyek, perubahan model yang belum memiliki migration, dan rencana migration yang akan dijalankan. Ketiganya bukan pengganti automated tests.

**Catatan:** Pengujian otomatis memeriksa logika pembayaran menggunakan mock response. Pengujian ini tidak membuktikan bahwa seluruh alur pembayaran berhasil pada Midtrans Sandbox atau bahwa notifikasi eksternal dapat diterima saat aplikasi berjalan secara lokal. Hasil pengujian harus diverifikasi dengan menjalankan test suite dan, untuk integrasi end-to-end, melakukan pengujian tambahan menggunakan Midtrans Sandbox.

### Catatan integrasi

- Pembayaran menggunakan Midtrans Snap. Order lokal dibuat sebelum permintaan token dikirim ke Midtrans. Jika permintaan token gagal, order ditandai `FAILED`.
- ID order menggunakan UUID dan dikirim ke Midtrans sebagai `order_id`. Nominal pembayaran berasal dari harga item saat order dibuat.
- Endpoint notifikasi menggunakan `csrf_exempt` agar dapat menerima callback dari Midtrans. Karena itu, validasi signature menjadi bagian penting dari pemeriksaan keaslian notifikasi.
- Endpoint sinkronisasi status langsung ke Midtrans disediakan sebagai fallback, khususnya ketika webhook tidak dapat menjangkau server lokal.
- Model `Order` menggunakan `on_delete=models.SET_NULL` untuk relasi item dan `on_delete=models.CASCADE` untuk pembeli. Penghapusan item tidak otomatis menghapus order, sedangkan penghapusan akun pembeli dapat menghapus order terkait.
- Saat ini, daftar My Purchases hanya menampilkan order berstatus `PAID`. Order `PENDING`, `FAILED`, `EXPIRED`, atau `CANCELLED` tidak muncul di daftar tersebut.
- Harga dan informasi item dikirim ke Midtrans dari data item saat checkout. Perubahan harga, pencegahan pembelian bersamaan, dan penguncian item ketika pembayaran berlangsung perlu ditinjau untuk menghindari transaksi dengan nominal atau status item yang tidak konsisten.
- Konfigurasi hosting, penyimpanan kredensial, URL notifikasi publik, dan pengujian terhadap database production perlu dilakukan sebelum deployment. Jangan menganggap hasil pengujian lokal sebagai bukti bahwa seluruh konfigurasi hosting telah teruji.

