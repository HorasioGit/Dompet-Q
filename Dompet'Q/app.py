from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Diperlukan untuk flash messages
DB_NAME = 'catatan_keuangan.db'

# Fungsi untuk koneksi ke database
def db_connect():
    return sqlite3.connect(DB_NAME)

# Membuat tabel jika belum ada
def create_db():
    with db_connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS catatan (
                            no INTEGER PRIMARY KEY AUTOINCREMENT,
                            tanggal TEXT NOT NULL,
                            jenis TEXT NOT NULL,
                            jumlah INTEGER NOT NULL,
                            deskripsi TEXT)''')

# Mendapatkan semua catatan
def get_catatan():
    with db_connect() as conn:
        return conn.execute('SELECT * FROM catatan ORDER BY tanggal DESC').fetchall()

# Mendapatkan total jumlah berdasarkan jenis
def get_total(jenis):
    with db_connect() as conn:
        result = conn.execute('SELECT SUM(jumlah) FROM catatan WHERE jenis = ?', (jenis,)).fetchone()[0]
        return result if result else 0

# Menambahkan catatan baru
def tambah_catatan(jenis, jumlah, deskripsi):
    with db_connect() as conn:
        conn.execute('INSERT INTO catatan (tanggal, jenis, jumlah, deskripsi) VALUES (date("now"), ?, ?, ?)', 
                     (jenis, int(jumlah), deskripsi))

# Mereset semua catatan
def reset_catatan():
    with db_connect() as conn:
        conn.execute('DELETE FROM catatan')
        conn.execute('DELETE FROM sqlite_sequence WHERE name="catatan"')

@app.route('/')
def index():
    histori = get_catatan()
    total_pemasukan = get_total("Pemasukan")
    total_pengeluaran = get_total("Pengeluaran")
    saldo = total_pemasukan - total_pengeluaran
    return render_template('index.html', histori=histori, total_pemasukan=total_pemasukan, 
                           total_pengeluaran=total_pengeluaran, saldo=saldo)

@app.route('/add', methods=['POST'])
def add():
    jenis = request.form['jenis']
    jumlah_raw = request.form['jumlah']
    deskripsi = request.form['deskripsi']

    try:
        # Mengubah input dengan titik atau koma menjadi angka
        jumlah = int(float(jumlah_raw.replace('.', '').replace(',', '.')))
    except ValueError:
        flash("Sepertinya ada yang salah, coba isi kembali!")
        return redirect(url_for('index'))

    total_pemasukan = get_total("Pemasukan")
    total_pengeluaran = get_total("Pengeluaran")
    saldo = total_pemasukan - total_pengeluaran

    if jenis == "Pengeluaran" and jumlah > saldo:
        flash("Uang tidak cukup :(")
        return redirect(url_for('index'))

    tambah_catatan(jenis, jumlah, deskripsi)
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    reset_catatan()
    flash("Semua data catatan telah dihapus")
    return redirect(url_for('index'))

@app.template_filter()
def format_jumlah(value):
    return f"{value:,}".replace(",", ".")

if __name__ == '__main__':
    create_db()
    app.run(debug=True)
