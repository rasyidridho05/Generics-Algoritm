# =============================================================================
# Sistem Fuzzy Logic untuk Pemilihan 5 Restoran Terbaik di Kota Bandung
# Mata Kuliah: Kecerdasan Buatan - S1 Rekayasa Perangkat Lunak
# Semester Genap 2025/2026
# =============================================================================
# CATATAN: Program ini TIDAK menggunakan library fuzzy apapun.
#          Seluruh proses fuzzification, inferensi, dan defuzzification
#          dibangun dari nol secara manual.
# =============================================================================

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import math

# =============================================================================
# BAGIAN 1: MEMBACA DATA DARI FILE
# =============================================================================

def baca_data(nama_file):
    """
    Membaca data restoran dari file Excel (.xlsx).
    Mengembalikan list of dict berisi: id, pelayanan, harga.
    """
    wb = openpyxl.load_workbook(nama_file)
    ws = wb.active
    data = []
    # Baris pertama adalah header, mulai dari baris ke-2
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is not None:
            data.append({
                'id': int(row[0]),
                'pelayanan': float(row[1]),
                'harga': float(row[2])
            })
    return data


# =============================================================================
# BAGIAN 2: DESAIN FUNGSI KEANGGOTAAN (MEMBERSHIP FUNCTIONS)
# =============================================================================

# --- INPUT 1: Kualitas Pelayanan (range: 1 - 100) ---
# Variabel linguistik: BURUK, SEDANG, BAIK
# Menggunakan fungsi segitiga (triangular) dan trapesium (trapezoidal)

def mf_pelayanan_buruk(x):
    """
    Pelayanan BURUK: trapesium kiri
    Penuh di [1, 30], turun di [30, 50], nol di [50, 100]
    """
    if x <= 30:
        return 1.0
    elif x <= 50:
        return (50 - x) / (50 - 30)   # turun linear dari 30 ke 50
    else:
        return 0.0

def mf_pelayanan_sedang(x):
    """
    Pelayanan SEDANG: segitiga
    Naik di [30, 50], puncak di 50, turun di [50, 70]
    """
    if x <= 30:
        return 0.0
    elif x <= 50:
        return (x - 30) / (50 - 30)   # naik dari 30 ke 50
    elif x <= 70:
        return (70 - x) / (70 - 50)   # turun dari 50 ke 70
    else:
        return 0.0

def mf_pelayanan_baik(x):
    """
    Pelayanan BAIK: trapesium kanan
    Nol di [1, 50], naik di [50, 70], penuh di [70, 100]
    """
    if x <= 50:
        return 0.0
    elif x <= 70:
        return (x - 50) / (70 - 50)   # naik dari 50 ke 70
    else:
        return 1.0


# --- INPUT 2: Harga (range: 25000 - 55000) ---
# Variabel linguistik: MURAH, SEDANG, MAHAL
# Menggunakan fungsi trapesium dan segitiga

def mf_harga_murah(x):
    """
    Harga MURAH: trapesium kiri
    Penuh di [20000, 30000], turun di [30000, 38000], nol di atas 38000
    """
    if x <= 30000:
        return 1.0
    elif x <= 38000:
        return (38000 - x) / (38000 - 30000)
    else:
        return 0.0

def mf_harga_sedang(x):
    """
    Harga SEDANG: segitiga
    Naik di [30000, 38000], puncak di 38000, turun di [38000, 47000]
    """
    if x <= 30000:
        return 0.0
    elif x <= 38000:
        return (x - 30000) / (38000 - 30000)
    elif x <= 47000:
        return (47000 - x) / (47000 - 38000)
    else:
        return 0.0

def mf_harga_mahal(x):
    """
    Harga MAHAL: trapesium kanan
    Nol di bawah 38000, naik di [38000, 47000], penuh di [47000, 55000]
    """
    if x <= 38000:
        return 0.0
    elif x <= 47000:
        return (x - 38000) / (47000 - 38000)
    else:
        return 1.0


# =============================================================================
# BAGIAN 3: FUZZIFIKASI
# =============================================================================

