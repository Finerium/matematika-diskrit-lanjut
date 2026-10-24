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

Bagian kelompok dikerjakan bertiga. Nama anggota lain tidak ditulis di repo publik ini, cukup di laporan
kelompok yang disimpan lokal.

| Modul | Topik | Bagian individu | Bagian kelompok |
|---|---|---|---|
| [Modul 1](2026-09-15-modul-1/) | Pengenalan graf dan visualisasi dasar | Semua task, laporan 24 halaman | tidak ada |
| [Modul 2](2026-09-15-modul-2/) | Properti, representasi, dan isomorfisme graf | Task01-02, laporan 24 halaman | Task03-05, laporan 26 halaman |
| [Modul 3](2026-09-15-modul-3/) | Konektivitas graf | Task01, laporan 20 halaman | Task02-04, laporan 26 halaman |
| [Modul 4](2026-09-22-modul-4/) | Euler, Hamilton, dan Dijkstra | Task01-03, laporan 24 halaman | tidak ada |
| [Modul 5](2026-09-22-modul-5/) | Graph coloring | Task01, laporan 13 halaman | Task02-04, laporan 17 halaman |

Soal kelompok dibagi rata dan digilir, tiap anggota memegang satu soal di setiap modul. Bagian saya:
Modul 2 Task04 (full-mesh K6), Modul 3 Task02 (jaringan jalan Simpang Lima), dan Modul 5 Task04 (rute kurir dan
loker). Kode semua soal tetap ada di folder `_048` karena dikerjakan dan diuji bersama di sana.

Catatan pengerjaan:

- Modul 2 Task02 menganalisis graf semu G3 dari berkas `Task02_Individu.py` bawaan zip, ditambah
  K4, C5, dan W6 dari Task01 sebagai pembanding.
- Modul 3 Task01 menemukan circuit a-b-d-c-a di `Tutorial01.py` tidak valid karena sisi c-a tidak ada di graf.
- Modul 3 Task02 memodelkan Simpang Lima Bandung dari data OpenStreetMap, sedangkan Task03 memakai
  12 tokoh yang data pendidikannya dicek di Wikipedia bahasa Indonesia.
- Modul 4 Task01 menemukan graf "Euler Circuit" di `Tutorial01.py` sebenarnya hanya punya Euler path
  (B dan C berderajat 3), dan `nx.eulerian_circuit()` ternyata tersedia walaupun komentar tutorial bilang tidak.
- Modul 5 Task01 menunjukkan greedy coloring hanya batas atas: crown graph 8 simpul butuh 2 warna,
  tetapi greedy dengan urutan tertentu memakai 4.
- Modul 5 Task04 tidak memberi daftar jalan, jadi jaringan 6 area dirancang sendiri dengan tepat dua
  simpul ganjil supaya kasus Euler path bisa dibahas.

## Tugas besar graph

