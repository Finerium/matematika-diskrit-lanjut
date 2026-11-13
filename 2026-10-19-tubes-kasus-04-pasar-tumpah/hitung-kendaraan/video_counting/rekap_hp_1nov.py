"""Rekap ulang 6 titik HP 1 Nov 2026 dari events dan config yang berlaku.

  python video_counting/rekap_hp_1nov.py                   # tulis ulang hasil_hitung/hp_1nov
  python video_counting/rekap_hp_1nov.py --keluar /tmp/x   # uji, tidak menimpa apa pun
  python video_counting/rekap_hp_1nov.py --salin <folder>  # tulis ulang lalu salin CSV ke folder lain

Folder events per titik dipilih otomatis: penuh3 kalau ada, lalu penuh2, lalu penuh.
Arah searah dan edge_model diambil dari config hp_1nov/<titik>.yaml yang sekarang, bukan dari meta, jadi kalau arah
di config ditukar hasilnya ikut berubah tanpa proses ulang YOLO.
Per 5 menit memakai agregasi.rekap apa adanya (interval mengikuti jam, interval terekam < 2,5 menit tidak dilaporkan).
Per jam untuk 15 menit dihitung dari seluruh waktu bersih. Rentang kamera_geser di meta dan BUANG di bawah tidak ikut.
skr/jam ditulis "menunggu ekr PKJI 2014" selama ekr SM atau KB di config masih null.
"""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import yaml

P = Path(__file__).resolve().parents[1]   # folder hitung-kendaraan
sys.path.insert(0, str(P / "video_counting"))
import agregasi as ag  # noqa: E402

D = P / "data/lapangan/hp_1nov"
KELUAR = P / "hasil_hitung/hp_1nov"
TITIK = ["V_Hasanuddin", "V_Surapati_Gagak", "V_Cilamaya", "V_Singaperbangsa", "V_Cisanggarung", "V_Titiran"]
URUTAN_FOLDER = ["penuh3", "penuh2", "penuh"]
MENUNGGU = "menunggu ekr PKJI 2014"
# Kamera di Gagak menoleh jauh sekitar detik 465-570 (hasil pemeriksaan), seluruh rentang itu dibuang.
BUANG = {"V_Surapati_Gagak": [(465.0, 570.0)]}
CATATAN = {
    ("V_Hasanuddin", "L1"): "bukan edge graf, ini arus Dipatiukur ke utara (dicek 14 Nov). cek visual AI klip 1: 56 lawan program 51",
    ("V_Hasanuddin", "L2"): "edge V_Hasanuddin->V_Djuanda_Hasanuddin, kendaraan yang belok masuk Jl. Hasanuddin (dicek 14 Nov). "
                            "cek visual AI klip 1: 20 lawan program 21",
    ("V_Surapati_Gagak", "L1"): "garis ikut gerak kamera (homografi). kemungkinan lebih hitung sampai sekitar 6%. "
                                "cek visual AI klip 1: 17 lawan program 20, bergantung ujung kiri garis",
    ("V_Surapati_Gagak", "L2"): "hanya lajur arah timur. garis tampak sekitar 451 dari 902 detik (ujung bawah di luar gambar). "
                                "cek visual AI klip 1: 75 lawan program 74",
    ("V_Surapati_Gagak", "L3"): "hanya lajur arah timur. cek visual AI klip 1: 84 lawan program 63, program kurang motor di rombongan padat",
    ("V_Singaperbangsa", "L1"): "TIDAK LAYAK untuk S2->V_Singaperbangsa. arus lurus ke selatan kecil dan tertutup antrean sehingga "
                                "program banyak salah hitung (hitung manual 14 Nov: 7 yakin lawan program 21 dalam 2 menit). "
                                "arah lawan adalah arus ke utara sekitar 1589 kend/jam dan cocok dengan video Hasanuddin",
    ("V_Cilamaya", "L2"): "layak. L1 dibuang karena hanya noise. cek visual AI klip 1: 64 lawan program 67",
    ("V_Cisanggarung", "L1"): "layak. cek visual AI klip 1: 68 lawan program 68",
    ("V_Titiran", "L1"): "arah kamera dicek 14 Nov dari peta OSM dan bangunan (kanan gambar = utara ke Titiran), "
                         "belum dikonfirmasi perekam. cek visual AI klip 1: 6 lawan program 5 (sampel kecil)",
}


# garis searah yang tidak boleh dipakai sebagai arus edge graf (hasil pemeriksaan 14 Nov 2026)
TIDAK_DIPAKAI = {
    ("V_Hasanuddin", "L1"): "tidak (arus Dipatiukur ke utara, bukan edge graf)",
    ("V_Singaperbangsa", "L1"): "tidak (arus ke selatan tidak terukur andal, lihat catatan)",
}


