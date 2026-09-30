import sqlite3
import os


def get_db_path():
    """
    Menentukan lokasi file database.
    Di Vercel, filesystem bersifat read-only kecuali folder /tmp,
    dan /tmp bersifat sementara (bisa hilang tiap deployment/instance baru).
    Untuk pemakaian lokal, database disimpan langsung di folder project.
    """
    if os.environ.get("VERCEL"):
        return "/tmp/library.db"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(conn, table, column):
    cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def _migrate_old_kategori_column(conn):
    """
    Menangani database lama (versi sebelum ada tabel categories) yang masih
    menyimpan kategori sebagai teks bebas di kolom books.kategori.
    Kategori teks tersebut dipindahkan menjadi baris di tabel categories,
    lalu books.kategori_id diisi sesuai relasinya.
    """
    if not _column_exists(conn, "books", "kategori"):
        return  # database baru, tidak perlu migrasi

    if _column_exists(conn, "books", "kategori_id"):
        return  # sudah pernah dimigrasi sebelumnya

    conn.execute("ALTER TABLE books ADD COLUMN kategori_id INTEGER REFERENCES categories(id)")

    existing = conn.execute(
        "SELECT DISTINCT kategori FROM books WHERE kategori IS NOT NULL AND TRIM(kategori) != ''"
    ).fetchall()

    for row in existing:
        nama = row["kategori"].strip()
        conn.execute("INSERT OR IGNORE INTO categories (nama) VALUES (?)", (nama,))

    conn.execute(
        """
        UPDATE books
        SET kategori_id = (
            SELECT id FROM categories WHERE nama = books.kategori COLLATE NOCASE
        )
        WHERE kategori IS NOT NULL AND TRIM(kategori) != ''
        """
    )
    conn.commit()

    # Kolom teks lama sudah tidak dipakai lagi. SQLite modern (3.35+) mendukung
    # DROP COLUMN; kalau versi lebih lama, cukup dibiarkan menganggur (aman).
    try:
        conn.execute("ALTER TABLE books DROP COLUMN kategori")
        conn.commit()
    except sqlite3.OperationalError:
        pass


def init_db():
    conn = get_db_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            penulis TEXT NOT NULL,
            tahun_terbit INTEGER,
            kategori_id INTEGER,
            stok INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kategori_id) REFERENCES categories(id) ON DELETE SET NULL
        )
        """
    )
    conn.commit()

    _migrate_old_kategori_column(conn)

    # Isi data contoh kalau tabel masih kosong, biar tampilan tidak kosong melompong
    total_kategori = conn.execute("SELECT COUNT(*) AS total FROM categories").fetchone()["total"]
    if total_kategori == 0:
        conn.executemany(
            "INSERT INTO categories (nama) VALUES (?)",
            [("Fiksi",), ("Pengembangan Diri",), ("Sejarah",)],
        )
        conn.commit()

    total_buku = conn.execute("SELECT COUNT(*) AS total FROM books").fetchone()["total"]
    if total_buku == 0:
        fiksi_id = conn.execute("SELECT id FROM categories WHERE nama = 'Fiksi'").fetchone()["id"]
        pengembangan_id = conn.execute(
            "SELECT id FROM categories WHERE nama = 'Pengembangan Diri'"
        ).fetchone()["id"]

        sample = [
            ("Laskar Pelangi", "Andrea Hirata", 2005, fiksi_id, 4),
            ("Bumi Manusia", "Pramoedya Ananta Toer", 1980, fiksi_id, 2),
            ("Filosofi Teras", "Henry Manampiring", 2018, pengembangan_id, 6),
        ]
        conn.executemany(
            "INSERT INTO books (judul, penulis, tahun_terbit, kategori_id, stok) VALUES (?, ?, ?, ?, ?)",
            sample,
        )
        conn.commit()

    conn.close()
