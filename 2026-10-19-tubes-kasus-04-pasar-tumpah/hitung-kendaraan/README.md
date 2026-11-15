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
6. **Isi ekr** SM dan KB tiap titik dari tabel ekr PKJI (bagian "ekr" di bawah), sesuai tipe jalan, lebar jalur, dan
   arus di titik itu. Kalau satu titik menghitung jalan dengan tipe berbeda, isi `ekr` di garisnya. Isi juga catatan
   `antrean` dari lapangan, lalu `python video_counting/agregasi.py`.
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
- **Video HP yang dipegang tangan** (`ikut_kamera: <detik>` di config titik): tiap frame dicocokkan ke frame acuan
  (homografi ORB + RANSAC) dan titik kendaraan dipindah ke koordinat frame acuan, jadi garis ikut bergerak bersama
  jalan. Garis dipasang di frame acuan itu (kalibrasi.py otomatis memakainya). Frame yang tidak cocok dicatat sebagai
  kamera bergeser, dan meta mencatat berapa detik tiap garis tampak di gambar (`garis_terlihat_detik`, dibobot
  bagian garis yang masuk gambar), untuk menghitung arus per jam garis itu.
- **Satu kendaraan dua kotak** (angkot dapat kotak car dan truck, kendaraan dekat kamera dapat 2-3 kotak): di blok
  `model` config bisa diisi `agnostic_nms: true` (NMS lintas kelas) dan `iou_ganda: 0.5` (lintasan track yang kotaknya
  bertumpuk IoU >= 0,5 dengan track lain yang sudah melintas ke arah yang sama di frame itu tidak dihitung). Bawaannya
  mati; sekarang dipakai titik V_Hasanuddin.
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

## Pemeriksaan rekaman HP 14 November 2026

Arah kamera dan label tiap garis di enam rekaman HP 1 November dicek ulang dari frame video, bayangan, tag lokasi, dan peta
OSM. Titiran sudah benar. Di Singaperbangsa arahnya terbalik sehingga `arah_dihitung` dibalik. Garis L2 di Hasanuddin ternyata
menghitung kendaraan yang belok masuk Jl. Hasanuddin, jadi labelnya sekarang `V_Hasanuddin->V_Djuanda_Hasanuddin`, sedangkan L1
adalah arus Dipatiukur ke utara yang bukan edge graf.

Edge `S2->V_Singaperbangsa` belum bisa diukur andal dari kedua video karena arus lurus ke selatan kecil dan sering tertutup
antrean. Hitungan manual dua menit di video Singaperbangsa memberi 7 kendaraan yang yakin sedangkan program mencatat 21.

Jam `creation_time` di video HP Android ternyata jam selesai rekam. Ini terlihat dari bus yang muncul di dua video, jadi rentang
rekaman sebenarnya 15 menit sebelum jam itu.

Sebagai pembanding, klip 1 tiap titik dihitung secara visual oleh AI dari frame video (ini bukan validasi manusia). Di garis
edge, program sekitar 7 sampai 10% lebih sedikit dari hitungan visual. Motor kurang 13 sampai 14% karena motor di lajur jauh
tertutup mobil, dan kendaraan besar terlalu banyak (29 lawan 7) karena angkot dan mobil boks terbaca truck atau bus. Rinciannya
ada di `hasil_hitung/hp_1nov/cek_visual_ai_klip1.csv` dan `banding_visual_ai_klip1.csv`.

Rekap dibuat ulang dengan `python video_counting/rekap_hp_1nov.py`. Kolom `dipakai_sebagai_arus_edge` menandai baris yang boleh
dipakai sebagai arus edge graf. Template validasi hitung manual oleh dua orang ada di `data/lapangan/manual_template.csv` dengan
panduannya di `data/lapangan/PANDUAN_VALIDASI.md`, sedangkan klip validasinya disimpan lokal karena besar.

## Rekaman CCTV Sabtu 14 November 2026

Sembilan kamera direkam bersamaan pukul 07.30 sampai 08.00 sebagai kondisi tanpa pasar tumpah, lalu dihitung dengan config
`cctv_14nov_sabtu.yaml`. Sudut kesembilan kamera sama dengan 13 November sehingga garis hitung tidak diubah. Rekap ada di
`hasil_hitung/cctv_14nov_sabtu/` dan bisa dibuat ulang dengan `python video_counting/rekap_cctv.py`.