def fuzzifikasi(pelayanan, harga):
    """
    Mengubah nilai crisp input menjadi derajat keanggotaan fuzzy.
    Mengembalikan dict berisi derajat keanggotaan setiap variabel linguistik.
    """
    hasil = {
        # Derajat keanggotaan Pelayanan
        'pelayanan_buruk' : mf_pelayanan_buruk(pelayanan),
        'pelayanan_sedang': mf_pelayanan_sedang(pelayanan),
        'pelayanan_baik'  : mf_pelayanan_baik(pelayanan),
        # Derajat keanggotaan Harga
        'harga_murah' : mf_harga_murah(harga),
        'harga_sedang': mf_harga_sedang(harga),
        'harga_mahal' : mf_harga_mahal(harga),
    }
    return hasil


# =============================================================================
# BAGIAN 4: DESAIN ATURAN INFERENSI (RULE BASE)
# =============================================================================
# Output: KELAYAKAN restoran (skor rekomendasi)
# Variabel linguistik output: TIDAK_LAYAK, CUKUP_LAYAK, LAYAK, SANGAT_LAYAK
#
# Logika: Restoran terbaik = pelayanan BAIK + harga MURAH/SEDANG
#         Pelayanan bagus tapi mahal = cukup layak
#         Pelayanan buruk = tidak layak
#
# Tabel Aturan (9 aturan):
# -----------------------------------------------------------
# Pelayanan \ Harga | MURAH       | SEDANG      | MAHAL
# -----------------------------------------------------------
# BURUK             | CUKUP_LAYAK | TIDAK_LAYAK | TIDAK_LAYAK
# SEDANG            | LAYAK       | CUKUP_LAYAK | TIDAK_LAYAK
# BAIK              | SANGAT_LAYAK| LAYAK       | CUKUP_LAYAK
# -----------------------------------------------------------

def inferensi(fuzz):
    """
    Menerapkan 9 aturan inferensi Mamdani (metode MIN untuk AND).
    Mengembalikan dict berisi kekuatan aktivasi tiap output linguistik.
    """
    pb = fuzz['pelayanan_buruk']
    ps = fuzz['pelayanan_sedang']
    pk = fuzz['pelayanan_baik']
    hm = fuzz['harga_murah']
    hs = fuzz['harga_sedang']
    ha = fuzz['harga_mahal']

    # Kekuatan setiap aturan menggunakan fungsi MIN (operator AND)
    # Output: TIDAK_LAYAK, CUKUP_LAYAK, LAYAK, SANGAT_LAYAK

    # R1: IF pelayanan BURUK AND harga MURAH THEN CUKUP_LAYAK
    r1 = min(pb, hm)
    # R2: IF pelayanan BURUK AND harga SEDANG THEN TIDAK_LAYAK
    r2 = min(pb, hs)
    # R3: IF pelayanan BURUK AND harga MAHAL THEN TIDAK_LAYAK
    r3 = min(pb, ha)
    # R4: IF pelayanan SEDANG AND harga MURAH THEN LAYAK
    r4 = min(ps, hm)
    # R5: IF pelayanan SEDANG AND harga SEDANG THEN CUKUP_LAYAK
    r5 = min(ps, hs)
    # R6: IF pelayanan SEDANG AND harga MAHAL THEN TIDAK_LAYAK
    r6 = min(ps, ha)
    # R7: IF pelayanan BAIK AND harga MURAH THEN SANGAT_LAYAK
    r7 = min(pk, hm)
    # R8: IF pelayanan BAIK AND harga SEDANG THEN LAYAK
    r8 = min(pk, hs)
    # R9: IF pelayanan BAIK AND harga MAHAL THEN CUKUP_LAYAK
    r9 = min(pk, ha)

    # Agregasi: gabungkan aturan dengan output yang sama menggunakan MAX
    aktivasi = {
        'tidak_layak' : max(r2, r3, r6),
        'cukup_layak' : max(r1, r5, r9),
        'layak'       : max(r4, r8),
        'sangat_layak': r7
    }
    return aktivasi


