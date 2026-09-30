import os
import io
import zipfile
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, send_file

from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ganti-secret-key-ini-sebelum-production")

# Pastikan tabel & data awal siap setiap kali app di-start
init_db()


# ======================================================
# BUKU
# ======================================================

@app.route("/")
def index():
    conn = get_db_connection()
    search = request.args.get("search", "").strip()
    kategori_id = request.args.get("kategori_id", "").strip()

    query = """
        SELECT books.*, categories.nama AS kategori_nama
        FROM books
        LEFT JOIN categories ON categories.id = books.kategori_id
        WHERE 1=1
    """
    params = []

    if search:
        like = f"%{search}%"
        query += " AND (books.judul LIKE ? OR books.penulis LIKE ? OR categories.nama LIKE ?)"
        params += [like, like, like]

    if kategori_id:
        query += " AND books.kategori_id = ?"
        params.append(kategori_id)

    query += " ORDER BY books.id DESC"

    books = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY nama COLLATE NOCASE").fetchall()

    total_buku = conn.execute("SELECT COUNT(*) AS c FROM books").fetchone()["c"]
    total_stok = conn.execute("SELECT COALESCE(SUM(stok), 0) AS c FROM books").fetchone()["c"]
    total_kategori = conn.execute("SELECT COUNT(*) AS c FROM categories").fetchone()["c"]

    conn.close()
    return render_template(
        "index.html",
        books=books,
        categories=categories,
        search=search,
        selected_kategori_id=kategori_id,
        total_buku=total_buku,
        total_stok=total_stok,
        total_kategori=total_kategori,
    )