Kasus 4 Pasar Tumpah (Max Flow), dikerjakan berlima. Folder [`2026-10-19-tubes-kasus-04-pasar-tumpah/`](2026-10-19-tubes-kasus-04-pasar-tumpah/)
berisi starter kit dari dosen ([trisgelar/matdis-tubes-2026](https://github.com/trisgelar/matdis-tubes-2026)) yang
dilengkapi bagian max flow:

- skenario jaringan jalan nyata Gasibu - Monumen Perjuangan dari OpenStreetMap (18 node, 24 edge berarah,
  kapasitas skr/jam menurut PKJI 2014, tiga pintu masuk termasuk Flyover Pasupati dari arah Pasteur) dengan
  34 event perubahan kapasitas dari lapak buka sampai pasar bubar;
- baseline Edmonds-Karp dan Ford-Fulkerson DFS, SOTA Push-Relabel dan Dinic dinamis yang melanjutkan aliran lama
  saat kapasitas berubah;
- analisis subgraf bus dan truk (jalan arteri dan kolektor) dan sensitivitas tiap edge di `scripts/analisis_kasus4.py`;
- runner `scripts/run_maxflow.py`, benchmark `scripts/run_benchmark_maxflow.py` dan `scripts/run_benchmark_skala.py`
  (graf kisi sampai 402 node), dan `tests/test_maxflow.py` (83 tes lulus, hasil dicocokkan dengan networkx).

Hasil: max flow normal 5.055,1 skr/jam, saat puncak pasar 3.296,9 skr/jam (turun 34,8%), setelah usulan penataan
4.817,5 skr/jam. Min cut di Jl. Surapati sisi utara Gasibu dan Jl. Japati, sesuai pola lalu lintas biasanya di
Google Maps hari Minggu. Dinic dinamis paling cepat di semua benchmark. Penjelasan lengkap ada di
`kode/matdis-tubes-2026/KASUS_04_GASIBU.md`. Laporan, rencana kerja, aset presentasi (fishbone, peta, slide), dan
skrip pembuatnya disimpan lokal karena memuat kliping berita dan identitas kelompok.

## Struktur

Repo ini hanya berisi kode dan output program. Laporan `.docx` dan `.pdf`, dokumentasi `.txt`, arsip `.zip`, dan
salinan kode kelompok disimpan lokal karena memuat foto dan identitas anggota kelompok.

```
2026-09-15-modul-1/
  [MDL2026_2B_D4_2025]_Modul1_048/          kode Task01 dan Task02, hasil/ berisi gambar dan output
  [MDL2026_2B_D4_2025]_Modul1_048.pdf, .docx, .txt
  submission/                               arsip .zip untuk dikumpulkan

2026-09-15-modul-2/, 2026-09-15-modul-3/, 2026-09-22-modul-5/
  [MDL2026_2B_D4_2025]_ModulN_048/          semua kode yang dikerjakan (tempat kerja), hasil/
  [MDL2026_2B_D4_2025]_ModulN_048.*         laporan individu (foto sendiri, task individu saja)
  [MDL2026_2B_D4_2025]_ModulN_042_048_049/  salinan kode task kelompok, identitas diganti penanggung jawabnya
  [MDL2026_2B_D4_2025]_ModulN_042_048_049.* laporan kelompok (foto kelompok, task kelompok saja)
  submission/                               zip individu dan zip kelompok

2026-09-22-modul-4/
  [MDL2026_2B_D4_2025]_Modul4_048/          kode Task01 sampai Task03, hasil/
  [MDL2026_2B_D4_2025]_Modul4_048.pdf, .docx, .txt
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

Di Teams, modul dikumpulkan per bagian, masing-masing punya slot individu dan slot kelompok:

| Slot di Teams | Deadline | Berkas yang diunggah |
|---|---|---|
| Tugas 1 Kompilasi Graph Part 1 Individu | Senin 26 Okt 2026 23.59 | `Modul1_048.zip`, `Modul2_048.zip`, `Modul3_048.zip` |
| Tugas 1 Kompilasi Graph Part 1 Kelompok | Senin 26 Okt 2026 23.59 | `Modul2_042_048_049.zip`, `Modul3_042_048_049.zip` (oleh perwakilan kelompok) |
| Tugas 2 Kompilasi Graph Part 2 Individu | Kamis 29 Okt 2026 23.59 | `Modul4_048.zip`, `Modul5_048.zip` |
| Tugas 2 Kompilasi Graph Part 2 Kelompok | Kamis 29 Okt 2026 23.59 | `Modul5_042_048_049.zip` (oleh perwakilan kelompok) |

Semua nama arsip diawali `[MDL2026_2B_D4_2025]_` dan ada di folder `submission/` tiap modul. Instruksi slot
Part 2 Kelompok di Teams tertulis "hanya bagian Individu", kemungkinan salin tempel dari slot individu,
jadi yang diisi tetap bagian kelompok.

Tiap arsip berisi folder kode bernama sama dengan arsipnya, laporan `.pdf` dan `.docx`, serta `.txt` berisi
dokumentasi referensi dan tanya jawab selama pengerjaan. Contoh penamaan di modul masih `MDL2025` angkatan
2024, jadi yang dipakai pola nama arsip tahun ini.

Laporannya adalah berkas modul dari dosen yang diisi langsung, bukan dokumen baru: foto di kotak kanan atas
sampul, baris identitas, lalu kode, output, analisis, dan lesson learnt di bawah setiap task. Laporan individu
memakai foto sendiri dan identitas `048 - Nama - tanggal`. Laporan kelompok memakai foto kelompok, tiga identitas
anggota, tabel pembagian soal, penanggung jawab tiap soal, dan catatan lesson learnt dari anggota lain. Versi PDF
dibuat langsung dari docx tersebut dengan skrip Python (ReportLab).

## Catatan

Modul dari dosen disimpan di `materi/` dan tidak ikut di-commit karena hak ciptanya milik kampus.