def events_berlaku(tid):
    for sub in URUTAN_FOLDER:
        f = D / tid / sub / f"events_{tid}.csv"
        if f.exists():
            return f
    raise SystemExit(f"{tid}: belum ada events di {D / tid}")


def skr(n, ekr, detik):
    if any(ekr.get(k) is None for k in ("KR", "SM", "KB")):
        return MENUNGGU
    return round(sum(n[k] * ekr[k] for k in ("KR", "SM", "KB")) * 3600 / detik, 1)


def rekap_titik(tid):
    f = events_berlaku(tid)
    meta = json.loads(f.with_suffix(".meta.json").read_text())
    t = yaml.safe_load((P / f"video_counting/config/hp_1nov/{tid}.yaml").read_text())
    iv, t = t["interval_menit"], t["titik"][0]
    ada = {g["id"] for g in meta["garis"]}  # garis yang benar-benar dihitung di events ini
    cfg_garis = [g for g in t["garis"] if g["id"] in ada]
    garis = [(g["id"], g["edge_model"]) for g in cfg_garis]
    searah = {g["id"]: g["arah_dihitung"] for g in cfg_garis}

    buang = BUANG.get(tid, [])
    bagian = [dict(b, kamera_geser=b.get("kamera_geser", []) + buang) for b in meta["bagian"]]
    rentang = ag.rentang_valid(bagian)
    events = ag.baca_events(f)
    for e in events:
        if any(a <= float(e["detik"]) < z for a, z in buang):
            e["kamera_geser"] = "ya"

    lima = []
    for x in ag.rekap(events, rentang, iv, t["ekr"], garis, t.get("antrean")):
        x.update(titik=tid, searah_edge="ya" if x["arah"] == searah[x["garis"]] else "tidak",
                 mulai_interval=x["mulai_interval"].isoformat(timespec="seconds"),
                 skr_per_jam=x["skr_per_jam"] if x["skr_per_jam"] != "" else MENUNGGU)
        lima.append(x)

    detik = sum((z - a).total_seconds() for a, z in rentang)
    limabelas = []
    for gid, edge in garis:
        for arah in sorted(("negatif", "positif"), key=lambda a: a != searah[gid]):  # searah dulu
            n = dict.fromkeys(ag.KELAS, 0)
            for e in events:
                if e["garis"] == gid and e["arah"] == arah and e["kamera_geser"] != "ya" and e["kelas_pkji"] in n:
                    n[e["kelas_pkji"]] += 1
            ya = arah == searah[gid]
            limabelas.append({
                "titik": tid, "garis": gid, "edge_model": edge, "arah": arah, "searah_edge": "ya" if ya else "tidak",
                "mulai_rekaman_metadata": rentang[0][0].isoformat(timespec="seconds"),
                "detik_bersih": round(detik, 1), **n, "kend": n["KR"] + n["SM"] + n["KB"],
                **{f"{k}_per_jam": round(n[k] * 3600 / detik, 1) for k in ag.KELAS},
                "kend_per_jam": round((n["KR"] + n["SM"] + n["KB"]) * 3600 / detik, 1),
                "skr_per_jam": skr(n, t["ekr"], detik),
                "dipakai_sebagai_arus_edge": (TIDAK_DIPAKAI.get((tid, gid), "ya") if ya else "tidak (arah lawan, bukan edge di graf)"),
                "catatan": CATATAN.get((tid, gid), "") if ya else "",
                "sumber": str(f.relative_to(P)),
            })
    return lima, limabelas


def tulis(path, kolom, baris):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, kolom)
        w.writeheader()
        w.writerows(baris)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keluar", type=Path, help="folder hasil untuk uji; tanpa ini menimpa hasil_hitung/hp_1nov")
    ap.add_argument("--salin", type=Path, help="setelah menulis hasil_hitung/hp_1nov, salin kedua CSV ke folder ini")
    a = ap.parse_args()
    keluar = a.keluar or KELUAR
    keluar.mkdir(parents=True, exist_ok=True)
    lima, limabelas = [], []
    for tid in TITIK:
        x, y = rekap_titik(tid)
        lima += x
        limabelas += y
    tulis(keluar / "rekap_5menit_hp_1nov.csv", ag.KOLOM, lima)
    tulis(keluar / "rekap_15menit_per_jam_hp_1nov.csv", list(limabelas[0]), limabelas)
    if a.keluar is None and a.salin:
        a.salin.mkdir(parents=True, exist_ok=True)
        for f in ("rekap_5menit_hp_1nov.csv", "rekap_15menit_per_jam_hp_1nov.csv"):
            shutil.copy2(keluar / f, a.salin / f)
    for x in limabelas:
        print(x["titik"], x["garis"], x["edge_model"], x["arah"], x["searah_edge"], x["detik_bersih"], x["kend"],
              x["kend_per_jam"], x["sumber"])
    print(f"ditulis ke {keluar}")


if __name__ == "__main__":
    main()
