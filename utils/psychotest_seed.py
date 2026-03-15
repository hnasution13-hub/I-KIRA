"""
utils/psychotest_seed.py

Jalankan sekali untuk mengisi soal default ke database:
    python manage.py shell -c "from utils.psychotest_seed import seed; seed()"
"""

SOAL_LOGIKA = [
    {
        'pertanyaan': 'Deret: 2, 4, 8, 16, ... Angka berikutnya adalah?',
        'opsi_a': '24', 'opsi_b': '32', 'opsi_c': '20', 'opsi_d': '28',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Deret: 1, 3, 6, 10, 15, ... Angka berikutnya adalah?',
        'opsi_a': '18', 'opsi_b': '19', 'opsi_c': '21', 'opsi_d': '20',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Deret: 100, 91, 83, 76, 70, ... Angka berikutnya adalah?',
        'opsi_a': '62', 'opsi_b': '64', 'opsi_c': '65', 'opsi_d': '63',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Deret: A, C, E, G, ... Huruf berikutnya adalah?',
        'opsi_a': 'H', 'opsi_b': 'I', 'opsi_c': 'J', 'opsi_d': 'K',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Semua kucing adalah hewan. Beberapa hewan adalah peliharaan. Kesimpulan yang benar?',
        'opsi_a': 'Semua kucing adalah peliharaan',
        'opsi_b': 'Beberapa kucing mungkin bukan peliharaan',
        'opsi_c': 'Tidak ada kucing yang peliharaan',
        'opsi_d': 'Semua peliharaan adalah kucing',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Jika hari ini Rabu, 3 hari yang lalu adalah?',
        'opsi_a': 'Jumat', 'opsi_b': 'Sabtu', 'opsi_c': 'Minggu', 'opsi_d': 'Kamis',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Deret: 3, 6, 12, 24, ... Angka berikutnya adalah?',
        'opsi_a': '36', 'opsi_b': '42', 'opsi_c': '48', 'opsi_d': '30',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Mana yang tidak termasuk kelompok yang sama? Apel, Mangga, Wortel, Pisang',
        'opsi_a': 'Apel', 'opsi_b': 'Mangga', 'opsi_c': 'Wortel', 'opsi_d': 'Pisang',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Deret: 1, 4, 9, 16, 25, ... Angka berikutnya adalah?',
        'opsi_a': '30', 'opsi_b': '35', 'opsi_c': '36', 'opsi_d': '49',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Bila A > B dan B > C, maka?',
        'opsi_a': 'C > A', 'opsi_b': 'A = C', 'opsi_c': 'A > C', 'opsi_d': 'C > B',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Deret: 5, 10, 20, 40, ... Angka berikutnya adalah?',
        'opsi_a': '60', 'opsi_b': '70', 'opsi_c': '75', 'opsi_d': '80',
        'jawaban_benar': 'D',
    },
    {
        'pertanyaan': 'Semua A adalah B. Tidak ada B yang C. Maka?',
        'opsi_a': 'Semua A adalah C',
        'opsi_b': 'Tidak ada A yang C',
        'opsi_c': 'Beberapa A adalah C',
        'opsi_d': 'Semua C adalah A',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Deret: Z, X, V, T, ... Huruf berikutnya adalah?',
        'opsi_a': 'P', 'opsi_b': 'Q', 'opsi_c': 'R', 'opsi_d': 'S',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Budi lebih tinggi dari Andi. Andi lebih tinggi dari Cici. Siapa yang paling pendek?',
        'opsi_a': 'Budi', 'opsi_b': 'Andi', 'opsi_c': 'Cici', 'opsi_d': 'Sama tinggi',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Deret: 2, 3, 5, 8, 13, ... Angka berikutnya adalah?',
        'opsi_a': '18', 'opsi_b': '20', 'opsi_c': '21', 'opsi_d': '23',
        'jawaban_benar': 'C',
    },
]

