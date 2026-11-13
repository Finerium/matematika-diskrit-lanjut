# Panduan Hitung Manual untuk Validasi

Folder ini dipakai untuk mengecek hasil hitung otomatis (YOLO) dari enam video HP tanggal 1 November 2026.
Dua orang menghitung kendaraan di klip yang sama secara terpisah, lalu hasilnya dibandingkan dengan hitungan
program lewat `validasi.py`.

## Isi folder

- Enam subfolder, satu per titik (V_Singaperbangsa, V_Hasanuddin, V_Cilamaya, V_Cisanggarung, V_Surapati_Gagak,
  V_Titiran). Tiap subfolder berisi 2 klip dari bagian yang paling ramai, masing-masing 2 menit
  rekaman (sekitar 4 menit saat diputar).
- Klip diputar setengah kecepatan. Angka di pojok kiri atas adalah detik asli video, jadi tetap benar walaupun
  klip diputar lambat. Klip V_Singaperbangsa sedikit lebih lambat lagi (sekitar 4,5 menit) karena frame rate
  video aslinya tidak tetap, angka detiknya tetap benar.
- Garis kuning adalah garis hitung (L1, L2, L3) dan panah merah menunjukkan arah yang dihitung sebagai searah edge.
  Kotak deteksi YOLO sengaja tidak digambar supaya penghitung tidak terpengaruh hasil program.
- `manual_template.csv` adalah lembar isian. Salinan yang sama ada di `hitung-kendaraan/data/lapangan/`.

Nama klip menunjukkan detik mulai dan selesai, misalnya `klip_V_Titiran_singaperbangsa-titiran_280-400.mp4`
berarti detik 280 sampai 400 dari video `singaperbangsa-titiran.mp4`.

## Cara menghitung

1. Dua orang menghitung sendiri-sendiri dan tidak saling melihat hasil sampai keduanya selesai.
2. Hitung satu garis dan satu arah dalam satu kali putar. Boleh pause dan mundur sebanyak perlu. Cara paling
   mudah adalah membuat turus di kertas dengan empat kolom kelas.
3. Kendaraan dihitung saat bagian bawahnya (roda) benar-benar melewati garis kuning. Kendaraan yang lewat di
   luar ujung garis tidak dihitung. Kendaraan yang berhenti di atas garis lalu jalan lagi tetap dihitung satu kali.
4. Kelas kendaraan:
   - KR: mobil penumpang, angkot, taksi, pikap, minibus, mobil boks kecil
   - SM: sepeda motor (motor berboncengan tetap satu)
   - KB: bus dan truk
   - KTB: sepeda
   Gerobak, becak, dan pejalan kaki tidak dihitung.
5. Arah positif dan negatif mengikuti gerak kendaraan di gambar:

| Titik | Garis | positif | negatif |
|---|---|---|---|
| V_Singaperbangsa | L1 | bergerak ke kanan gambar | bergerak ke kiri gambar |
| V_Hasanuddin | L1 dan L2 | ke kanan | ke kiri |
| V_Cilamaya | L2 | ke kanan | ke kiri |
| V_Cisanggarung | L1 | ke kanan | ke kiri |
| V_Surapati_Gagak | L1 (mulut Jl. Gagak) | ke atas gambar, masuk ke Gagak | ke bawah gambar, keluar dari Gagak |
| V_Surapati_Gagak | L2 dan L3 | ke kanan | ke kiri |
| V_Titiran | L1 | ke kanan | ke kiri |

Catatan untuk V_Surapati_Gagak: HP-nya goyang, jadi garis di klip ikut bergeser bersama jalan. Kalau HP menoleh
jauh, garis hilang dari gambar. Kendaraan yang lewat saat garis tidak tampak jangan dihitung. Garis L2 sering
terpotong di bawah gambar, hitung hanya bagian garis yang terlihat.

## Mengisi CSV

Buka `manual_template.csv` dengan Excel, Numbers, atau editor teks. Satu baris berarti satu klip, satu garis, satu
arah, dan satu penghitung. Kolom yang diisi hanya:

- `penghitung`: ganti `penghitung1` dan `penghitung2` dengan nama masing-masing (tanpa koma).
- `KR`, `SM`, `KB`, `KTB`: jumlah kendaraan. Tulis 0 kalau tidak ada. Jangan ada sel yang kosong karena
  `validasi.py` akan berhenti dengan error.

Kolom lain (titik, garis, arah, video, detik klip) jangan diubah. Kalau ada garis atau arah yang memang tidak
sempat dihitung, hapus barisnya dan jangan diisi 0, supaya tidak dianggap tidak ada kendaraan.

Contoh baris yang sudah diisi:

```
titik,garis,arah,video,klip_mulai_detik,klip_selesai_detik,penghitung,KR,SM,KB,KTB
V_Titiran,L1,positif,singaperbangsa-titiran.mp4,280,400,Ghaisan,1,6,0,1
V_Titiran,L1,positif,singaperbangsa-titiran.mp4,280,400,Rekan,1,7,0,1
```

Simpan tetap sebagai CSV (dipisah koma), lalu salin ke `hitung-kendaraan/data/lapangan/manual.csv`.

## Menjalankan validasi.py

Jalankan dari folder `hitung-kendaraan`, satu perintah per titik. Folder `--keluar` adalah folder events yang
sedang berlaku (kalau nanti ada folder `penuh3`, pakai yang itu):

```
PY=~/.venvs/yolo-hitung-kendaraan/bin/python
$PY video_counting/validasi.py --config video_counting/config/hp_1nov/V_Singaperbangsa.yaml --keluar data/lapangan/hp_1nov/V_Singaperbangsa/penuh --manual data/lapangan/manual.csv
$PY video_counting/validasi.py --config video_counting/config/hp_1nov/V_Hasanuddin.yaml --keluar data/lapangan/hp_1nov/V_Hasanuddin/penuh2 --manual data/lapangan/manual.csv
$PY video_counting/validasi.py --config video_counting/config/hp_1nov/V_Cilamaya.yaml --keluar data/lapangan/hp_1nov/V_Cilamaya/penuh2 --manual data/lapangan/manual.csv
$PY video_counting/validasi.py --config video_counting/config/hp_1nov/V_Cisanggarung.yaml --keluar data/lapangan/hp_1nov/V_Cisanggarung/penuh --manual data/lapangan/manual.csv
$PY video_counting/validasi.py --config video_counting/config/hp_1nov/V_Surapati_Gagak.yaml --keluar data/lapangan/hp_1nov/V_Surapati_Gagak/penuh2 --manual data/lapangan/manual.csv
$PY video_counting/validasi.py --config video_counting/config/hp_1nov/V_Titiran.yaml --keluar data/lapangan/hp_1nov/V_Titiran/penuh --manual data/lapangan/manual.csv
```

Hasilnya tampil di layar dan tersimpan sebagai `validasi.csv` di folder `--keluar` tiap titik. Hitungan manual
tiap klip adalah rata-rata kedua penghitung. Target dari spec: error TOTAL (KR + SM + KB) paling besar 10% dan
error SM paling besar 15%. Kolom `lulus` berisi `ya` atau `tidak`.

Kalau selisih kedua penghitung di satu klip lebih dari sekitar 10%, tonton ulang klip itu bersama dulu sebelum
hasilnya dipakai.