@app.route("/add", methods=["GET", "POST"])
def add_book():
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories ORDER BY nama COLLATE NOCASE").fetchall()

    if request.method == "POST":
        judul = request.form.get("judul", "").strip()
        penulis = request.form.get("penulis", "").strip()
        tahun_terbit = request.form.get("tahun_terbit") or None
        kategori_id = request.form.get("kategori_id") or None
        stok = request.form.get("stok") or 1

        if not judul or not penulis:
            flash("Judul dan penulis wajib diisi!", "error")
            conn.close()
            return render_template("add.html", form_data=request.form, categories=categories)

        conn.execute(
            "INSERT INTO books (judul, penulis, tahun_terbit, kategori_id, stok) VALUES (?, ?, ?, ?, ?)",
            (judul, penulis, tahun_terbit, kategori_id, stok),
        )
        conn.commit()
        conn.close()

        flash(f'Buku "{judul}" berhasil ditambahkan!', "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("add.html", form_data={}, categories=categories)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (id,)).fetchone()
    categories = conn.execute("SELECT * FROM categories ORDER BY nama COLLATE NOCASE").fetchall()

    if book is None:
        conn.close()
        flash("Buku tidak ditemukan!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        judul = request.form.get("judul", "").strip()
        penulis = request.form.get("penulis", "").strip()
        tahun_terbit = request.form.get("tahun_terbit") or None
        kategori_id = request.form.get("kategori_id") or None
        stok = request.form.get("stok") or 1

        if not judul or not penulis:
            flash("Judul dan penulis wajib diisi!", "error")
            conn.close()
            return render_template("edit.html", book=book, categories=categories)

        conn.execute(
            "UPDATE books SET judul=?, penulis=?, tahun_terbit=?, kategori_id=?, stok=? WHERE id=?",
            (judul, penulis, tahun_terbit, kategori_id, stok, id),
        )
        conn.commit()
        conn.close()

        flash(f'Buku "{judul}" berhasil diperbarui!', "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit.html", book=book, categories=categories)


@app.route("/delete/<int:id>", methods=["POST"])
def delete_book(id):
    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (id,)).fetchone()

    if book is None:
        conn.close()
        flash("Buku tidak ditemukan!", "error")
        return redirect(url_for("index"))

    conn.execute("DELETE FROM books WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash(f'Buku "{book["judul"]}" berhasil dihapus!', "success")
    return redirect(url_for("index"))


# ======================================================
# KATEGORI
# ======================================================

@app.route("/categories")
def categories_list():
    conn = get_db_connection()
    categories = conn.execute(
        """
        SELECT categories.*, COUNT(books.id) AS jumlah_buku
        FROM categories
        LEFT JOIN books ON books.kategori_id = categories.id
        GROUP BY categories.id
        ORDER BY categories.nama COLLATE NOCASE
        """
    ).fetchall()
    conn.close()
    return render_template("categories/index.html", categories=categories)


@app.route("/categories/add", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()

        if not nama:
            flash("Nama kategori wajib diisi!", "error")
            return render_template("categories/add.html", form_data=request.form)

        conn = get_db_connection()
        duplikat = conn.execute(
            "SELECT id FROM categories WHERE nama = ? COLLATE NOCASE", (nama,)
        ).fetchone()

        if duplikat:
            conn.close()
            flash(f'Kategori "{nama}" sudah ada!', "error")
            return render_template("categories/add.html", form_data=request.form)

        conn.execute("INSERT INTO categories (nama) VALUES (?)", (nama,))
        conn.commit()
        conn.close()

        flash(f'Kategori "{nama}" berhasil ditambahkan!', "success")
        return redirect(url_for("categories_list"))

    return render_template("categories/add.html", form_data={})


@app.route("/categories/edit/<int:id>", methods=["GET", "POST"])
def edit_category(id):
    conn = get_db_connection()
    category = conn.execute("SELECT * FROM categories WHERE id = ?", (id,)).fetchone()

    if category is None:
        conn.close()
        flash("Kategori tidak ditemukan!", "error")
        return redirect(url_for("categories_list"))

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()

        if not nama:
            flash("Nama kategori wajib diisi!", "error")
            conn.close()
            return render_template("categories/edit.html", category=category)

        duplikat = conn.execute(
            "SELECT id FROM categories WHERE nama = ? COLLATE NOCASE AND id != ?", (nama, id)
        ).fetchone()

        if duplikat:
            conn.close()
            flash(f'Kategori "{nama}" sudah ada!', "error")
            return render_template("categories/edit.html", category=category)

        conn.execute("UPDATE categories SET nama = ? WHERE id = ?", (nama, id))
        conn.commit()
        conn.close()

        flash("Kategori berhasil diperbarui!", "success")
        return redirect(url_for("categories_list"))

    conn.close()
    return render_template("categories/edit.html", category=category)


@app.route("/categories/delete/<int:id>", methods=["POST"])
def delete_category(id):
    conn = get_db_connection()
    category = conn.execute("SELECT * FROM categories WHERE id = ?", (id,)).fetchone()

    if category is None:
        conn.close()
        flash("Kategori tidak ditemukan!", "error")
        return redirect(url_for("categories_list"))

    jumlah_buku = conn.execute(
        "SELECT COUNT(*) AS c FROM books WHERE kategori_id = ?", (id,)
    ).fetchone()["c"]

    # books.kategori_id otomatis di-set NULL oleh ON DELETE SET NULL (foreign key)
    conn.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    if jumlah_buku > 0:
        flash(
            f'Kategori "{category["nama"]}" dihapus. {jumlah_buku} buku terkait kini tanpa kategori.',
            "success",
        )
    else:
        flash(f'Kategori "{category["nama"]}" berhasil dihapus!', "success")

    return redirect(url_for("categories_list"))


# ======================================================
# DOWNLOAD SOURCE CODE
# ======================================================

@app.route("/download-source")
def download_source():
    """
    Fitur utama: mem-package seluruh source code project ini
    (kecuali file yang tidak perlu) menjadi satu file .zip,
    lalu mengirimkannya sebagai file download ke browser.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    memory_file = io.BytesIO()

    exclude_dirs = {"__pycache__", ".git", "venv", ".venv", ".vercel", "node_modules"}
    exclude_files = {"library.db"}
    exclude_ext = {".pyc"}

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files:
                    continue
                if os.path.splitext(file)[1] in exclude_ext:
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                zf.write(file_path, arcname)

    memory_file.seek(0)
    filename = f"sistem-perpustakaan-source-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"

    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(debug=True, port= 5001)
