# Matematika Diskrit Lanjut

Sarjana Terapan Teknik Informatika, Jurusan Teknik Komputer dan Informatika,
Politeknik Negeri Bandung. Semester Ganjil 2026/2027.

- Nama  : Ghaisan Khoirul Badruzaman
- NIM   : 251524048
- Kelas : 2B-D4

Materinya teori graf. Teori memakai buku Rosen, *Discrete Mathematics and Its Applications*,
sedangkan praktikum mengerjakan graf dengan Python, NetworkX, dan Matplotlib.

## Jadwal

| Jenis | Waktu | Ruang | Dosen |
|---|---|---|---|
| Praktikum | Selasa 10.40 - 12.20 | D102 Lab. MT | Trisna Gelar, S.T., M.Kom. |
| Teori | Rabu 13.50 - 15.20 | D223 | Siti Dwi Setiarini, S.Si., M.T. |

## Progres praktikum

| Modul | Topik | Status |
|---|---|---|
| [Modul 1](2026-09-15-modul-1/) | Pengenalan graf dan visualisasi dasar | Selesai: latihan G1-G5 dan 6 graf tugas, laporan 12 halaman |
| [Modul 2](2026-09-15-modul-2/) | Properti, representasi, dan isomorfisme graf | Selesai: Task01-Task05, laporan 16 halaman |

Menurut info kelas, pengumpulan dua modul ini tidak wajib. Modul 2 dikerjakan dari berkas
modul versi 2025, jadi soalnya bisa berubah kalau dosen membagikan versi terbaru.

## Struktur

```
2026-09-15-modul-1/
  [MDL2026_2B_D4_2025]_Modul1_048/   kode Task01 dan Task02
    hasil/                           gambar graf dan output program
  [MDL2026_2B_D4_2025]_Modul1_048.pdf, .docx, .txt
  submission/                        arsip .zip untuk dikumpulkan

2026-09-15-modul-2/
  [MDL2026_2B_D4_2025]_Modul2_048/   kode Task01 sampai Task05
    hasil/
  [MDL2026_2B_D4_2025]_Modul2_048.pdf, .docx, .txt
  submission/
```

## Menjalankan

```
pip install networkx matplotlib numpy scipy
cd "2026-09-15-modul-1/[MDL2026_2B_D4_2025]_Modul1_048"
python3 "Task02_Hello Networkx.py"
```

Modul menyarankan Thonny, tapi berkasnya juga bisa dijalankan dari terminal atau IDE lain.
Gambar graf ikut disimpan ke folder `hasil/` di samping berkas kode.
Diuji dengan Python 3.14.6, NetworkX 3.6.1, dan Matplotlib 3.10.8.

## Pengumpulan

Satu arsip `[MDL2026_2B_D4_2025]_Modul<N>_048.zip` berisi folder kode bernama sama, laporan
`.pdf` dan `.docx`, serta `.txt` berisi dokumentasi referensi dan tanya jawab selama pengerjaan.
Contoh penamaan di modul masih `MDL2025` angkatan 2024, jadi yang dipakai pola nama arsip tahun ini.

## Catatan

Modul dari dosen disimpan di `materi/` dan tidak ikut di-commit karena hak ciptanya milik kampus.