Yang layak dipakai sebagai arus edge baru empat, yaitu S2 ke V_Singaperbangsa sekitar 1.510 kend/jam, V_DU_Selatan ke
V_Singaperbangsa sekitar 2.702 kend/jam, V_Djuanda_Hasanuddin ke V_Djuanda_Diponegoro sekitar 1.852 kend/jam, dan V_Sulanjana ke
V_Djuanda_Diponegoro sekitar 720 kend/jam. Di lima kamera lain motor banyak tidak terhitung karena pagi itu berkabut dan nilai
kepercayaan deteksi motor di bawah ambang pembuatan jejak ByteTrack, atau rekamannya rusak (Gasibu Barat). Arah kamera S1
terhadap edge S1 ke V_Cikapayang juga perlu dicek ulang karena hampir semua kendaraan tercatat di arah lawan.

## Rekaman CCTV Minggu 15 November 2026

Kamera yang sama direkam lagi pukul 07.30 sampai 08.00 saat pasar tumpah berlangsung, lalu dihitung dengan config
`cctv_15nov_minggu.yaml` (garis hitung sama dengan Sabtu). S2 tidak terekam karena stream CCTV-nya mengembalikan 404 sepanjang
jam itu. Rekap ada di `hasil_hitung/cctv_15nov_minggu/`:

```bash
python video_counting/rekap_cctv.py video_counting/config/cctv_15nov_minggu.yaml data/lapangan/cctv_15nov_minggu hasil_hitung/cctv_15nov_minggu cctv_15nov_minggu
```

Dua hal yang terlihat jelas di video. Pertama, jalan di depan kamera Gasibu Timur tertutup penuh tenda lapak pasar, jadi
arusnya 0 kend/jam dan kapasitas ruas itu saat pasar berlangsung bisa dianggap 0. Kedua, Jl. Ir. H. Djuanda ditutup untuk Car
Free Day, jadi kamera Djuanda Hasanuddin cuma mencatat pejalan kaki dan sepeda, dan arus di persimpangan Cikapayang (DU Selatan)
turun dari 2.702 ke 480 kend/jam. Penurunan di dua ruas Djuanda ini efek CFD, bukan efek pasar.

Perbandingan Sabtu dan Minggu per ruas ada di `hasil_hitung/banding_cctv_sabtu_minggu.csv`. Ruas yang bisa dibandingkan
langsung hanya Sulanjana (720 lawan 686 kend/jam, rasio 0,95). Gasibu Barat Minggu layak sebagai batas bawah (1.034 kend/jam)
tapi rekaman Sabtunya rusak. S1, Surapati Merak, dan T1_T2 masih kurang hitung motor seperti Sabtu.

## ekr

Arus diubah ke skr/jam dengan ekr dari tabel ekr PKJI untuk jalan perkotaan. KR selalu 1,0. Sepeda (KTB) tidak ikut
dihitung.

| Tipe jalan | Arus | KB | SM (lebar jalur <= 6 m) | SM (lebar jalur > 6 m) |
|---|---|---|---|---|
| 2/2TT | < 1800 kend/jam dua arah | 1,3 | 0,5 | 0,40 |
| 2/2TT | >= 1800 kend/jam dua arah | 1,2 | 0,35 | 0,25 |
| 2/1 dan 4/2T | < 1050 kend/jam per lajur | 1,3 | 0,40 | 0,40 |
| 2/1 dan 4/2T | >= 1050 kend/jam per lajur | 1,2 | 0,25 | 0,25 |
| 3/1 dan 6/2T | < 1100 kend/jam per lajur | 1,3 | 0,40 | 0,40 |
| 3/1 dan 6/2T | >= 1100 kend/jam per lajur | 1,2 | 0,25 | 0,25 |

Dokumen resmi PKJI tidak bisa diunduh dari situs Bina Marga (yang terbuka hanya cuplikan 5 halaman), jadi angka di atas
diambil dari dua skripsi yang mengutip tabel PKJI 2023 dengan angka yang sama persis (Tabel 2.9 dan 2.10 skripsi
Mauliddyah Turrochmah, UM Surabaya; Tabel 2.23 dan 2.24 skripsi Arif Rachman, ITPLN). Kutipan tabel PKJI 2014 di sumber
lain memberi angka yang sama, tapi batas arus 2/2TT di sana tertulis "< 3700" lalu ">= 1800". Batas yang dipakai di sini
1800, sama dengan PKJI 2023. Di dua titik (S2 Sabtu 2.772 dan V_Singaperbangsa 2.377 kend/jam dua arah) pilihan ini
mengubah ekr. Kalau ada yang memegang dokumen resmi PKJI, angka ini sebaiknya dicek ulang.

Tipe jalan, lebar jalur, dan jumlah lajur tiap titik diambil dari OpenStreetMap (unduhan 19 Oktober 2026) dan
`graph/data/graf.json`, lalu ditulis sebagai komentar di samping `tipe_jalan` di config. Jl. Gagak ditulis satu arah
di graf.json tapi dua arah di OSM. Yang dipakai OSM, karena arah lawan juga terhitung di rekaman HP.
