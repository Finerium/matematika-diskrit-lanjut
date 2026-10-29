# Hitung Kendaraan dari Video (YOLO)

Bagian tubes Kasus 4 (pasar tumpah Gasibu) untuk mengukur arus kendaraan nyata di node graf. Masukannya rekaman
CCTV Pemkot Bandung (pelindung.bandung.go.id) atau video HP. Keluarannya jumlah kendaraan yang melewati garis hitung,
dipisah per jenis (SM, KR, KB, KTB), per arah, dan per edge graf, lalu direkap jadi kend/jam dan skr/jam per
interval.

Titik dan edge mengikuti graf kelompok terbaru: source S1 (turun Pasupati / Tamansari) dan S2 (Dipatiukur), sink T1
(PUSDAI / Surapati Timur) dan T2 (Diponegoro Timur), 4 jalur S1/S2 ke T1/T2.

## Isi folder

```
video_counting/
  config/titik_hitung.yaml       titik pengambilan data: CCTV, garis hitung per edge, ekr, catatan antrean
  config/uji_cctv_malam.yaml     config uji 29 Okt 2026 malam (7 CCTV, 6 menit)
  config/demo.yaml               config uji video contoh Intel (bukan data Gasibu)
  config/uji_cctv_malam_conf01.yaml  varian conf 0,1 untuk perbandingan model
  config/cctv_usulan_awal.yaml   10 CCTV usulan awal, dipakai cek_cctv.py saja
  config/cctv_spec_kelompok.yaml 25 kamera di tabel 7.1 spec graf kelompok, dipakai cek_cctv.py saja
  cek_cctv.py                    cek CCTV hidup atau mati, resolusi, fps, satu frame, cari alternatif
  rekam_cctv.py                  rekam stream CCTV ke data/video/<titik>/ (.ts + .json jam mulai)
  kalibrasi.py                   pasang garis hitung per edge, bisa dibantu peta jejak kendaraan
  hitung.py                      deteksi + tracking (ByteTrack) + lintasan garis -> events_<titik>.csv
  agregasi.py                    events -> rekap.csv per interval dan jam_puncak.csv
  potong_klip.py                 potong klip berpenanda detik untuk hitung manual
  validasi.py                    bandingkan dengan hitungan manual -> validasi.csv
  tests/test_lintasan.py         20 tes
hasil_uji/                       CSV dan JSON hasil uji (demo dan CCTV malam)
data/lapangan/                   CSV hasil pengambilan data asli
data/video/, models/             video mentah dan bobot model (tidak masuk repo)
```

