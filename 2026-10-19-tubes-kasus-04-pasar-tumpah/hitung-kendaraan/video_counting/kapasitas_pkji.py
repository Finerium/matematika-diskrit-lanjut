"""Kapasitas tiap ruas graf kasus 4 dengan rumus PKJI jalan perkotaan, lalu dicek terhadap arus hasil hitung CCTV dan HP.

C = C0 x FCLJ x FCPA x FCHS x FCUK (skr/jam per arah)
- 2/2TT (dua arah tak terbagi): C0 2900 untuk dua arah, dibagi 2 karena graf hanya memakai satu arah (FCPA 1,00 untuk
  pembagian 50:50). FCLJ dari lebar jalur total.
- Terbagi (4/2T, 6/2T) dan satu arah: C0 1650 per lajur dikali jumlah lajur, FCLJ dari lebar per lajur. Jalan satu arah
  memakai baris FCHS 2/2TT, jalan terbagi memakai baris FCHS 4/2T.
- FCUK 1,00 (Kota Bandung 1 sampai 3 juta jiwa). Hambatan samping hari biasa dianggap sedang (S) untuk semua ruas.
- Lebar dan jumlah lajur dari graph/data/graf.json (OpenStreetMap). Kalau lebarnya rentang, dipakai batas bawah. Jalan
  lingkungan yang lebarnya di bawah 5 m memakai nilai tabel terkecil (5 m), jadi angkanya batas atas.
- Penyempitan pasar di Jl. Gasibu Atas: hambatan samping naik dari sedang ke sangat tinggi (FCHS 0,91 jadi 0,81, turun
  sekitar 11%). Angka ini sementara sampai perbandingan Gasibu_02 Sabtu 21 dan Minggu 22 November keluar.

Jalankan dari folder hitung-kendaraan: python video_counting/kapasitas_pkji.py
Hasil: hasil_hitung/kapasitas_pkji.csv dan hasil_hitung/cek_arus_vs_kapasitas.csv
"""
import csv
from pathlib import Path

P = Path(__file__).resolve().parents[1]
C0 = {"2/2TT": 2900, "terbagi": 1650, "1-arah": 1650}
FCLJ_LAJUR = {3.00: 0.92, 3.25: 0.96, 3.50: 1.00, 3.75: 1.04, 4.00: 1.08}
FCLJ_JALUR_2_2TT = {5.0: 0.56, 6.0: 0.87, 7.0: 1.00, 8.0: 1.14, 9.0: 1.25, 10.0: 1.29, 11.0: 1.34}
FCHS = {"terbagi": {"S": 0.91, "ST": 0.81}, "2/2TT": {"S": 0.86, "ST": 0.68}}
FCHS["1-arah"] = FCHS["2/2TT"]

# (dari, ke, nama jalan, tipe, lajur, lebar). lebar = lebar jalur total untuk 2/2TT, lebar per lajur untuk yang lain.
RUAS = [
    ("S1", "V_Cikapayang", "Jl. Tamansari (turun Pasupati)", "2/2TT", 2, 7.0),
    ("V_Cikapayang", "V_Sulanjana", "Jl. Tamansari ke Sulanjana", "2/2TT", 2, 7.0),
    ("V_Cikapayang", "V_DU_Selatan", "Jl. Cikapayang", "terbagi", 2, 3.00),
    ("V_DU_Selatan", "V_Singaperbangsa", "Jl. Dipatiukur (selatan)", "2/2TT", 2, 8.0),
    ("V_DU_Selatan", "V_Gasibu_Barat", "Jl. Surapati (barat, bawah flyover)", "terbagi", 2, 3.50),
    ("S2", "V_Hasanuddin", "Jl. Dipatiukur (tengah)", "2/2TT", 2, 8.0),
    ("V_Hasanuddin", "V_Singaperbangsa", "Jl. Dipatiukur (utara)", "2/2TT", 2, 8.0),
    ("V_Hasanuddin", "V_Djuanda_Hasanuddin", "Jl. Hasanuddin", "2/2TT", 2, 6.0),
    ("V_Djuanda_Hasanuddin", "V_DU_Selatan", "Jl. Ir. H. Djuanda (SMA 1 ke Cikapayang)", "terbagi", 2, 3.00),
    ("V_DU_Selatan", "V_Djuanda_Diponegoro", "Jl. Ir. H. Djuanda (ke Diponegoro)", "terbagi", 2, 3.00),
    ("V_Sulanjana", "V_Djuanda_Diponegoro", "Jl. Sulanjana", "2/2TT", 2, 6.0),
    ("V_Djuanda_Diponegoro", "V_AriaJipang", "Jl. Diponegoro (barat)", "terbagi", 2, 3.50),
    ("V_AriaJipang", "V_Cilamaya", "Jl. Aria Jipang", "2/2TT", 2, 6.0),
    ("V_Cilamaya", "V_Cimandiri", "Jl. Cilamaya", "1-arah", 2, 3.50),
    ("V_Cimandiri", "V_Cisanggarung", "Jl. Cimandiri", "1-arah", 2, 3.00),
    ("V_Cisanggarung", "V_Cisangkuy", "Jl. Cisanggarung / Cimanuk", "2/2TT", 2, 6.0),
    ("V_Cisangkuy", "T2", "Jl. Cisangkuy", "1-arah", 2, 3.50),
    ("V_Cisanggarung", "V_Citarum", "Jl. Cisanggarung", "1-arah", 2, 3.00),
    ("V_Citarum", "T2", "Jl. Citarum", "2/2TT", 2, 7.0),
    ("V_Singaperbangsa", "V_Titiran", "Jl. Singaperbangsa", "2/2TT", 2, 5.0),
    ("V_Titiran", "V_Merak", "Jl. Titiran", "2/2TT", 1, 5.0),
    ("V_Merak", "V_Surapati_Merak", "Jl. Merak", "2/2TT", 2, 5.0),
    ("V_Titiran", "V_Tikukur", "Jl. Titiran (ke Tikukur)", "2/2TT", 1, 5.0),
    ("V_Tikukur", "V_Gagak", "Jl. Tikukur", "2/2TT", 1, 5.0),
    ("V_Gagak", "V_Surapati_Gagak", "Jl. Gagak", "2/2TT", 1, 5.0),
    ("V_Gasibu_Barat", "V_Gasibu_Timur", "Jl. Gasibu Atas (Surapati utara Lapangan Gasibu)", "terbagi", 3, 3.75),
    ("V_Gasibu_Timur", "V_Surapati_Merak", "Jl. Surapati (depan Telkom)", "terbagi", 3, 3.75),
    ("V_Surapati_Merak", "V_Surapati_Gagak", "Jl. Surapati (timur)", "terbagi", 3, 3.75),
    ("V_Surapati_Gagak", "T1", "Jl. Surapati (ke PUSDAI)", "terbagi", 3, 3.75),
    ("V_Gasibu_Timur", "V_Diponegoro_Sentot", "Jl. Sentot Alibasyah", "1-arah", 2, 3.50),
    ("V_Diponegoro_Sentot", "T2", "Jl. Diponegoro (timur)", "terbagi", 2, 3.50),
]
RUAS_PASAR = ("V_Gasibu_Barat", "V_Gasibu_Timur")


