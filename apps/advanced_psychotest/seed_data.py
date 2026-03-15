"""
apps/advanced_psychotest/seed_data.py

Bank soal lengkap untuk 5 tipe tes advanced.
Jalankan: python manage.py shell -c "from apps.advanced_psychotest.seed_data import seed_all; seed_all()"
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. RAVEN'S PROGRESSIVE MATRICES  (20 soal — deskripsi pola)
# ─────────────────────────────────────────────────────────────────────────────

RAVEN_SOAL = [
    # (nomor, pertanyaan/deskripsi_pola, opsi_a, opsi_b, opsi_c, opsi_d, jwb_benar, sulit)
    (1,  "Matriks 2×2: baris 1 = [●, ●●], baris 2 = [●●●, ?]. Pola bertambah 1 titik tiap sel.",
     "●●●●", "●●", "●●●", "○", "A", "mudah"),
    (2,  "Matriks 3×3: angka pada diagonal utama = 1,5,9. Pola selisih tetap. Nilai ? di sudut kanan bawah?",
     "11", "12", "13", "14", "C", "mudah"),
    (3,  "Deretan gambar: ▲ → ▲▲ → ▲▲▲ → ?, pola penambahan satu segitiga.",
     "▲▲", "▲▲▲▲", "▲▲▲", "▲▲▲▲▲", "B", "mudah"),
    (4,  "Matriks 3×3: tiap baris jumlah bentuk = 6. Baris 3 berisi [3 kotak, 1 kotak, ?].",
     "1 kotak", "2 kotak", "3 kotak", "4 kotak", "B", "sedang"),
    (5,  "Pola rotasi: ◆ diputar 45° searah jarum jam setiap langkah. Langkah ke-5 dimulai dari posisi tegak?",
     "tegak", "miring kanan 45°", "horizontal", "miring kiri 45°", "B", "sedang"),
    (6,  "Deretan: 2, 6, 18, 54, ?. Pola perkalian konstanta.",
     "108", "162", "216", "324", "B", "mudah"),
    (7,  "Matriks 3×3: kolom 1 = [○,○○,○○○], kolom 2 = [□,□□,□□□], kolom 3 = [△,△△,?].",
     "△", "△△△△", "△△", "△△△", "D", "mudah"),
    (8,  "Pola hitam-putih: sel ganjil = hitam, sel genap = putih, diagonal = abu. Sel (3,3) bernilai?",
     "hitam", "putih", "abu", "hitam-putih", "C", "sedang"),
    (9,  "Bentuk besar mengandung bentuk kecil di dalam. Lingkaran → segitiga kecil; Kotak → bulat kecil; Segitiga → ?",
     "kotak kecil", "kotak besar", "lingkaran kecil", "segitiga kecil", "A", "sedang"),
    (10, "Deretan angka: 1, 1, 2, 3, 5, 8, ?. Fibonacci.",
     "11", "12", "13", "14", "C", "mudah"),
    (11, "Matriks: tiap baris angka = jumlah dua sel sebelumnya. Baris [3, 5, ?].",
     "6", "7", "8", "9", "C", "mudah"),
    (12, "Pola bayangan cermin vertikal: A → Ƨ; B → ꓤ; R → ?",
     "Я", "R", "r", "ɹ", "A", "sedang"),
    (13, "Deretan: Z, X, V, T, R, ?. Pola loncat 1 huruf mundur.",
     "Q", "P", "O", "N", "B", "sedang"),
    (14, "Matriks 3×3: baris 1 = [1,2,3], baris 2 = [4,5,6], baris 3 = [7,8,?].",
     "8", "9", "10", "7", "B", "mudah"),
    (15, "Tiga bentuk: ○ besar, □ sedang, △ kecil → ○ kecil, □ besar, △ sedang. Pola transformasi ukuran berputar. Langkah berikutnya?",
     "○ sedang, □ kecil, △ besar", "○ besar, □ sedang, △ kecil", "○ kecil, □ besar, △ sedang", "○ sedang, □ besar, △ kecil", "A", "sulit"),
    (16, "Pola warna: merah→biru→hijau→merah→biru→?",
     "merah", "biru", "hijau", "kuning", "C", "mudah"),
    (17, "Matriks: sel = baris × kolom. Nilai sel (4,3) = ?",
     "10", "11", "12", "14", "C", "mudah"),
    (18, "Deretan: 100, 50, 25, 12.5, ?. Pola dibagi 2.",
     "5", "6", "6.25", "7", "C", "sedang"),
    (19, "Pola simetri: tiap baris matriks 3×3 memiliki simetri horizontal. Sel yang hilang di tengah baris 2 jika [A,?,A]?",
     "B", "A", "C", "kosong", "B", "sedang"),
    (20, "Pola kompleks: angka dalam kotak = jumlah digit posisi baris + kolom. Kotak (4,4) = ?",
     "6", "7", "8", "9", "C", "sulit"),
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. COGNITIVE SPEED TEST  (30 soal — inspired by Wonderlic)
# ─────────────────────────────────────────────────────────────────────────────

COGSPEED_SOAL = [
    (1,  "Sebuah toko menjual pensil Rp 500/buah. Berapa harga 12 pensil?",
     "Rp 5.000", "Rp 6.000", "Rp 6.500", "Rp 7.000", "B", "mudah"),
    (2,  "Kata manakah yang BERBEDA maknanya dari lainnya?",
     "Gembira", "Senang", "Bahagia", "Sedih", "D", "mudah"),
    (3,  "Jika hari ini Rabu, 10 hari lagi hari apa?",
     "Jumat", "Sabtu", "Minggu", "Senin", "B", "mudah"),
    (4,  "24 ÷ 6 × 3 + 2 = ?",
     "10", "12", "14", "16", "C", "mudah"),
    (5,  "Analogi: Dokter : Rumah Sakit = Guru : ?",
     "Buku", "Sekolah", "Murid", "Pelajaran", "B", "mudah"),
    (6,  "Tiga orang berbagi keuntungan Rp 1.500.000 sama rata. Bagian masing-masing?",
     "Rp 400.000", "Rp 450.000", "Rp 500.000", "Rp 550.000", "C", "mudah"),
    (7,  "Huruf mana yang melanjutkan deretan: B, D, F, H, ?",
     "I", "J", "K", "L", "B", "mudah"),
    (8,  "Jika semua A adalah B, dan semua B adalah C, maka semua A adalah?",
     "Bukan C", "C", "Kadang C", "Tidak bisa ditentukan", "B", "sedang"),
    (9,  "Volume kubus dengan sisi 3 cm = ? cm³",
     "9", "18", "27", "36", "C", "mudah"),
    (10, "Sinonim 'efisien' adalah?",
     "Lambat", "Boros", "Hemat & tepat", "Mahal", "C", "mudah"),
    (11, "Sebuah mobil menempuh 120 km dalam 2 jam. Kecepatan rata-ratanya?",
     "50 km/jam", "55 km/jam", "60 km/jam", "65 km/jam", "C", "mudah"),
    (12, "Angka berikutnya: 3, 6, 12, 24, ?",
     "36", "42", "48", "52", "C", "mudah"),
    (13, "Kata yang ejaannya BENAR?",
     "Frekwensi", "Frekuensi", "Frequensi", "Frekunsi", "B", "mudah"),
    (14, "Jika x + 7 = 15, maka x = ?",
     "6", "7", "8", "9", "C", "mudah"),
    (15, "Antonim 'dermawan' adalah?",
     "Pemurah", "Kikir", "Baik hati", "Ramah", "B", "mudah"),
    (16, "40% dari 250 = ?",
     "80", "90", "100", "110", "C", "mudah"),
    (17, "Tiga minggu = berapa hari?",
     "17", "18", "21", "24", "C", "mudah"),
    (18, "Analogi: Panas : Api = Dingin : ?",
     "Es", "Air", "Angin", "Salju", "A", "mudah"),
    (19, "Luas persegi panjang 8×5 = ?",
     "26", "36", "40", "45", "C", "mudah"),
    (20, "Harga sepatu diskon 25% dari Rp 200.000. Harga setelah diskon?",
     "Rp 130.000", "Rp 140.000", "Rp 150.000", "Rp 160.000", "C", "mudah"),
    (21, "Manakah yang paling besar? 2/3, 3/4, 5/8, 7/12",
     "2/3", "3/4", "5/8", "7/12", "B", "sedang"),
    (22, "Jika P = 4 dan Q = 7, nilai 3P + 2Q = ?",
     "24", "25", "26", "27", "C", "sedang"),
    (23, "Kata manakah yang termasuk kategori PERALATAN DAPUR?",
     "Bor", "Wajan", "Tang", "Gergaji", "B", "mudah"),
    (24, "Berapa banyak segitiga dalam gambar yang terdiri dari 4 baris segitiga tersusun?",
     "8", "9", "10", "12", "C", "sulit"),
    (25, "Kecepatan diketik 45 kata/menit. Berapa kata dalam 20 menit?",
     "800", "850", "900", "950", "C", "mudah"),
    (26, "Urutan yang benar dari terkecil ke terbesar: 0.5, 0.05, 5, 0.005",
     "0.005, 0.05, 0.5, 5", "0.05, 0.005, 0.5, 5", "5, 0.5, 0.05, 0.005", "0.5, 0.05, 5, 0.005", "A", "mudah"),
    (27, "Rata-rata 6 angka: 4,8,3,9,5,7 = ?",
     "5", "6", "7", "8", "B", "mudah"),
    (28, "Rotasi 3D: kubus dilihat dari depan terlihat □. Dilihat dari atas juga □. Bagaimana dari samping?",
     "Lingkaran", "Segitiga", "Persegi", "Belah ketupat", "C", "sedang"),
    (29, "Jika semua karyawan berprestasi mendapat bonus, dan Andi mendapat bonus, apakah Andi pasti berprestasi?",
     "Ya, pasti", "Tidak pasti", "Pasti tidak", "Tidak relevan", "B", "sulit"),
    (30, "Berapa bilangan prima antara 20 dan 30?",
     "2 bilangan", "3 bilangan", "4 bilangan", "1 bilangan", "A", "sedang"),
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. BIG FIVE / OCEAN  (25 soal — Likert 1-5, per dimensi 5 soal)
# ─────────────────────────────────────────────────────────────────────────────
# Format: (nomor, pertanyaan, dimensi, reverse_scored)

BIGFIVE_SOAL = [
    # OPENNESS (O)
    (1,  "Saya menikmati menjelajahi ide-ide baru dan tidak biasa.", "O", False),
    (2,  "Saya lebih suka rutinitas yang sudah pasti daripada hal-hal baru.", "O", True),
    (3,  "Saya tertarik pada seni, musik, atau sastra.", "O", False),
    (4,  "Saya cepat bosan dengan kegiatan yang sama berulang kali.", "O", False),
    (5,  "Saya senang memikirkan pertanyaan-pertanyaan filosofis.", "O", False),
    # CONSCIENTIOUSNESS (C)
    (6,  "Saya selalu menyelesaikan pekerjaan sesuai jadwal yang ditetapkan.", "C", False),
    (7,  "Saya sering meninggalkan pekerjaan setengah jalan.", "C", True),
    (8,  "Saya terorganisir dan menjaga kerapian dalam bekerja.", "C", False),
    (9,  "Saya mempersiapkan rencana sebelum memulai suatu proyek.", "C", False),
    (10, "Saya mudah teralihkan dari tugas yang sedang dikerjakan.", "C", True),
    # EXTRAVERSION (E)
    (11, "Saya merasa bersemangat ketika berada di tengah banyak orang.", "E", False),
    (12, "Saya lebih suka bekerja sendiri daripada dalam tim.", "E", True),
    (13, "Saya mudah memulai percakapan dengan orang yang baru dikenal.", "E", False),
    (14, "Setelah bersosialisasi panjang, saya merasa kelelahan.", "E", True),
    (15, "Saya aktif berbicara dan berpendapat dalam diskusi kelompok.", "E", False),
    # AGREEABLENESS (A)
    (16, "Saya mudah berempati dengan perasaan orang lain.", "A", False),
    (17, "Saya sering tidak setuju dengan pendapat orang lain dan mengatakannya langsung.", "A", True),
    (18, "Saya senang membantu rekan kerja yang kesulitan.", "A", False),
    (19, "Saya percaya bahwa kebanyakan orang berniat baik.", "A", False),
    (20, "Saya merasa sulit untuk memaafkan orang yang telah menyakiti saya.", "A", True),
    # NEUROTICISM (N)
    (21, "Saya sering merasa cemas tanpa alasan yang jelas.", "N", False),
    (22, "Saya tetap tenang dalam situasi yang penuh tekanan.", "N", True),
    (23, "Suasana hati saya berubah-ubah sepanjang hari.", "N", False),
    (24, "Saya mudah merasa tersinggung oleh komentar orang lain.", "N", False),
    (25, "Saya jarang merasa khawatir tentang masa depan.", "N", True),
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. SITUATIONAL JUDGEMENT TEST — SJT  (15 skenario)
# ─────────────────────────────────────────────────────────────────────────────
# skor per opsi: 3=sangat tepat, 2=cukup tepat, 1=kurang tepat, 0=tidak tepat

SJT_SOAL = [
    (1, "Anda menemukan rekan kerja memalsukan laporan absensi. Apa yang Anda lakukan?",
     "Melaporkan langsung ke HR dengan bukti",
     "Mengabaikannya karena bukan urusan Anda",
     "Menegur rekan secara pribadi terlebih dahulu",
     "Membicarakannya dengan rekan lain",
     3, 0, 2, 1),
    (2, "Deadline proyek besok, tapi Anda menyadari ada kesalahan besar dalam pekerjaan Anda. Apa yang Anda lakukan?",
     "Menyerahkan tetap meskipun ada kesalahan",
     "Segera laporkan ke atasan dan tawarkan solusi perbaikan",
     "Minta bantuan rekan untuk menutupi kesalahan",
     "Meminta perpanjangan waktu tanpa menjelaskan alasan",
     0, 3, 1, 2),
    (3, "Atasan meminta Anda mengerjakan tugas yang menurut Anda tidak etis. Respons Anda?",
     "Langsung menolak tanpa penjelasan",
     "Menurut saja demi menjaga hubungan",
     "Mengklarifikasi alasan permintaan, sampaikan keberatan secara profesional",
     "Melaporkan ke HRD tanpa bicara ke atasan",
     1, 0, 3, 2),
    (4, "Klien penting marah karena keterlambatan layanan. Anda sebagai frontliner, apa yang dilakukan?",
     "Membela diri dan menjelaskan bahwa itu bukan salah Anda",
     "Minta maaf, dengarkan keluhan, cari solusi segera",
     "Minta klien menunggu dan langsung hubungi supervisor",
     "Memberikan diskon tanpa persetujuan atasan",
     0, 3, 2, 1),
    (5, "Tim Anda tidak mencapai target bulan ini. Sebagai anggota tim, Anda?",
     "Menyalahkan rekan yang berkinerja rendah",
     "Menganalisis penyebab bersama tim dan buat rencana perbaikan",
     "Diam dan menunggu instruksi dari atasan",
     "Mencari proyek lain yang lebih mudah dicapai",
     0, 3, 1, 2),
    (6, "Anda mendapat dua tugas penting dengan deadline bersamaan. Apa pendekatan Anda?",
     "Kerjakan yang paling disukai terlebih dahulu",
     "Prioritaskan berdasarkan dampak bisnis, komunikasikan ke atasan",
     "Minta rekan mengerjakan salah satunya",
     "Selesaikan keduanya dengan kualitas setengah-setengah",
     0, 3, 2, 1),
    (7, "Anda memiliki ide inovatif tapi bertentangan dengan kebijakan lama. Langkah Anda?",
     "Langsung implementasikan tanpa izin",
     "Simpan ide karena terlalu berisiko",
     "Susun proposal, presentasikan dengan data pendukung ke atasan",
     "Gosipkan ide ke rekan agar viral secara internal",
     0, 1, 3, 2),
    (8, "Rekan kerja dalam tim Anda terus menerus terlambat dan memperlambat proyek. Anda?",
     "Komplain langsung ke manajer tanpa bicara ke rekan",
     "Lakukan percakapan langsung secara empatis, tawarkan bantuan",
     "Ambil alih seluruh tugasnya",
     "Abaikan karena bukan tanggung jawab Anda",
     1, 3, 2, 0),
    (9, "Anda menerima kredit/pujian atas pekerjaan yang sebenarnya dilakukan rekan Anda. Anda?",
     "Terima saja karena menguntungkan karir",
     "Langsung klarifikasi ke atasan bahwa itu kerja rekan Anda",
     "Bisikkan ke rekan bahwa Anda sudah mendapat pujian",
     "Diam dan berikan kompensasi ke rekan secara pribadi",
     0, 3, 0, 1),
    (10, "Anda mengalami burnout berat. Apa tindakan Anda?",
     "Terus bekerja sampai proyek selesai baru istirahat",
     "Komunikasikan kondisi ke atasan, minta penyesuaian beban kerja",
     "Tiba-tiba tidak masuk tanpa pemberitahuan",
     "Resign tanpa mencari solusi lain",
     1, 3, 0, 0),
    (11, "Dalam rapat, atasan memutuskan sesuatu yang menurut Anda salah. Anda?",
     "Diam dan setuju demi menghindari konflik",
     "Protes keras di depan semua peserta rapat",
     "Ajukan pertanyaan klarifikasi dan sampaikan perspektif Anda dengan sopan",
     "Komplain ke rekan setelah rapat",
     1, 0, 3, 2),
    (12, "Seorang pelanggan meminta sesuatu yang di luar kebijakan perusahaan. Anda?",
     "Langsung menolak tanpa penjelasan",
     "Setuju saja agar pelanggan senang",
     "Jelaskan kebijakan dengan sopan, tawarkan alternatif solusi",
     "Alihkan ke rekan lain tanpa penjelasan",
     1, 0, 3, 2),
    (13, "Anda menemukan proses kerja yang tidak efisien di divisi Anda. Anda?",
     "Abaikan karena prosedur sudah ditetapkan",
     "Dokumentasikan masalah dan usulan perbaikan, sampaikan ke atasan",
     "Langsung ubah prosedur sendiri",
     "Keluhkan ke sesama rekan",
     0, 3, 1, 2),
    (14, "Proyek berjalan lancar tapi ada konflik internal dalam tim. Sebagai anggota, Anda?",
     "Pilih kubu yang menurut Anda benar",
     "Fasilitasi diskusi terbuka untuk mencari solusi bersama",
     "Laporkan semua yang terlibat ke HR",
     "Fokus pada pekerjaan, abaikan konflik",
     0, 3, 1, 2),
    (15, "Anda diberi tanggung jawab baru yang belum pernah Anda lakukan. Respons Anda?",
     "Tolak karena di luar kompetensi Anda",
     "Terima, cari mentor/sumber belajar, minta arahan awal",
     "Terima tapi kerjakan sesuai pengetahuan lama",
     "Terima tapi diam-diam delegasikan ke orang lain",
     0, 3, 1, 1),
]

# ─────────────────────────────────────────────────────────────────────────────
# 5. CULTURE FAIR INTELLIGENCE TEST (CFIT)  (20 soal — non-verbal reasoning)
# ─────────────────────────────────────────────────────────────────────────────

CFIT_SOAL = [
    (1,  "Deretan: ▲ ○ ▲▲ ○○ ▲▲▲ ?",
     "○", "○○○", "▲▲▲▲", "△", "B", "mudah"),
    (2,  "Mana yang TIDAK termasuk kelompok: segitiga, kotak, lingkaran, merah",
     "segitiga", "kotak", "lingkaran", "merah", "D", "mudah"),
    (3,  "Pola lipatan kertas: kertas persegi dilipat 2× menghasilkan persegi kecil. Jika dilubangi di tengah, ketika dibuka ada berapa lubang?",
     "1", "2", "3", "4", "D", "sedang"),
    (4,  "Bayangan: benda P terletak di sebelah kiri cermin. Bayangannya terletak di?",
     "Kiri cermin", "Kanan cermin", "Atas cermin", "Bawah cermin", "B", "mudah"),
    (5,  "Klasifikasi: {anjing, kucing, ikan, pohon}. Mana yang tidak satu kelompok?",
     "anjing", "kucing", "ikan", "pohon", "D", "mudah"),
    (6,  "Deretan angka: 2, 4, 8, 16, 32, ?",
     "48", "56", "64", "72", "C", "mudah"),
    (7,  "Mana bentuk yang bisa dilipat menjadi kubus? (A=T-shape, B=cross, C=L-shape, D=plus-sign)",
     "A", "B", "C", "D", "B", "sulit"),
    (8,  "Seri gambar: ● dalam □ → □ dalam ● → ? (pola bertukar posisi)",
     "● dalam □", "□ dalam ●", "○ dalam □", "● tanpa □", "A", "sedang"),
    (9,  "Lima bentuk berbeda ukuran, manakah yang terletak di TENGAH jika diurutkan besar-kecil?",
     "Terkecil", "Terbesar", "Ketiga dari terkecil", "Kedua dari terbesar", "C", "mudah"),
    (10, "Matriks ganjil: baris1=[■□■], baris2=[□■□], baris3=[■□?]",
     "■", "□", "▲", "○", "A", "mudah"),
    (11, "Rotasi: gambar bintang 5 sudut diputar 72°. Hasilnya tampak?",
     "Berbeda", "Sama", "Terbalik", "Lebih kecil", "B", "sedang"),
    (12, "Analogi gambar: ○ : ◎ = □ : ?",
     "□□", "■", "◻", "⊡", "D", "sedang"),
    (13, "Klasifikasi warna-bentuk: merah-besar, biru-kecil, merah-kecil, biru-?",
     "besar", "kecil", "sedang", "merah", "A", "sedang"),
    (14, "Jumlah sisi: segitiga+kotak+segi5+segi6 = ?",
     "16", "17", "18", "19", "C", "mudah"),
    (15, "Pola: setiap baris matriks 3×3 mengandung ○□△ masing-masing sekali. Sel kosong di baris3=[□,△,?]",
     "□", "△", "○", "■", "C", "mudah"),
    (16, "Bayangan 3D: kubus 2×2×2 dicat merah di semua permukaan lalu dipotong jadi kubus 1×1×1. Berapa kubus yang tidak ada cat sama sekali?",
     "0", "1", "2", "4", "A", "sulit"),
    (17, "Deretan: A1, B2, C3, D4, ?",
     "D5", "E4", "E5", "F5", "C", "mudah"),
    (18, "Cermin diagonal: jika huruf P dicerminkan pada sumbu diagonal 45°, hasilnya?",
     "P terbalik", "d", "q", "Γ", "D", "sulit"),
    (19, "Mana yang BERBEDA: {penjumlahan, pengurangan, perkalian, variabel}?",
     "penjumlahan", "pengurangan", "perkalian", "variabel", "D", "mudah"),
    (20, "Pola kompleks: tiap sel bernilai = (baris × kolom) mod 3. Nilai sel (4,5)?",
     "0", "1", "2", "3", "C", "sulit"),
]


# ─────────────────────────────────────────────────────────────────────────────
# SEED FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def seed_all(clear=False):
    from apps.advanced_psychotest.models import AdvSoal

    if clear:
        AdvSoal.objects.all().delete()
        print("🗑  Soal lama dihapus.")

    created = 0

    # 1. Raven
    for row in RAVEN_SOAL:
        nomor, soal, a, b, c, d, jwb, sulit = row
        obj, c_ = AdvSoal.objects.get_or_create(
            test_type='raven', nomor=nomor,
            defaults=dict(tipe_soal='pilihan_ganda', pertanyaan=soal,
                          opsi_a=a, opsi_b=b, opsi_c=c, opsi_d=d,
                          jawaban_benar=jwb, tingkat_kesulitan=sulit)
        )
        if c_: created += 1

    # 2. Cognitive Speed
    for row in COGSPEED_SOAL:
        nomor, soal, a, b, c, d, jwb, sulit = row
        obj, c_ = AdvSoal.objects.get_or_create(
            test_type='cogspeed', nomor=nomor,
            defaults=dict(tipe_soal='pilihan_ganda', pertanyaan=soal,
                          opsi_a=a, opsi_b=b, opsi_c=c, opsi_d=d,
                          jawaban_benar=jwb, tingkat_kesulitan=sulit)
        )
        if c_: created += 1

    # 3. Big Five
    for row in BIGFIVE_SOAL:
        nomor, soal, dim, rev = row
        obj, c_ = AdvSoal.objects.get_or_create(
            test_type='bigfive', nomor=nomor,
            defaults=dict(tipe_soal='likert', pertanyaan=soal,
                          bigfive_dimensi=dim, bigfive_reverse=rev,
                          opsi_a='Sangat Tidak Setuju',
                          opsi_b='Tidak Setuju',
                          opsi_c='Netral',
                          opsi_d='Setuju',
                          opsi_e='Sangat Setuju',
                          tingkat_kesulitan='sedang')
        )
        if c_: created += 1

    # 4. SJT
    for row in SJT_SOAL:
        nomor, soal, a, b, c, d, sa, sb, sc, sd = row
        obj, c_ = AdvSoal.objects.get_or_create(
            test_type='sjt', nomor=nomor,
            defaults=dict(tipe_soal='pilihan_ganda', pertanyaan=soal,
                          opsi_a=a, opsi_b=b, opsi_c=c, opsi_d=d,
                          sjt_skor_a=sa, sjt_skor_b=sb, sjt_skor_c=sc, sjt_skor_d=sd,
                          tingkat_kesulitan='sedang')
        )
        if c_: created += 1

    # 5. CFIT
    for row in CFIT_SOAL:
        nomor, soal, a, b, c, d, jwb, sulit = row
        obj, c_ = AdvSoal.objects.get_or_create(
            test_type='cfit', nomor=nomor,
            defaults=dict(tipe_soal='pilihan_ganda', pertanyaan=soal,
                          opsi_a=a, opsi_b=b, opsi_c=c, opsi_d=d,
                          jawaban_benar=jwb, tingkat_kesulitan=sulit)
        )
        if c_: created += 1

    print(f"✅ Seed selesai: {created} soal baru ditambahkan.")
    print(f"   Total soal: {AdvSoal.objects.count()}")
