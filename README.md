# Presensi Face Recognition Flask

Web presensi berbasis Flask untuk 3 role: peserta, pengajar, dan admin. Database menggunakan MySQL dari Laragon.

## Struktur Folder

```text
website-presensi/
  app.py
  presensi/
    __init__.py
    factory.py
    config.py
    extensions.py
    helpers.py
    models.py
    routes/
      main.py
      auth.py
      participant.py
      teacher.py
      admin.py
    services/
      face_utils.py
  static/
  templates/
```

## Fitur

- Landing page dengan pilihan peserta dan pengajar.
- Login, daftar akun, dan lupa password untuk peserta, pengajar, dan admin.
- Peserta dapat mendaftarkan wajah, melakukan presensi wajah, dan melihat riwayat presensi.
- Pengajar dapat membuat, mengubah, membuka/menutup, menghapus sesi, melihat peserta hadir, dan melihat rekap.
- Admin dapat melihat ringkasan sistem, mengelola pengguna, mengelola sesi, dan melihat seluruh rekap presensi.
- Face recognition lokal memakai webcam browser dan OpenCV di backend Flask.

## Persiapan

Pastikan sudah terpasang:

- Python 3.10 atau 3.11
- Laragon dengan MySQL aktif
- Browser modern seperti Chrome atau Edge

## Cara Install

1. Buka Laragon, lalu start MySQL.

2. Buat database:

   Buka Laragon Terminal atau phpMyAdmin, lalu jalankan isi file `database.sql`.

   ```sql
   CREATE DATABASE IF NOT EXISTS presensi_face
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

3. Buka terminal di folder proyek:

   ```powershell
   cd "C:\Users\Iqbal Mahendra\Desktop\website-presensi"
   ```

4. Buat virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\activate
   ```

   Jika perintah `py` tidak ada, pakai:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

5. Install dependency:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Buat file konfigurasi:

   ```powershell
   copy .env.example .env
   ```

   Jika password MySQL Laragon masih kosong, biarkan:

   ```env
   DB_USER=root
   DB_PASSWORD=
   ```

7. Buat tabel dan admin awal:

   ```powershell
   python -m flask --app app init-db
   ```

8. Jalankan web:

   ```powershell
   python -m flask --app app run --debug
   ```

9. Buka browser:

   ```text
   http://127.0.0.1:5000
   ```

## Akun Admin Awal

Saat menjalankan `init-db`, aplikasi membuat admin:

```text
Email    : admin@presensi.local
Password : admin123
```

Data ini bisa diganti di `.env`:

```env
SEED_ADMIN_EMAIL=admin@presensi.local
SEED_ADMIN_PASSWORD=admin123
ADMIN_INVITE_CODE=admin123
```

## Cara Menggunakan

### Peserta

1. Dari landing page pilih `Masuk Peserta`.
2. Pilih `Daftar akun` jika belum punya akun.
3. Login sebagai peserta.
4. Buka menu `Kelola wajah`, aktifkan kamera, lalu ambil 5 sampel wajah.
5. Buka menu `Presensi`, pilih sesi yang dibuka pengajar, aktifkan kamera, lalu klik `Presensi`.
6. Buka menu `Riwayat` untuk melihat catatan presensi.

### Pengajar

1. Dari landing page pilih `Masuk Pengajar`.
2. Daftar atau login sebagai pengajar.
3. Buka menu `Sesi`, lalu klik `Buat sesi`.
4. Isi nama sesi, kelas, lokasi, jadwal, dan centang `Sesi dibuka`.
5. Peserta baru bisa presensi jika sesi sedang dibuka dan masih berada dalam jadwal.
6. Buka detail sesi untuk melihat siapa saja peserta yang sudah presensi.
7. Gunakan menu `Rekap` untuk melihat ringkasan sesi sebelumnya.

### Admin

1. Login melalui `Akses admin`.
2. Gunakan `Pengguna` untuk melihat peserta, pengajar, dan admin.
3. Gunakan `Sesi` untuk membuka/menutup atau menghapus sesi.
4. Gunakan `Rekap` untuk melihat semua presensi.

## Catatan Face Recognition

- Kamera browser berjalan normal di `localhost` atau `127.0.0.1`.
- Pastikan wajah menghadap kamera dan pencahayaan cukup saat daftar wajah maupun presensi.
- Ambang kecocokan dapat diubah lewat `.env`:

  ```env
  LBPH_DISTANCE_THRESHOLD=75.0
  ```

- Untuk sistem produksi, tambahkan validasi liveness, audit log, enkripsi data biometrik, dan kebijakan izin pengguna.

## Masalah Umum

Jika muncul error koneksi database:

- Pastikan MySQL Laragon sudah aktif.
- Pastikan database `presensi_face` sudah dibuat.
- Pastikan `DB_USER`, `DB_PASSWORD`, `DB_HOST`, dan `DB_PORT` di `.env` sesuai Laragon.

Jika kamera tidak muncul:

- Buka web lewat `http://127.0.0.1:5000`.
- Izinkan akses kamera saat browser meminta izin.
- Coba Chrome atau Edge.

Jika `opencv-python` gagal terinstall:

- Gunakan Python 3.10 atau 3.11.
- Jalankan ulang:

  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  ```

## Catatan Struktur Baru

- `app.py` sekarang hanya menjadi pintu masuk aplikasi.
- Seluruh konfigurasi, model, helper, layanan face recognition, dan route sudah dipisah ke folder `presensi/`.
- Kalau nanti fitur bertambah, tempat paling enak untuk menaruhnya adalah di `presensi/routes/` atau `presensi/services/`.
