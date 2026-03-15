# 📖 HRIS SmartDesk — Manual Pengguna

> Panduan lengkap penggunaan sistem HRIS SmartDesk.
> Ditulis untuk pengguna umum — tidak perlu latar belakang IT.

---

## 🗂️ DAFTAR ISI

1. [Login & Akses](#1-login--akses)
2. [Dashboard](#2-dashboard)
3. [Database Karyawan](#3-database-karyawan)
4. [Absensi & Kehadiran](#4-absensi--kehadiran)
5. [Cuti](#5-cuti)
6. [Lembur](#6-lembur)
7. [Kontrak Kerja](#7-kontrak-kerja)
8. [Penggajian (Payroll)](#8-penggajian-payroll)
9. [Hubungan Industrial](#9-hubungan-industrial)
10. [Rekrutmen](#10-rekrutmen)
11. [Psikotes & Tes Lanjutan](#11-psikotes--tes-lanjutan)
12. [Laporan](#12-laporan)
13. [Shift & Jadwal Kerja](#13-shift--jadwal-kerja)
14. [Organisasi & Pengembangan (OD)](#14-organisasi--pengembangan-od)
15. [Penilaian Kinerja (Performance)](#15-penilaian-kinerja-performance)
16. [Manajemen Aset](#16-manajemen-aset)
17. [Portal Karyawan (Mandiri)](#17-portal-karyawan-mandiri)
18. [Pengaturan Sistem](#18-pengaturan-sistem)

---

## 1. Login & Akses

### Cara Masuk ke Sistem
1. Buka browser, ketik alamat sistem HRIS Anda
2. Klik tombol **Masuk** di halaman awal
3. Isi **Username** dan **Password**
4. Klik **Login**

### Lupa Password
1. Di halaman login, klik **Lupa Password**
2. Masukkan alamat email yang terdaftar
3. Cek email masuk, klik link reset password
4. Buat password baru

### Level Akses Pengguna
| Level | Bisa Apa |
|---|---|
| **Administrator / HR** | Akses penuh ke semua menu |
| **Manager** | Melihat data tim, approve cuti & lembur |
| **Karyawan** | Hanya Portal Karyawan (mandiri) |

---

## 2. Dashboard

Halaman pertama setelah login. Menampilkan:
- **Ringkasan karyawan** — total aktif, kontrak habis, masa probasi
- **Notifikasi penting** — kontrak mau habis, peringatan probasi
- **Grafik kehadiran** bulan berjalan

---

## 3. Database Karyawan

Menu: **Karyawan**

### Melihat Daftar Karyawan
- Buka menu **Karyawan**
- Gunakan kolom pencarian untuk cari nama atau NIK
- Klik nama karyawan untuk lihat detail lengkap

### Tambah Karyawan Baru
1. Klik tombol **+ Tambah Karyawan**
2. Isi form data karyawan (nama, NIK, jabatan, departemen, dll.)
3. Klik **Simpan**

### Edit Data Karyawan
1. Klik nama karyawan yang ingin diedit
2. Klik tombol **Edit**
3. Ubah data yang perlu diperbarui
4. Klik **Simpan**

### Import Karyawan Massal (dari Excel)
Berguna saat pertama kali setup atau tambah banyak karyawan sekaligus.
1. Klik **Import**
2. Download dulu **Template Excel** sebagai panduan format
3. Isi template Excel dengan data karyawan
4. Upload file Excel tersebut
5. Sistem akan otomatis mencocokkan data wilayah dan bank

### Export Daftar Karyawan
1. Klik **Export**
2. File Excel akan terunduh otomatis

### Atur Gaji Karyawan
1. Buka detail karyawan
2. Klik tab atau tombol **Gaji**
3. Isi komponen gaji: gaji pokok, tunjangan tetap, dll.
4. Klik **Simpan**

### Nonaktifkan Karyawan (Resign/PHK)
1. Buka detail karyawan
2. Klik **Nonaktifkan**
3. Isi tanggal keluar dan alasan
4. Klik **Konfirmasi**

### Job Library (Daftar Jabatan)
Menu: **Job Library** di sidebar

Tempat mendaftarkan semua jabatan yang ada di perusahaan beserta deskripsi, persyaratan, dan level jabatan.

1. Klik **+ Tambah Jabatan**
2. Isi nama jabatan, deskripsi, dan persyaratan
3. Klik **Simpan**

---

## 4. Absensi & Kehadiran

Menu: **Absensi**

### Melihat Rekap Absensi
- Pilih **bulan** dan **tahun** yang ingin dilihat
- Tabel menampilkan daftar karyawan beserta kehadiran, terlambat, izin, dan lembur

### Input Absensi Manual (Check-in/out)
Untuk HR yang input manual (bukan dari mesin fingerprint):
1. Buka menu **Absensi**
2. Klik **Check-in Manual**
3. Pilih karyawan, isi jam masuk dan jam keluar
4. Klik **Simpan**

### Input Absensi Massal
Untuk input kehadiran banyak karyawan dalam satu hari sekaligus:
1. Klik **Input Massal**
2. Pilih tanggal
3. Centang karyawan yang hadir, isi status masing-masing
4. Klik **Simpan Semua**

### Import Absensi dari Mesin Fingerprint
1. Export data dari mesin fingerprint ke file Excel/CSV
2. Di menu Absensi, klik **Import**
3. Download **Template Import** untuk lihat format yang dibutuhkan
4. Upload file dari mesin fingerprint
5. Sistem akan memproses dan mencocokkan data

### Laporan Absensi
1. Klik **Laporan**
2. Pilih rentang tanggal dan filter departemen
3. Lihat rekap lengkap atau klik **Export Excel**

### Kalender Kehadiran
Tampilan kalender bulanan untuk melihat pola kehadiran. Klik menu **Kalender**.

---

## 5. Cuti

Menu: **Absensi → Cuti**

### Pengajuan Cuti (oleh HR)
1. Klik **+ Ajukan Cuti**
2. Pilih karyawan dan jenis cuti (tahunan, sakit, melahirkan, dll.)
3. Isi tanggal mulai dan tanggal selesai
4. Upload dokumen pendukung jika ada (misal surat dokter)
5. Klik **Kirim**

### Menyetujui Cuti
1. Buka menu **Cuti**
2. Cari pengajuan dengan status **Menunggu Persetujuan**
3. Klik nama karyawan untuk buka detail
4. Klik **Setujui** atau **Tolak** dengan mengisi alasan

### Melihat Detail Cuti
Klik nama karyawan di daftar cuti untuk lihat informasi lengkap termasuk riwayat persetujuan.

---

## 6. Lembur

Menu: **Absensi → Lembur**

### Melihat Daftar Lembur
Daftar semua pengajuan lembur karyawan beserta status persetujuan.

### Input Lembur Manual
1. Klik **+ Tambah Lembur**
2. Pilih karyawan dan tanggal
3. Isi jumlah jam lembur dan keterangan
4. Sistem otomatis menghitung upah lembur berdasarkan gaji karyawan
5. Klik **Simpan**

### Hitung Ulang Lembur
Jika ada perubahan gaji yang mempengaruhi tarif lembur:
1. Klik **Hitung Ulang**
2. Sistem akan recalculate semua upah lembur yang belum diproses payroll

### Setujui / Tolak Lembur
Sama seperti proses cuti — cari pengajuan, klik **Setujui** atau **Tolak**.

---

## 7. Kontrak Kerja

Menu: **Kontrak**

### Melihat Daftar Kontrak
Semua kontrak karyawan aktif beserta tanggal mulai, berakhir, dan statusnya.

### Tambah Kontrak Baru
1. Klik **+ Tambah Kontrak**
2. Pilih karyawan
3. Pilih jenis kontrak: **PKWT** (kontrak waktu tertentu), **PKWTT** (tetap), atau **PHL** (harian lepas)
4. Isi tanggal mulai dan berakhir
5. Klik **Simpan**

### Perpanjang Kontrak
1. Buka detail kontrak yang akan diperpanjang
2. Klik **Perpanjang**
3. Isi tanggal berakhir yang baru
4. Klik **Simpan**

### Print Kontrak
1. Buka detail kontrak
2. Pilih format: **PKWT**, **PKWTT**, atau **PHL**
3. Klik **Cetak** — dokumen siap print

### Kontrak Hampir Habis
1. Klik menu **Hampir Habis**
2. Sistem menampilkan daftar kontrak yang akan berakhir dalam 30 hari ke depan

---

## 8. Penggajian (Payroll)

Menu: **Payroll**

### Atur Gaji Karyawan
Menu: **Payroll → Data Gaji**
1. Klik **+ Tambah** atau cari karyawan yang ingin diatur gajinya
2. Isi komponen: gaji pokok, tunjangan jabatan, tunjangan makan, BPJS, dll.
3. Klik **Simpan**

### Generate Slip Gaji Bulanan
1. Klik **Generate Payroll**
2. Pilih **bulan** dan **tahun**
3. Klik **Generate** — sistem otomatis menghitung gaji semua karyawan termasuk lembur dan potongan
4. Lihat rekap total per komponen

### Melihat Slip Gaji Individual
1. Dari hasil generate, klik nama karyawan
2. Slip gaji detail tampil lengkap dengan semua komponen
3. Klik **Cetak Slip** untuk print

### Export Payroll ke Excel
1. Setelah generate, klik **Export Excel**
2. File Excel berisi semua data gaji bulan tersebut

### Tunjangan Site (untuk Perusahaan Multi-Lokasi)
Menu: **Payroll → Site Allowance**

Untuk perusahaan yang punya beberapa lokasi/site kerja dengan tunjangan berbeda-beda:
1. Klik **+ Tambah Aturan**
2. Pilih lokasi (Job Site) dan jabatan yang berlaku
3. Isi nominal tunjangan (flat Rp atau persentase dari gaji)
4. Aktifkan aturan
5. Saat generate payroll, tunjangan ini otomatis terhitung

### Ringkasan Per Site
Menu: **Payroll → Ringkasan Site** — melihat total pengeluaran gaji per lokasi kerja.

### Import Data Gaji Massal
1. Klik **Import**
2. Download **Template Excel**
3. Isi template lalu upload

---

## 9. Hubungan Industrial

Menu: **Industrial**

### Surat Peringatan (SP)

#### Membuat SP
1. Klik **SP → Buat SP**
2. Pilih karyawan
3. Pilih tingkat SP (SP1, SP2, SP3) — sistem otomatis menyarankan berdasarkan riwayat pelanggaran
4. Isi kronologi pelanggaran dan pasal yang dilanggar
5. Klik **Simpan**

#### Cetak SP
1. Buka detail SP
2. Klik **Cetak** — dokumen SP siap ditandatangani

### Pelanggaran

#### Catat Pelanggaran
1. Klik **Pelanggaran → + Tambah**
2. Pilih karyawan dan jenis pelanggaran
3. Isi tanggal dan kronologi
4. Klik **Simpan**

### Pesangon & PHK

#### Kalkulator Pesangon
1. Klik **Pesangon → Kalkulator**
2. Pilih karyawan
3. Pilih alasan PHK (resign, efisiensi, pensiun, dll.)
4. Sistem otomatis menghitung pesangon sesuai PP 35/2021:
   - Uang pesangon
   - Uang penghargaan masa kerja
   - Uang penggantian hak
5. Klik **Simpan** untuk membuat dokumen pesangon resmi

#### Surat PHK
1. Klik **Surat PHK → Buat**
2. Pilih karyawan (data pesangon otomatis ter-link)
3. Isi detail tanggal efektif PHK
4. Klik **Simpan** lalu **Cetak**

#### Perjanjian Bersama (PB)
Dokumen kesepakatan antara perusahaan dan karyawan saat PHK:
1. Klik **Perjanjian Bersama → Buat**
2. Pilih karyawan dan link ke data pesangon
3. Edit isi perjanjian jika perlu
4. Klik **Simpan** lalu **Cetak**

### Surat Keterangan Kerja
Dibuat secara otomatis dari data karyawan:
1. Buka detail karyawan
2. Klik **Surat Keterangan Kerja**
3. Cetak langsung

---

## 10. Rekrutmen

Menu: **Rekrutmen**

### Alur Rekrutmen Standar
```
Buat MPR → Tambah Kandidat → Proses Seleksi → Buat Offering Letter → Hired
```

### Manpower Request (MPR)
Permintaan kebutuhan karyawan baru dari departemen:
1. Klik **MPR → + Buat MPR**
2. Pilih departemen, jabatan, dan jumlah yang dibutuhkan
3. Isi alasan kebutuhan
4. Klik **Simpan** → Manager menyetujui

### Kelola Kandidat

#### Tambah Kandidat
1. Klik **Kandidat → + Tambah**
2. Isi data: nama, email, nomor HP, jabatan yang dilamar, link ke MPR (opsional)
3. Upload CV (opsional)
4. Klik **Simpan**

#### Update Status Kandidat
Alur status: `Screening → Psikotes → Interview HR → Interview User → Medical Check → Offering → Hired / Rejected`

1. Buka detail kandidat
2. Klik **Update Status**
3. Pilih status baru dan isi catatan
4. Klik **Simpan**

#### Cetak Profil Kandidat
1. Buka detail kandidat
2. Klik **Cetak** — dokumen profil kandidat siap untuk arsip

### ATS — Scan CV Otomatis
Fitur AI untuk mencocokkan CV dengan kebutuhan jabatan:
1. Klik **ATS Scan**
2. Upload file CV kandidat (PDF)
3. Isi jabatan dan kriteria yang dibutuhkan
4. Klik **Analisis** — sistem memberi skor dan rekomendasi
5. Jika cocok, klik **Simpan sebagai Kandidat**

### Offering Letter (Surat Penawaran Kerja)

#### Buat Template Offering
Buat template surat yang bisa dipakai berulang:
1. Klik **Template Offering → + Tambah**
2. Beri nama template dan tulis isi surat
3. Klik **Simpan**

#### Buat Offering Letter
1. Klik **Offering → + Buat**
2. Pilih kandidat dan template surat
3. Isi detail gaji dan tunjangan yang ditawarkan
4. Klik **Simpan**
5. Klik **Cetak** untuk print surat resmi

#### Update Status Offering
Setelah kandidat memberi keputusan:
1. Buka detail offering
2. Klik **Update Status**: Diterima / Ditolak / Negosiasi

### Pengaturan Rekrutmen
Menu: **Rekrutmen → Pengaturan Perusahaan** — atur logo dan informasi perusahaan yang muncul di dokumen rekrutmen.

---

## 11. Psikotes & Tes Lanjutan

Menu: **Psikotes** dan **Tes Lanjutan**

### Psikotes Dasar

#### Kelola Bank Soal
1. Klik **Soal → + Tambah Soal**
2. Pilih tipe soal (pilihan ganda, skala, gambar)
3. Isi pertanyaan dan pilihan jawaban
4. Klik **Simpan**

#### Buat Sesi Psikotes
1. Klik **Sesi → Buat Sesi** untuk kandidat tertentu
2. Sistem menghasilkan **link unik** untuk kandidat
3. Kirim link ke kandidat
4. Kandidat mengerjakan tes secara mandiri via browser

#### Lihat Hasil Psikotes
1. Klik nama sesi yang sudah selesai
2. Lihat rekap jawaban dan skor

### Tes Lanjutan (Advanced — OCEAN Big Five)
Tes kepribadian komprehensif berbasis model psikologi Big Five:

#### Buat Sesi Tes
Bisa untuk **kandidat** (rekrutmen) atau **karyawan** (pengembangan):
1. Klik **Kandidat → Buat Tes** atau **Karyawan → Buat Tes**
2. Pilih kandidat/karyawan
3. Sistem menghasilkan link tes
4. Kirim link ke peserta

#### Lihat & Cetak Hasil
1. Buka sesi yang selesai
2. Laporan OCEAN otomatis terhitung (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
3. Klik **Cetak** untuk laporan resmi

#### Export Semua Hasil
Klik **Export Excel** untuk mengunduh semua hasil tes dalam satu file.

#### Laporan Ringkasan
Klik **Laporan** untuk melihat perbandingan hasil semua peserta.

---

## 12. Laporan

Menu: **Laporan**

Semua laporan bisa dilihat di layar dan diexport ke Excel.

| Laporan | Isi |
|---|---|
| **Laporan Absensi** | Rekap kehadiran, terlambat, izin per karyawan |
| **Laporan Payroll** | Ringkasan gaji bulanan semua karyawan |
| **Laporan Karyawan** | Data master karyawan aktif |
| **Laporan Kontrak** | Status kontrak semua karyawan |
| **Laporan Pelanggaran** | Riwayat SP dan pelanggaran |
| **Laporan Rekrutmen** | Statistik proses rekrutmen dan status kandidat |

### Cara Export ke Excel
1. Buka laporan yang diinginkan
2. Atur filter (tanggal, departemen, dll.) jika tersedia
3. Klik **Export Excel**

---

## 13. Shift & Jadwal Kerja

Menu: **Shift**

### Buat Shift Kerja
1. Klik **Shift → + Tambah Shift**
2. Isi nama shift (misal "Shift Pagi"), jam masuk, jam keluar
3. Klik **Simpan**

### Assign Shift ke Karyawan
1. Klik **Assignment → + Tambah**
2. Pilih karyawan dan shift yang berlaku
3. Tentukan tanggal mulai berlaku
4. Klik **Simpan**

### Jadwal Roster (Bulanan)
Tampilan kalender untuk mengatur jadwal shift massal:
1. Klik **Roster**
2. Pilih bulan
3. Klik sel di pertemuan karyawan dan tanggal
4. Pilih shift atau hari libur
5. Gunakan **Isi Massal** untuk mengisi banyak sel sekaligus

### Shift Siklus (Rotating)
Untuk shift yang berputar otomatis (misal ABCABC):
1. Klik **Siklus Shift → + Buat Siklus**
2. Definisikan urutan shift dalam satu siklus
3. Assign ke karyawan dengan tanggal mulai
4. Sistem otomatis menjadwalkan berdasarkan siklus

---

## 14. Organisasi & Pengembangan (OD)

Menu: **OD** *(Add-On — perlu aktivasi)*

### Workload Standard
Standar beban kerja per jabatan:
1. Klik **Workload → + Tambah**
2. Pilih jabatan dan isi volume kerja standar per hari/bulan
3. Klik **Simpan**

### FTE (Full-Time Equivalent) Planning
Menghitung kebutuhan jumlah karyawan berdasarkan beban kerja:
1. Klik **FTE Standard → + Tambah**
2. Isi data jam kerja efektif dan volume pekerjaan
3. Lihat hasil di **FTE Planning** — sistem otomatis menampilkan apakah departemen kekurangan atau kelebihan karyawan

### Kompetensi Jabatan

#### Tambah Kompetensi
1. Klik **Kompetensi → + Tambah**
2. Isi kode, nama kompetensi, dan deskripsi tiap level (L1–L5)
3. Klik **Simpan**

#### Standar Kompetensi Per Jabatan
1. Klik **Kompetensi → Jabatan**
2. Pilih jabatan
3. Isi level minimum yang dibutuhkan untuk setiap kompetensi
4. Tentukan apakah kompetensi tersebut **wajib** atau tidak

#### Penilaian Kompetensi Karyawan
1. Klik **Kompetensi → Nilai Karyawan**
2. Pilih karyawan dan periode
3. Isi level aktual setiap kompetensi
4. Klik **Simpan**

#### Competency Matrix
Tampilan tabel besar: karyawan vs kompetensi.
- **Hijau** = memenuhi standar
- **Merah** = gap (di bawah standar)
- **Abu-abu** = belum dinilai

#### Gap Report
Laporan prioritas pengembangan — menampilkan karyawan dengan gap kompetensi terbesar yang perlu pelatihan.

### Org Chart
Struktur organisasi visual perusahaan:
1. Klik **Org Chart → Buat**
2. Sistem otomatis membangun chart dari data jabatan dan karyawan
3. Aktifkan chart untuk ditampilkan
4. Lihat tampilan visual hierarki organisasi

---

## 15. Penilaian Kinerja (Performance)

Menu: **Performance** *(terintegrasi dengan OD)*

### Alur Penilaian
```
Buat Periode → Buat Template KPI → Buat Penilaian → Input KPI → Review Atasan
```

### Periode Penilaian
1. Klik **Periode → + Tambah**
2. Isi nama periode (misal "Semester 1 2025"), tanggal mulai dan selesai
3. Klik **Simpan**

### Template KPI
Buat template KPI yang bisa dipakai berulang untuk jabatan tertentu:
1. Klik **Template → + Tambah**
2. Isi nama template dan item-item KPI default
3. Klik **Simpan**

### Buat Penilaian Karyawan
1. Klik **Penilaian → + Buat**
2. Pilih karyawan dan periode
3. Opsional: pilih template KPI sebagai titik awal
4. Klik **Simpan**

### Input KPI
1. Buka penilaian karyawan
2. Klik **Input KPI**
3. Isi target dan realisasi setiap item KPI
4. Klik **Simpan**

### Review Atasan
Setelah karyawan atau HR input KPI:
1. Buka penilaian
2. Klik **Review Atasan**
3. Atasan mengisi penilaian kualitatif dan skor final
4. Klik **Simpan**

### Ranking Kinerja
Klik **Ranking** untuk melihat perbandingan skor kinerja semua karyawan dalam satu periode.

---

## 16. Manajemen Aset

Menu: **Aset** *(Add-On)*

### Struktur Modul Aset
```
Kategori → Aset → Lokasi → Vendor → Pergerakan → Perawatan → Audit → Laporan
```

### Kategori Aset
1. Klik **Kategori → + Buat**
2. Isi nama kategori (misal "Kendaraan", "IT Equipment")
3. Bisa dibuat hierarki: kategori → subkategori
4. Klik **Simpan**

### Daftar Aset
1. Klik **Aset → + Tambah**
2. Isi: nama aset, kode, kategori, lokasi, vendor, tanggal beli, nilai beli
3. Klik **Simpan**

### Lokasi Aset
Daftarkan semua lokasi fisik aset (kantor, gudang, cabang, dll.):
1. Klik **Lokasi → + Tambah**
2. Isi nama dan detail lokasi
3. Bisa dibuat hierarki lokasi

### Vendor / Supplier
1. Klik **Vendor → + Tambah**
2. Isi nama, kontak, dan informasi vendor
3. Klik **Simpan**

### Pergerakan Aset (Mutasi)
Catat perpindahan aset dari satu lokasi/pengguna ke lain:
1. Klik **Pergerakan → + Buat**
2. Pilih aset, dari mana, ke mana, dan siapa PIC-nya
3. Klik **Simpan**

### Lihat Assignment (Aset Siapa)
Klik **Pergerakan → Assignment** untuk melihat siapa yang memegang aset apa saat ini.

### Perawatan (Maintenance)
Catat jadwal dan riwayat perawatan aset:
1. Klik **Perawatan → + Tambah**
2. Pilih aset, isi tanggal, jenis perawatan, dan biaya
3. Klik **Simpan**

### Audit Aset
Proses pencocokan fisik aset dengan data sistem:
1. Klik **Audit**
2. Jalankan audit — tandai aset yang sudah dicek fisik
3. Lihat statistik: aset ditemukan, tidak ditemukan, kondisi

### Laporan Aset
Menu: **Laporan Aset**
- **Kartu Aset** — detail riwayat satu aset, bisa dicetak
- **PIC Beban** — laporan aset per penanggung jawab
- **Stock Opname** — laporan hasil pengecekan fisik
- **Depresiasi** — laporan penyusutan nilai aset
- **Laporan Perawatan** — riwayat semua perawatan

---

## 17. Portal Karyawan (Mandiri)

Alamat: `[alamat-sistem]/karyawan/login`

Portal khusus untuk karyawan — akses sendiri tanpa perlu akun HR.

### Cara Login Karyawan
1. Buka alamat portal karyawan
2. Isi **NIK** dan **Tanggal Lahir** sebagai password
3. Klik **Masuk**

> Catatan: Akun portal dibuat oleh HR. Karyawan tidak bisa buat akun sendiri.

### Fitur Portal Karyawan

#### Check-in / Check-out
1. Di dashboard portal, klik **Check-in**
2. Sistem mencatat lokasi GPS dan perangkat
3. Saat pulang, klik **Check-out**

> Fitur anti-fraud: sistem mendeteksi lokasi GPS dan identitas perangkat untuk mencegah titip absen.

#### Pengajuan Cuti
1. Klik menu **Cuti**
2. Klik **+ Ajukan Cuti**
3. Pilih jenis cuti, isi tanggal, alasan, dan upload dokumen jika perlu
4. Klik **Kirim** — pengajuan masuk ke HR/Manager untuk disetujui
5. Lihat status persetujuan di halaman yang sama

#### Lihat Slip Gaji
1. Klik menu **Slip Gaji**
2. Pilih bulan/tahun
3. Slip gaji tampil lengkap dengan semua komponen

#### Jadwal Kerja
Klik menu **Jadwal** untuk melihat shift dan jadwal kerja bulan ini.

#### Riwayat Absensi
Klik menu **Riwayat** untuk melihat catatan kehadiran pribadi.

#### Edit Profil
1. Klik menu **Profil**
2. Update data pribadi yang diizinkan (nomor HP, alamat, kontak darurat, dll.)
3. Klik **Simpan** — perubahan dicatat dan menunggu verifikasi HR

### Portal Offline (PWA)
Portal bisa digunakan walau **koneksi internet terputus**:
- Check-in/out tersimpan sementara di perangkat
- Saat internet kembali, data otomatis tersinkronisasi ke server

### Tambah / Atur Akun Portal Karyawan (oleh HR)
Menu: **Karyawan → Akun Portal**

1. Klik **Buat Akun Massal** untuk buat semua sekaligus
2. Atau klik per karyawan → **Atur Akun** untuk atur individual
3. Klik tab **Log Biodata** untuk lihat riwayat perubahan data yang diajukan karyawan

---

## 18. Pengaturan Sistem

### Approval Matrix (Rantai Persetujuan)
Menu: **Pengaturan → Approval Matrix**

Mengatur siapa yang menyetujui pengajuan cuti, lembur, dan proses HR lainnya:
1. Klik **+ Tambah Aturan**
2. Pilih modul (Cuti, Lembur, dll.) dan jabatan pemohon
3. Atur urutan approver (step 1, step 2, dst.)
4. Klik **Simpan**

### Org Chart
Menu: **Pengaturan → Org Chart**

1. Klik **Buat Org Chart**
2. Sistem otomatis mengambil data dari jabatan dan karyawan aktif
3. Klik **Aktifkan** agar bisa dilihat seluruh tim

### Ganti Password
1. Klik nama pengguna di pojok kanan atas
2. Klik **Ganti Password**
3. Isi password lama dan password baru
4. Klik **Simpan**

### Profil Pengguna
1. Klik **Profil** di menu kanan atas
2. Update nama, email, dan foto profil
3. Klik **Simpan**

---

## ✅ CHECKLIST SEMUA FUNGSI SISTEM

### 🧑‍💼 Karyawan & Organisasi
- [ ] Tambah karyawan baru
- [ ] Edit data karyawan
- [ ] Import karyawan massal (Excel)
- [ ] Export daftar karyawan
- [ ] Nonaktifkan karyawan
- [ ] Atur gaji karyawan
- [ ] Kelola Job Library (jabatan)
- [ ] Buat & kelola akun portal karyawan
- [ ] Buat akun portal massal
- [ ] Lihat log perubahan biodata karyawan

### 📅 Absensi & Waktu
- [ ] Lihat rekap absensi bulanan
- [ ] Input check-in/out manual
- [ ] Input absensi massal
- [ ] Import absensi dari fingerprint
- [ ] Lihat kalender kehadiran
- [ ] Export laporan absensi

### 🏖️ Cuti
- [ ] Ajukan cuti (oleh HR)
- [ ] Setujui cuti
- [ ] Tolak cuti
- [ ] Lihat detail & riwayat persetujuan cuti

### ⏰ Lembur
- [ ] Input lembur manual
- [ ] Setujui / tolak lembur
- [ ] Hitung ulang upah lembur
- [ ] Lihat daftar lembur

### 📄 Kontrak
- [ ] Tambah kontrak baru (PKWT/PKWTT/PHL)
- [ ] Perpanjang kontrak
- [ ] Cetak kontrak
- [ ] Hapus kontrak
- [ ] Lihat kontrak hampir habis

### 💰 Payroll
- [ ] Atur data gaji karyawan
- [ ] Import gaji massal
- [ ] Generate payroll bulanan
- [ ] Lihat & cetak slip gaji
- [ ] Export payroll ke Excel
- [ ] Kelola Site Allowance (tunjangan lokasi)
- [ ] Lihat ringkasan payroll per site

### ⚖️ Hubungan Industrial
- [ ] Catat pelanggaran
- [ ] Buat & cetak Surat Peringatan (SP1/SP2/SP3)
- [ ] Hitung pesangon (PP 35/2021)
- [ ] Buat & cetak Surat PHK
- [ ] Buat & cetak Perjanjian Bersama
- [ ] Cetak Surat Keterangan Kerja

### 🔍 Rekrutmen
- [ ] Buat Manpower Request (MPR)
- [ ] Setujui MPR
- [ ] Tambah kandidat
- [ ] Update status kandidat
- [ ] Cetak profil kandidat
- [ ] Scan CV dengan ATS (AI)
- [ ] Buat template Offering Letter
- [ ] Buat & cetak Offering Letter
- [ ] Update status offering
- [ ] Atur pengaturan perusahaan rekrutmen

### 🧠 Psikotes
- [ ] Kelola bank soal
- [ ] Buat sesi psikotes untuk kandidat
- [ ] Lihat hasil psikotes
- [ ] Buat sesi tes OCEAN (kandidat)
- [ ] Buat sesi tes OCEAN (karyawan)
- [ ] Lihat & cetak laporan OCEAN
- [ ] Export semua hasil tes

### 📊 Laporan
- [ ] Laporan absensi (+ export)
- [ ] Laporan payroll (+ export)
- [ ] Laporan karyawan (+ export)
- [ ] Laporan kontrak (+ export)
- [ ] Laporan pelanggaran (+ export)
- [ ] Laporan rekrutmen (+ export)

### 🕐 Shift & Roster
- [ ] Buat shift kerja
- [ ] Assign shift ke karyawan
- [ ] Atur roster bulanan
- [ ] Isi roster massal
- [ ] Buat siklus shift (rotating)
- [ ] Assign siklus ke karyawan

### 🏢 OD & Kompetensi *(Add-On)*
- [ ] Tambah workload standard
- [ ] Tambah FTE standard
- [ ] Lihat FTE planning
- [ ] Tambah kompetensi
- [ ] Atur standar kompetensi per jabatan
- [ ] Nilai kompetensi karyawan
- [ ] Lihat competency matrix
- [ ] Lihat gap report
- [ ] Buat & aktifkan org chart

### 🎯 Penilaian Kinerja *(Add-On)*
- [ ] Buat periode penilaian
- [ ] Buat template KPI
- [ ] Buat penilaian karyawan
- [ ] Input KPI (target & realisasi)
- [ ] Review atasan
- [ ] Lihat ranking kinerja

### 📦 Manajemen Aset *(Add-On)*
- [ ] Tambah kategori aset
- [ ] Tambah aset
- [ ] Tambah lokasi
- [ ] Tambah vendor
- [ ] Catat pergerakan aset
- [ ] Lihat assignment aset
- [ ] Catat perawatan
- [ ] Jalankan audit aset
- [ ] Lihat statistik audit
- [ ] Cetak kartu aset
- [ ] Laporan PIC beban
- [ ] Laporan stock opname
- [ ] Laporan depresiasi
- [ ] Laporan perawatan

### 📱 Portal Karyawan (Mandiri)
- [ ] Login portal (NIK + tanggal lahir)
- [ ] Check-in / check-out
- [ ] Lihat slip gaji
- [ ] Ajukan cuti
- [ ] Lihat status cuti
- [ ] Lihat jadwal kerja
- [ ] Lihat riwayat absensi
- [ ] Edit profil
- [ ] Check-in offline (PWA)
- [ ] Auto-sync saat online kembali

### ⚙️ Pengaturan
- [ ] Atur approval matrix
- [ ] Buat org chart
- [ ] Ganti password
- [ ] Edit profil pengguna
- [ ] Reset password via email

---

*HRIS SmartDesk v1.0 — Dokumen ini berlaku untuk versi terkini sistem.*