SOAL_VERBAL = [
    {
        'pertanyaan': 'Sinonim dari kata ABADI adalah?',
        'opsi_a': 'Sementara', 'opsi_b': 'Kekal', 'opsi_c': 'Fana', 'opsi_d': 'Sesaat',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Antonim dari kata GIGIH adalah?',
        'opsi_a': 'Rajin', 'opsi_b': 'Semangat', 'opsi_c': 'Malas', 'opsi_d': 'Tekun',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'BUKU : MEMBACA = PENSIL : ?',
        'opsi_a': 'Menulis', 'opsi_b': 'Kertas', 'opsi_c': 'Tajam', 'opsi_d': 'Menghapus',
        'jawaban_benar': 'A',
    },
    {
        'pertanyaan': 'Sinonim dari kata INOVASI adalah?',
        'opsi_a': 'Tradisi', 'opsi_b': 'Pembaruan', 'opsi_c': 'Kebiasaan', 'opsi_d': 'Rutinitas',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Antonim dari kata TRANSPARAN adalah?',
        'opsi_a': 'Jelas', 'opsi_b': 'Terbuka', 'opsi_c': 'Buram', 'opsi_d': 'Terang',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'DOKTER : RUMAH SAKIT = GURU : ?',
        'opsi_a': 'Buku', 'opsi_b': 'Murid', 'opsi_c': 'Sekolah', 'opsi_d': 'Ilmu',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Sinonim dari kata EFISIEN adalah?',
        'opsi_a': 'Boros', 'opsi_b': 'Lambat', 'opsi_c': 'Hemat', 'opsi_d': 'Mahal',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Antonim dari kata DERMAWAN adalah?',
        'opsi_a': 'Kaya', 'opsi_b': 'Kikir', 'opsi_c': 'Baik hati', 'opsi_d': 'Murah hati',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'PANAS : API = DINGIN : ?',
        'opsi_a': 'Angin', 'opsi_b': 'Es', 'opsi_c': 'Air', 'opsi_d': 'Salju',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Sinonim dari kata AMBIGU adalah?',
        'opsi_a': 'Jelas', 'opsi_b': 'Tegas', 'opsi_c': 'Mendua', 'opsi_d': 'Pasti',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Antonim dari kata OPTIMIS adalah?',
        'opsi_a': 'Yakin', 'opsi_b': 'Semangat', 'opsi_c': 'Pesimis', 'opsi_d': 'Percaya diri',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'LAPAR : MAKAN = HAUS : ?',
        'opsi_a': 'Tidur', 'opsi_b': 'Minum', 'opsi_c': 'Istirahat', 'opsi_d': 'Berlari',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Sinonim dari kata INTEGRITAS adalah?',
        'opsi_a': 'Kejujuran', 'opsi_b': 'Kepintaran', 'opsi_c': 'Keberanian', 'opsi_d': 'Kekuatan',
        'jawaban_benar': 'A',
    },
    {
        'pertanyaan': 'Antonim dari kata SOMBONG adalah?',
        'opsi_a': 'Angkuh', 'opsi_b': 'Takabur', 'opsi_c': 'Rendah hati', 'opsi_d': 'Bangga',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'PAGI : SIANG = MUDA : ?',
        'opsi_a': 'Kecil', 'opsi_b': 'Tua', 'opsi_c': 'Besar', 'opsi_d': 'Dewasa',
        'jawaban_benar': 'B',
    },
]