# =============================================================================
# BAGIAN 5: DEFUZZIFIKASI (Metode Centroid / Center of Area)
# =============================================================================
# Output KELAYAKAN: range 0 - 100
# Fungsi keanggotaan output:
#   TIDAK_LAYAK  : trapesium kiri  [0, 25]     puncak di [0,15], turun ke 25
#   CUKUP_LAYAK  : segitiga        [15, 50]    puncak di 35
#   LAYAK        : segitiga        [40, 75]    puncak di 60
#   SANGAT_LAYAK : trapesium kanan [65, 100]   naik dari 65 ke 80, penuh di [80,100]

def mf_output_tidak_layak(z):
    """Trapesium kiri: penuh [0,15], turun [15,25], nol di atas 25"""
    if z <= 15:
        return 1.0
    elif z <= 25:
        return (25 - z) / (25 - 15)
    else:
        return 0.0

def mf_output_cukup_layak(z):
    """Segitiga: naik [15,35], turun [35,50]"""
    if z <= 15:
        return 0.0
    elif z <= 35:
        return (z - 15) / (35 - 15)
    elif z <= 50:
        return (50 - z) / (50 - 35)
    else:
        return 0.0

def mf_output_layak(z):
    """Segitiga: naik [40,60], turun [60,75]"""
    if z <= 40:
        return 0.0
    elif z <= 60:
        return (z - 40) / (60 - 40)
    elif z <= 75:
        return (75 - z) / (75 - 60)
    else:
        return 0.0

def mf_output_sangat_layak(z):
    """Trapesium kanan: naik [65,80], penuh [80,100]"""
    if z <= 65:
        return 0.0
    elif z <= 80:
        return (z - 65) / (80 - 65)
    else:
        return 1.0

def defuzzifikasi(aktivasi, num_points=1000):
    """
    Defuzzifikasi menggunakan metode Centroid (Center of Area).
    Rumus: z* = (integral z * mu(z) dz) / (integral mu(z) dz)
    Pendekatan numerik dengan diskretisasi sebanyak num_points titik.
    """
    z_min = 0.0
    z_max = 100.0
    step = (z_max - z_min) / num_points

    numerator = 0.0    # pembilang: sum(z * mu(z))
    denominator = 0.0  # penyebut:  sum(mu(z))

    alpha_tl = aktivasi['tidak_layak']
    alpha_cl = aktivasi['cukup_layak']
    alpha_l  = aktivasi['layak']
    alpha_sl = aktivasi['sangat_layak']

    for i in range(num_points):
        z = z_min + (i + 0.5) * step  # titik tengah setiap interval

        # Clipping (potong) setiap fungsi keanggotaan output sesuai kekuatan aturan
        mu_tl = min(alpha_tl, mf_output_tidak_layak(z))
        mu_cl = min(alpha_cl, mf_output_cukup_layak(z))
        mu_l  = min(alpha_l,  mf_output_layak(z))
        mu_sl = min(alpha_sl, mf_output_sangat_layak(z))

        # Agregasi: ambil nilai maksimum dari semua potongan
        mu_total = max(mu_tl, mu_cl, mu_l, mu_sl)

        numerator   += z * mu_total * step
        denominator += mu_total * step

    # Hindari pembagian dengan nol
    if denominator == 0:
        return 0.0
    return numerator / denominator


# =============================================================================
# BAGIAN 6: PROSES UTAMA - Hitung skor semua restoran
# =============================================================================

def hitung_semua_skor(data):
    """
    Menjalankan seluruh pipeline fuzzy untuk setiap restoran:
    fuzzifikasi -> inferensi -> defuzzifikasi
    """
    hasil = []
    for restoran in data:
        # Fuzzifikasi input
        fuzz = fuzzifikasi(restoran['pelayanan'], restoran['harga'])
        # Inferensi (apply rules)
        aktivasi = inferensi(fuzz)
        # Defuzzifikasi (hasilkan skor crisp)
        skor = defuzzifikasi(aktivasi)
        hasil.append({
            'id'       : restoran['id'],
            'pelayanan': restoran['pelayanan'],
            'harga'    : restoran['harga'],
            'skor'     : round(skor, 4)
        })
    # Urutkan dari skor tertinggi ke terendah
    hasil.sort(key=lambda x: x['skor'], reverse=True)
    return hasil