def kapasitas(tipe, lajur, lebar, khs="S"):
    if tipe == "2/2TT":
        fclj = FCLJ_JALUR_2_2TT[lebar]
        return round(C0[tipe] * fclj * 1.00 * FCHS[tipe][khs] * 1.00 * 0.5, 1), fclj
    fclj = FCLJ_LAJUR[lebar]
    return round(C0[tipe] * lajur * fclj * FCHS[tipe][khs] * 1.00, 1), fclj


def arus_terukur():
    """Arus searah edge yang dinilai layak, skr/jam, diambil yang terbesar dari CCTV Sabtu, CCTV Minggu, dan HP."""
    hasil = {}
    for label, f in [("CCTV Sabtu 14 Nov", "cctv_14nov_sabtu/ringkas_30menit_per_jam_cctv_14nov_sabtu.csv"),
                     ("CCTV Minggu 15 Nov", "cctv_15nov_minggu/ringkas_30menit_per_jam_cctv_15nov_minggu.csv"),
                     ("HP 1 Nov", "hp_1nov/rekap_15menit_per_jam_hp_1nov.csv")]:
        for r in csv.DictReader(open(P / "hasil_hitung" / f)):
            if r["searah_edge"] != "ya" or not r["dipakai_sebagai_arus_edge"].startswith("ya"):
                continue
            try:
                skr = float(r["skr_per_jam"])
            except ValueError:
                continue
            if skr > hasil.get(r["edge_model"], (0, ""))[0]:
                hasil[r["edge_model"]] = (skr, f"{label} ({r['titik']})")
    return hasil


def main():
    terukur = arus_terukur()
    baris, cek = [], []
    for a, b, nama, tipe, lajur, lebar in RUAS:
        c, fclj = kapasitas(tipe, lajur, lebar)
        c_pasar = kapasitas(tipe, lajur, lebar, "ST")[0] if (a, b) == RUAS_PASAR else ""
        edge = f"{a}->{b}"
        baris.append({"edge_model": edge, "nama_jalan": nama, "tipe": tipe, "lajur": lajur, "lebar_m": lebar,
                      "C0": C0[tipe], "FCLJ": fclj, "FCHS_normal": FCHS[tipe]["S"], "kapasitas_skr_per_jam": c,
                      "kapasitas_pasar_skr_per_jam": c_pasar})
        if edge in terukur:
            arus, sumber = terukur[edge]
            cek.append({"edge_model": edge, "nama_jalan": nama, "arus_terukur_skr_per_jam": arus, "sumber": sumber,
                        "kapasitas_skr_per_jam": c, "derajat_kejenuhan": round(arus / c, 2),
                        "arus_tidak_melebihi_kapasitas": "ya" if arus <= c * 1.05 else "tidak"})
    for nama, isi in [("kapasitas_pkji.csv", baris), ("cek_arus_vs_kapasitas.csv", cek)]:
        with open(P / "hasil_hitung" / nama, "w", newline="") as f:
            w = csv.DictWriter(f, list(isi[0]))
            w.writeheader()
            w.writerows(isi)
    for x in cek:
        print(f"{x['edge_model']:44} arus {x['arus_terukur_skr_per_jam']:7.1f}  kapasitas {x['kapasitas_skr_per_jam']:7.1f}  "
              f"DJ {x['derajat_kejenuhan']}")
    print(f"{len(baris)} ruas ditulis ke hasil_hitung/kapasitas_pkji.csv, {len(cek)} ruas dicek terhadap arus terukur")


if __name__ == "__main__":
    main()