SOAL_NUMERIK = [
    {
        'pertanyaan': '15 × 8 − 40 = ?',
        'opsi_a': '80', 'opsi_b': '90', 'opsi_c': '100', 'opsi_d': '110',
        'jawaban_benar': 'A',
    },
    {
        'pertanyaan': 'Jika 3x + 9 = 24, maka x = ?',
        'opsi_a': '3', 'opsi_b': '5', 'opsi_c': '7', 'opsi_d': '9',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Berapa persen 45 dari 180?',
        'opsi_a': '20%', 'opsi_b': '25%', 'opsi_c': '30%', 'opsi_d': '35%',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': '√144 + √25 = ?',
        'opsi_a': '15', 'opsi_b': '17', 'opsi_c': '19', 'opsi_d': '21',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Sebuah barang harganya Rp 120.000 diskon 25%. Harga setelah diskon?',
        'opsi_a': 'Rp 80.000', 'opsi_b': 'Rp 85.000', 'opsi_c': 'Rp 90.000', 'opsi_d': 'Rp 95.000',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Rata-rata dari 12, 18, 24, 30 adalah?',
        'opsi_a': '18', 'opsi_b': '20', 'opsi_c': '21', 'opsi_d': '22',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': '(4² + 3²) × 2 = ?',
        'opsi_a': '40', 'opsi_b': '48', 'opsi_c': '50', 'opsi_d': '58',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Jika kecepatan mobil 80 km/jam, berapa km yang ditempuh dalam 2,5 jam?',
        'opsi_a': '160 km', 'opsi_b': '180 km', 'opsi_c': '200 km', 'opsi_d': '220 km',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': '1/4 + 2/3 = ?',
        'opsi_a': '3/7', 'opsi_b': '5/12', 'opsi_c': '11/12', 'opsi_d': '7/12',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Modal Rp 2.000.000 dengan bunga 15% per tahun. Bunga selama 8 bulan?',
        'opsi_a': 'Rp 180.000', 'opsi_b': 'Rp 200.000', 'opsi_c': 'Rp 240.000', 'opsi_d': 'Rp 160.000',
        'jawaban_benar': 'B',
    },
    {
        'pertanyaan': 'Deret: 5, 15, 45, 135, ... Angka berikutnya?',
        'opsi_a': '270', 'opsi_b': '375', 'opsi_c': '405', 'opsi_d': '315',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': '60% dari 250 adalah?',
        'opsi_a': '130', 'opsi_b': '140', 'opsi_c': '150', 'opsi_d': '160',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Sebuah pekerjaan diselesaikan 5 orang dalam 12 hari. Berapa hari jika dikerjakan 4 orang?',
        'opsi_a': '12 hari', 'opsi_b': '14 hari', 'opsi_c': '15 hari', 'opsi_d': '16 hari',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': '125 ÷ 0.5 = ?',
        'opsi_a': '62.5', 'opsi_b': '125', 'opsi_c': '250', 'opsi_d': '500',
        'jawaban_benar': 'C',
    },
    {
        'pertanyaan': 'Persentase kenaikan dari 200 menjadi 250 adalah?',
        'opsi_a': '20%', 'opsi_b': '25%', 'opsi_c': '30%', 'opsi_d': '50%',
        'jawaban_benar': 'B',
    },
]

# DISC: setiap set berisi 4 kata sifat, masing-masing mewakili dimensi D/I/S/C
# Kandidat memilih yang PALING dan KURANG mencerminkan diri mereka
SOAL_DISC = [
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Dominan', 'opsi_b': 'Berpengaruh', 'opsi_c': 'Stabil', 'opsi_d': 'Cermat',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Berani', 'opsi_b': 'Antusias', 'opsi_c': 'Sabar', 'opsi_d': 'Teliti',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Kompetitif', 'opsi_b': 'Optimis', 'opsi_c': 'Konsisten', 'opsi_d': 'Analitis',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Tegas', 'opsi_b': 'Persuasif', 'opsi_c': 'Dapat Diandalkan', 'opsi_d': 'Sistematis',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Langsung', 'opsi_b': 'Ramah', 'opsi_c': 'Tenang', 'opsi_d': 'Hati-hati',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Mandiri', 'opsi_b': 'Ekspresif', 'opsi_c': 'Loyal', 'opsi_d': 'Akurat',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Hasil-orientasi', 'opsi_b': 'Menginspirasi', 'opsi_c': 'Kooperatif', 'opsi_d': 'Perfeksionis',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Pemimpin', 'opsi_b': 'Sosial', 'opsi_c': 'Pengertian', 'opsi_d': 'Terstruktur',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Cepat bertindak', 'opsi_b': 'Spontan', 'opsi_c': 'Metodis', 'opsi_d': 'Berhati-hati',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Ambisius', 'opsi_b': 'Menyenangkan', 'opsi_c': 'Harmonis', 'opsi_d': 'Disiplin',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Menantang', 'opsi_b': 'Antusias berbagi', 'opsi_c': 'Setia', 'opsi_d': 'Kompeten',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
    {
        'pertanyaan': 'Pilih kata yang PALING mencerminkan Anda, dan yang PALING TIDAK mencerminkan Anda.',
        'opsi_a': 'Pionir', 'opsi_b': 'Motivator', 'opsi_c': 'Pendukung', 'opsi_d': 'Evaluator',
        'disc_a': 'D', 'disc_b': 'I', 'disc_c': 'S', 'disc_d': 'C',
    },
]

