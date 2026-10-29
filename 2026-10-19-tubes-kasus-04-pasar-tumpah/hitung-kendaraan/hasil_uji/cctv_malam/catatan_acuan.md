# Catatan hitungan acuan uji CCTV malam (29 Okt 2026)

Jendela: detik 30 sampai 90 tiap video uji malam. Dicek pada saat pengujian dengan lembar 4 frame per kandidat
(0,6 dan 0,2 detik sebelum, 0,2 dan 0,6 detik sesudah melintas) lengkap dengan kotak track tiap varian, ditambah
lembar frame tiap 0,5 detik untuk mencari kendaraan yang terlewat semua varian. Ini bukan validasi resmi 2 penghitung
sesuai spec; validasi resmi dilakukan pada data Minggu.

## V_Djuanda_Hasanuddin (V_Djuanda_Hasanuddin_20261029-184158.ts)
- Arah negatif (ke selatan, searah edge V_Djuanda_Hasanuddin->V_Djuanda_Diponegoro, kendaraan menghadap kamera):
  12 KR + 2 SM. Semua kandidat dicek satu per satu; tidak ditemukan kendaraan yang terlewat.
- Arah positif (ke utara, menjauhi kamera): minimal 11 KR + 1 KB + 17 SM. Kandidat yang terdeteksi dicek satu per
  satu (1 hitungan dobel dari s_640 di detik 66,2). Kendaraan terlewat yang dikonfirmasi dengan kotak semua varian:
  motor 47,8 s, motor 50,3 s, mobil 52,3 s, mobil 56,3 s. Sisanya dihitung dari lembar frame (motor di 40,7; 60-62;
  67,4; 70,8-71,6; 73,2-73,6; 75,3; 81,5-83 s dan mobil di 78,9; 80,7; 88 s), jadi angka ini batas bawah.
- Penyebab terlewat: pengendara motor yang membelakangi kamera terdeteksi sebagai person, badan motornya tidak
  terdeteksi; frame rusak dari stream (artefak decode) memutus track; ID track putus tepat saat melintas.

## V_Surapati_Merak (V_Surapati_Merak_20261029-184158.ts)
- Arah positif (ke timur, searah edge V_Surapati_Merak->T1): 18 kandidat semuanya kendaraan roda empat atau lebih
  (17 mobil/angkot, 1 minibus). Motor terlihat banyak di frame tetapi tidak ada satu pun yang terdeteksi, jadi SM tidak
  dihitung manual di titik ini.
- Arah negatif: lajur ke barat macet (bus diam di dekat garis), tidak ada kendaraan yang melintas di jendela ini.

## S2
- Lajur sangat padat motor dan pejalan kaki, tidak dibuat hitungan acuan; hanya dibandingkan antar varian.