# =============================================================================
# BAGIAN 7: SIMPAN OUTPUT KE FILE EXCEL
# =============================================================================

def simpan_output(top5, nama_file='peringkat.xlsx'):
    """
    Menyimpan 5 restoran terbaik ke file Excel dengan formatting rapi.
    Kolom: Peringkat, ID Restoran, Kualitas Pelayanan, Harga, Skor Kelayakan
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "5 Restoran Terbaik"

    # --- Gaya sel ---
    header_font   = Font(bold=True, color='FFFFFF', size=12)
    header_fill   = PatternFill('solid', start_color='1F4E79')  # biru tua
    rank_fill     = PatternFill('solid', start_color='D6E4F0')  # biru muda
    center_align  = Alignment(horizontal='center', vertical='center')
    thin_border   = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # --- Judul ---
    ws.merge_cells('A1:E1')
    ws['A1'] = '5 RESTORAN TERBAIK DI BANDUNG - SISTEM FUZZY LOGIC'
    ws['A1'].font      = Font(bold=True, size=14, color='1F4E79')
    ws['A1'].alignment = center_align

    # --- Header tabel ---
    headers = ['Peringkat', 'ID Restoran', 'Kualitas Pelayanan (1-100)',
               'Harga (Rp)', 'Skor Kelayakan (0-100)']
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center_align
        cell.border    = thin_border

    # --- Data baris ---
    for i, r in enumerate(top5, start=1):
        row_idx = i + 3
        data_row = [i, r['id'], r['pelayanan'], r['harga'], r['skor']]
        for col, val in enumerate(data_row, start=1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            cell.alignment = center_align
            cell.border    = thin_border
            if col == 1:
                cell.fill = rank_fill
                cell.font = Font(bold=True)
            # Format harga dengan ribuan
            if col == 4:
                cell.number_format = '#,##0'
            # Format skor 2 desimal
            if col == 5:
                cell.number_format = '0.00'

    # --- Lebar kolom ---
    lebar = [12, 14, 28, 18, 25]
    for i, w in enumerate(lebar, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # --- Tinggi baris ---
    ws.row_dimensions[1].height = 28
    ws.row_dimensions[3].height = 22

    wb.save(nama_file)
    print(f"\n[OK] File output disimpan: {nama_file}")


# =============================================================================
# BAGIAN 8: TAMPILKAN HASIL DI KONSOL
# =============================================================================

def tampilkan_hasil(top5):
    """Menampilkan 5 restoran terbaik dalam format tabel di konsol."""
    print("\n" + "=" * 70)
    print("   SISTEM FUZZY LOGIC - 5 RESTORAN TERBAIK DI BANDUNG")
    print("=" * 70)
    print(f"{'Peringkat':<10} {'ID':>5}  {'Pelayanan':>12}  {'Harga (Rp)':>14}  {'Skor':>8}")
    print("-" * 70)
    for i, r in enumerate(top5, start=1):
        print(f"  #{i:<8} {r['id']:>5}  {r['pelayanan']:>12.0f}  {r['harga']:>14,.0f}  {r['skor']:>8.4f}")
    print("=" * 70)


# =============================================================================
# MAIN - Titik masuk program
# =============================================================================

if __name__ == '__main__':
    print("[INFO] Membaca data dari file restoran.xlsx ...")
    data = baca_data('restoran.xlsx')
    print(f"[INFO] Total data restoran: {len(data)}")

    print("[INFO] Menjalankan sistem Fuzzy Logic ...")
    semua_hasil = hitung_semua_skor(data)

    # Ambil 5 terbaik
    top5 = semua_hasil[:5]

    # Tampilkan di konsol
    tampilkan_hasil(top5)

    # Simpan ke file Excel
    simpan_output(top5, 'peringkat.xlsx')