# Deskripsi profil DISC
DISC_DESKRIPSI = {
    'D': {
        'nama': 'Dominance — Pemimpin Berani',
        'deskripsi': (
            'Anda memiliki kepribadian Dominance yang kuat. Anda berorientasi pada hasil, '
            'menyukai tantangan, dan tidak takut mengambil keputusan sulit. '
            'Anda cenderung langsung, tegas, dan kompetitif. '
            'Kekuatan utama: kepemimpinan, ketegasan, dan orientasi pada tujuan. '
            'Area pengembangan: kesabaran, mendengarkan orang lain, dan empati.'
        ),
        'cocok_untuk': 'Manajer, Entrepreneur, Sales Leader, Project Manager',
    },
    'I': {
        'nama': 'Influence — Komunikator Inspiratif',
        'deskripsi': (
            'Anda memiliki kepribadian Influence yang menonjol. Anda antusias, optimis, '
            'dan sangat pandai membangun hubungan. Anda menyukai interaksi sosial dan '
            'mampu memotivasi orang-orang di sekitar Anda. '
            'Kekuatan utama: komunikasi, kreativitas, dan kemampuan mempengaruhi. '
            'Area pengembangan: fokus pada detail, konsistensi, dan manajemen waktu.'
        ),
        'cocok_untuk': 'Marketing, Public Relations, Sales, HR, Customer Service',
    },
    'S': {
        'nama': 'Steadiness — Pendukung yang Dapat Diandalkan',
        'deskripsi': (
            'Anda memiliki kepribadian Steadiness yang kuat. Anda sabar, konsisten, '
            'dan sangat dapat diandalkan. Anda bekerja baik dalam tim dan '
            'menghargai stabilitas serta harmoni di lingkungan kerja. '
            'Kekuatan utama: loyalitas, ketenangan di bawah tekanan, dan kerja tim. '
            'Area pengembangan: ketegasan, adaptasi terhadap perubahan, dan inisiatif.'
        ),
        'cocok_untuk': 'Support Staff, Administrator, Nurse, Teacher, Counselor',
    },
    'C': {
        'nama': 'Conscientiousness — Analis yang Teliti',
        'deskripsi': (
            'Anda memiliki kepribadian Conscientiousness yang dominan. Anda sangat teliti, '
            'analitis, dan berorientasi pada kualitas dan akurasi. Anda bekerja '
            'secara sistematis dan selalu memastikan pekerjaan sesuai standar tertinggi. '
            'Kekuatan utama: ketelitian, analisis mendalam, dan standar kualitas tinggi. '
            'Area pengembangan: fleksibilitas, kecepatan pengambilan keputusan, dan komunikasi.'
        ),
        'cocok_untuk': 'Akuntan, Quality Assurance, Data Analyst, Engineer, Programmer',
    },
}


def seed():
    """Isi database dengan soal-soal default."""
    from apps.psychotest.models import SoalBank

    created = 0

    # Cek apakah sudah ada soal
    if SoalBank.objects.exists():
        print("Soal sudah ada di database. Skip seeding.")
        return

    for i, soal in enumerate(SOAL_LOGIKA, 1):
        SoalBank.objects.create(
            kategori='logika', tipe='pilihan_ganda', urutan=i, **soal
        )
        created += 1

    for i, soal in enumerate(SOAL_VERBAL, 1):
        SoalBank.objects.create(
            kategori='verbal', tipe='pilihan_ganda', urutan=i, **soal
        )
        created += 1

    for i, soal in enumerate(SOAL_NUMERIK, 1):
        SoalBank.objects.create(
            kategori='numerik', tipe='pilihan_ganda', urutan=i, **soal
        )
        created += 1

    for i, soal in enumerate(SOAL_DISC, 1):
        SoalBank.objects.create(
            kategori='disc', tipe='disc_set', urutan=i, **soal
        )
        created += 1

    print(f"✅ Seeding selesai: {created} soal ditambahkan.")
    print(f"   Logika : {len(SOAL_LOGIKA)} soal")
    print(f"   Verbal : {len(SOAL_VERBAL)} soal")
    print(f"   Numerik: {len(SOAL_NUMERIK)} soal")
    print(f"   DISC   : {len(SOAL_DISC)} set")