## Setup (sekali saja)

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/yolo settings sync=False
```

Perintah ketiga mematikan kiriman data analitik Ultralytics. Butuh juga `ffmpeg` (di Mac: `brew install ffmpeg`).
Bobot model (`yolo26s.pt`, `yolo26m.pt`, `yolo26l.pt`) ditaruh di `models/`; kalau belum ada, terunduh otomatis dari
rilis Ultralytics saat `hitung.py` pertama kali jalan. Device dipilih otomatis: `mps` di Mac Apple Silicon, `cuda`
kalau ada GPU NVIDIA, selain itu `cpu`.

## Alur pengambilan data (satu perintah per tahap)

Semua perintah dijalankan dari folder ini.

1. **Cek CCTV** beberapa menit sebelum merekam: `python video_counting/cek_cctv.py --alternatif 350`.
   Hasilnya tabel status dan frame tiap kamera di `dokumentasi/cek_cctv/`. Kalau ada yang mati, ganti url-nya di
   config dengan alternatif yang hidup.
2. **Rekam** semua titik CCTV bersamaan: `python video_counting/rekam_cctv.py --menit 240`. Laptop jangan tidur
   selama merekam. Kalau stream putus, perekaman lanjut otomatis sebagai bagian baru.
3. **Kalibrasi garis** tiap edge. Lihat dulu jejak kendaraannya:
   `python video_counting/kalibrasi.py --titik T1 --frame cek_T1.jpg --lintasan 60`, lalu pasang garis tegak lurus
   jejak: `python video_counting/kalibrasi.py --titik T1 --garis L1 --koordinat X1 Y1 X2 Y2 --datang X Y`
   (`--datang` = satu titik di sisi tempat kendaraan datang untuk arah edge). Mode klik juga ada (tanpa
   `--koordinat`). Cek hasilnya dengan `--frame` lagi; panah merah harus menunjuk searah edge.
4. **Uji 1 menit dulu**: `python video_counting/hitung.py --titik T1 --detik 60 --anotasi`, lalu tonton
   `data/lapangan/anotasi_*.mp4`.
5. **Proses penuh**: `python video_counting/hitung.py`.
6. **Isi ekr** SM dan KB tiap titik dari tabel ekr PKJI 2014 (wajib, jangan pakai angka dari chat AI), isi juga
   catatan `antrean` dari lapangan, lalu `python video_counting/agregasi.py`.
7. **Validasi**: potong 3 klip x 2 menit per titik (`python video_counting/potong_klip.py --titik T1 --mulai 600
   --durasi 120 --lambat 0.5`), dua orang menghitung manual, isi `data/lapangan/manual.csv` (format di
   `python video_counting/validasi.py -h`), lalu `python video_counting/validasi.py`. Target: error total
   paling besar 10%, motor paling besar 15%.

Tes: `python -m pytest video_counting/tests` atau `python video_counting/tests/test_lintasan.py`.

## Keluaran

| File | Isi |
|---|---|
| `events_<titik>.csv` | satu baris per kendaraan: video, titik, garis, edge_model, track_id, frame, detik, waktu, kelas_coco, kelas_pkji, arah, conf_rata, kamera_geser |
| `events_<titik>.meta.json` | bobot, tracker, imgsz, versi ultralytics, garis, bagian video (jam mulai, fps, durasi, rentang kamera bergeser) |
| `rekap.csv` | per titik, garis, arah, interval: KR, SM, KB, KTB, kend_per_jam, skr_per_jam, ada_antrean |
| `jam_puncak.csv` | jendela 60 menit dengan kend/jam terbesar per garis dan arah |
| `validasi.csv` | manual vs otomatis per kelas, error, target, lulus atau tidak |

`arah` bernilai `positif` atau `negatif` sesuai sisi garis tempat kendaraan datang. Di rekap, `searah_edge = ya`
artinya arah itu sama dengan arah edge di graf.

## Hal penting

- **Waktu kendaraan** diambil dari jam laptop saat merekam (jam selesai dikurangi durasi rekaman), dengan ketelitian
  sekitar satu potongan HLS (paling lama 15 detik). Jam yang tampil di layar CCTV tidak dipakai karena di beberapa
  kamera meleset sampai 20 menit, bahkan ada yang tahunnya salah.
- **Lintasan garis** dihitung saat titik acuan kendaraan (tengah sisi bawah kotak) pindah sisi garis di dalam segmen,
  asal sebelumnya pernah cukup jauh di sisi asal (0,2 x tinggi kotaknya). Kotak kendaraan yang diam di garis tidak
  terhitung. Garis harus dibentangkan dari trotoar ke trotoar, kendaraan yang lewat di luar ujung garis tidak dihitung.
- **Model**: yolo26s dengan input 640 untuk CCTV 640 x 480 (titik S1 yang 1280 x 720 memakai 1280) dan conf 0,1,
  dipilih dari uji 29 Okt 2026.
- **Kamera bergeser** (PTZ diputar, kamera kesenggol, siaran mati) dideteksi otomatis tiap detik dengan pencocokan
  titik fitur ke latar 5 detik pertama. Rentang waktunya dicatat di meta, dan kendaraan di rentang itu tidak ikut
  rekap.
- **Yang diukur arus, bukan kapasitas.** Arus sama dengan kapasitas hanya di titik yang hulunya sedang antre.
- Video mentah dan video beranotasi tidak masuk repo publik. Sumber CCTV ditulis di laporan.

- Tidak perlu screen record situs pelindung. `rekam_cctv.py` mengambil stream asli langsung dari servernya: resolusi
  asli, tanpa tampilan web, semua kamera sekaligus, dan jam mulai tercatat otomatis.
- Status CCTV berubah-ubah (ada yang mati lalu hidup lagi dalam dua jam), jadi jalankan `cek_cctv.py` sesaat sebelum
  merekam.

## Hasil uji 29 Oktober 2026 (malam)

- 10 CCTV usulan awal: 6 hidup, 4 mati (semua milik DPKP3 dan Dishub). Config memakai 7 CCTV Diskominfo yang hidup.
- Perbandingan model di 3 kamera: yolo26s dengan input 640 menangkap kendaraan paling banyak dan paling cepat
  (sekitar 45 frame/detik di M2 Pro); input 1280 dan model m atau l tidak lebih baik untuk CCTV 640 x 480.
- Kendaraan yang menghadap kamera terhitung tepat (14 dari 14 di V_Djuanda_Hasanuddin arah selatan). Mobil yang
  menjauhi kamera sebagian besar terhitung, tetapi motor yang menjauhi kamera di malam hari hampir tidak terdeteksi
  (pengendaranya terbaca sebagai person). Uji siang hari diperlukan sebelum data Minggu dipakai.
- CSV hasil uji ada di `hasil_uji/`. Laporan uji lengkap (docx dan pdf) dan video anotasi disimpan lokal di
  `dokumentasi/`.
