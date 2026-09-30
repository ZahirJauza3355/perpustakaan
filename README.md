# 📚 PerpustakaanKu — Sistem Perpustakaan Sederhana

CRUD sederhana untuk mengelola data buku, dibangun dengan **Flask** + **SQLite**, tampilan modern & clean, plus fitur unggulan: **download seluruh source code langsung dari web**.

## ✨ Fitur

**Buku**
- ➕ Tambah buku (judul, penulis, tahun terbit, kategori, stok) — kategori dipilih lewat dropdown dari tabel kategori
- ✏️ Edit buku
- 🗑️ Hapus buku (dengan konfirmasi)
- 📄 Lihat daftar buku + pencarian (judul/penulis/kategori) + filter berdasarkan kategori
- 📊 Statistik ringkas (total judul, total stok, jumlah kategori)

**Kategori** (CRUD terpisah, halaman `/categories`)
- ➕ Tambah kategori baru
- ✏️ Edit nama kategori (otomatis ter-update di semua buku terkait)
- 🗑️ Hapus kategori (buku yang terkait otomatis jadi "Tanpa kategori", tidak ikut terhapus)
- 📄 Lihat daftar kategori beserta jumlah buku per kategori
- 🔗 Nama kategori unik (tidak boleh duplikat, tidak case-sensitive)

**Lainnya**
- ⬇️ **Download source code**: tombol di navbar yang men-generate file `.zip` berisi seluruh kode project secara on-the-fly
- 🔄 **Migrasi otomatis**: kalau kamu sebelumnya pakai versi lama (kategori sebagai teks bebas), saat pertama kali dijalankan datanya otomatis dipindahkan ke tabel kategori baru — tidak ada data yang hilang

## 🗂️ Struktur Project

```
perpustakaan-crud/
├── app.py                 # Route Flask (semua logic CRUD + download source)
├── database.py             # Koneksi & inisialisasi SQLite
├── requirements.txt
├── vercel.json              # Konfigurasi deploy ke Vercel
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html          # Daftar buku
│   ├── add.html            # Form tambah buku
│   ├── edit.html           # Form edit buku
│   └── categories/
│       ├── index.html      # Daftar kategori
│       ├── add.html        # Form tambah kategori
│       └── edit.html       # Form edit kategori
└── static/
    └── css/
        └── style.css
```

## 🗄️ Skema Database

```
categories
├── id            INTEGER PK
├── nama          TEXT UNIQUE
└── created_at    TIMESTAMP

books
├── id              INTEGER PK
├── judul           TEXT
├── penulis         TEXT
├── tahun_terbit    INTEGER
├── kategori_id     INTEGER  -> FK ke categories(id), ON DELETE SET NULL
├── stok            INTEGER
└── created_at      TIMESTAMP
```

Kalau sebuah kategori dihapus, buku yang tadinya memakai kategori itu **tidak ikut terhapus** — hanya `kategori_id`-nya kembali menjadi `NULL` (ditampilkan sebagai "Tanpa kategori").

## 🚀 Menjalankan Secara Lokal

1. Buat virtual environment (opsional tapi disarankan):
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Jalankan aplikasi:
   ```bash
   python app.py
   ```

4. Buka browser ke `http://127.0.0.1:5000`

Database `library.db` akan otomatis dibuat (beserta 3 data contoh) saat pertama kali dijalankan.

## ☁️ Deploy ke Vercel

1. Push project ini ke repository GitHub/GitLab/Bitbucket.
2. Buka [vercel.com](https://vercel.com) → **New Project** → import repository tersebut.
3. Vercel akan otomatis mendeteksi `vercel.json` dan men-deploy `app.py` sebagai serverless function Python.
4. Klik **Deploy**.

Atau lewat Vercel CLI:
```bash
npm i -g vercel
vercel
```

### ⚠️ Catatan Penting soal SQLite di Vercel

Vercel menjalankan aplikasi sebagai **serverless function** dengan filesystem *read-only*, kecuali folder `/tmp` yang bersifat **sementara** (isinya bisa hilang kapan saja saat instance di-restart/scale/redeploy).

Project ini sudah diatur agar otomatis memakai `/tmp/library.db` saat berjalan di Vercel (lihat `database.py`), sehingga aplikasi **tetap bisa jalan** untuk demo/testing. Tapi konsekuensinya:

- Data yang ditambahkan **tidak permanen** — bisa hilang sewaktu-waktu.
- Ini cocok untuk **demo/prototype**, bukan untuk data buku sungguhan yang harus tersimpan lama.

Kalau nanti butuh data yang benar-benar persisten di Vercel, pertimbangkan pindah ke database eksternal seperti **Vercel Postgres**, **Turso (SQLite via edge)**, **Supabase**, atau **PlanetScale** — strukturnya (tabel `books`) bisa dipakai ulang, tinggal ganti bagian koneksi di `database.py`.

## 🎨 Desain

- Font: [Inter](https://fonts.google.com/specimen/Inter) via Google Fonts
- Palet warna: indigo sebagai aksen utama, slate untuk teks & border, dengan banyak whitespace agar terasa lega
- Komponen: stat cards, tabel dengan hover state, badge kategori, empty state, form card dengan validasi sederhana

## 🔒 Sebelum ke Production

- Ganti `secret_key` di `app.py` (gunakan environment variable `SECRET_KEY`)
- Tambahkan validasi input lebih ketat jika perlu
- Pertimbangkan migrasi ke database eksternal (lihat catatan di atas)
