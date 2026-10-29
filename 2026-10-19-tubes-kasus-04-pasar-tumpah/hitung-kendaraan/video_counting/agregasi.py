"""events_<titik>.csv -> rekap.csv (per titik, garis, arah, interval) dan jam_puncak.csv.

  python video_counting/agregasi.py
  python video_counting/agregasi.py --keluar data/uji/m

Interval mengikuti jam (08:00, 08:05, dan seterusnya). Durasi tiap interval adalah bagian interval yang benar-benar
terekam dengan kamera diam, jadi kend/jam tetap benar walaupun rekaman sempat putus atau kamera sempat diputar.
Interval yang terekam kurang dari setengahnya tidak dilaporkan.

kend/jam = (KR + SM + KB) x 3600 / detik terekam. KTB (sepeda) dilaporkan terpisah dan tidak masuk skr.
skr/jam dikosongkan selama ekr SM atau KB di config masih null.
"""
import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from hitung import CONFIG, KELUAR, folder

KELAS = ["KR", "SM", "KB", "KTB"]
KOLOM = ["titik", "garis", "edge_model", "arah", "searah_edge", "mulai_interval", "durasi_menit", *KELAS,
         "kend_per_jam", "skr_per_jam", "ada_antrean"]


def baca_events(path):
    with open(path, newline="") as f:
        return [dict(e, waktu=datetime.fromisoformat(e["waktu"])) for e in csv.DictReader(f)]


def rentang_valid(bagian):
    """Rentang waktu yang terekam dan kameranya diam, dari daftar bagian di meta hasil hitung.py."""
    hasil = []
    for b in bagian:
        m = datetime.fromisoformat(b["mulai"])
        sisa = [(0.0, b["durasi_detik"])]
        for g0, g1 in b.get("kamera_geser", []):
            sisa = [x for a, z in sisa for x in ((a, min(z, g0)), (max(a, g1), z)) if x[1] > x[0]]
        hasil += [(m + timedelta(seconds=a), m + timedelta(seconds=z)) for a, z in sisa]
    return hasil


def tertutup(rentang, awal, akhir):
    """Berapa detik dari [awal, akhir) yang ada di dalam rentang."""
    return sum(max(0.0, (min(z, akhir) - max(a, awal)).total_seconds()) for a, z in rentang)


def ada_antrean(antrean, awal, akhir):
    if antrean is None:
        return ""  # belum ada catatan lapangan
    for a, b in antrean:
        if datetime.fromisoformat(a) < akhir and datetime.fromisoformat(b) > awal:
            return "ya"
    return "tidak"


def rekap(events, rentang, interval_menit, ekr, garis, antrean=None):
    """garis = [(id, edge_model)]. Satu baris per garis, arah, dan interval yang cukup terekam."""
    if not rentang:
        return []
    lengkap = all(ekr.get(k) is not None for k in ("KR", "SM", "KB"))
    detik = interval_menit * 60
    t0, t1 = min(a for a, _ in rentang), max(z for _, z in rentang)
    awal0 = datetime.fromtimestamp(t0.timestamp() // detik * detik, t0.tzinfo)  # dibulatkan ke bawah mengikuti jam
    baris = []
    for gid, edge in garis:
        for arah in ("positif", "negatif"):
            awal = awal0
            while awal < t1:
                akhir = awal + timedelta(seconds=detik)
                cover = tertutup(rentang, awal, akhir)
                if cover >= detik / 2:
                    n = dict.fromkeys(KELAS, 0)
                    for e in events:
                        if (e["garis"] == gid and e["arah"] == arah and e.get("kamera_geser") != "ya"
                                and e["kelas_pkji"] in n and awal <= e["waktu"] < akhir):
                            n[e["kelas_pkji"]] += 1
                    per_jam = 3600 / cover
                    skr = sum(n[c] * ekr[c] for c in ("KR", "SM", "KB")) * per_jam if lengkap else None
                    baris.append({"garis": gid, "edge_model": edge, "arah": arah, "mulai_interval": awal,
                                  "durasi_menit": round(cover / 60, 2), **n,
                                  "kend_per_jam": round((n["KR"] + n["SM"] + n["KB"]) * per_jam, 1),
                                  "skr_per_jam": "" if skr is None else round(skr, 1),
                                  "ada_antrean": ada_antrean(antrean, awal, akhir)})
                awal = akhir
    return baris


def jam_puncak(baris, interval_menit):
    """Per garis dan arah: jendela 60 menit (interval berurutan tanpa celah) dengan kend/jam terbesar."""
    n = round(60 / interval_menit)
    langkah = timedelta(minutes=interval_menit)
    hasil = []
    for gid, arah in dict.fromkeys((x["garis"], x["arah"]) for x in baris):
        b = sorted((x for x in baris if x["garis"] == gid and x["arah"] == arah), key=lambda x: x["mulai_interval"])
        terbaik = None
        for i in range(len(b) - n + 1):
            w = b[i:i + n]
            if w[-1]["mulai_interval"] - w[0]["mulai_interval"] != (n - 1) * langkah:
                continue  # ada interval yang hilang di tengah jendela
            menit = sum(x["durasi_menit"] for x in w)
            kend = sum(x["KR"] + x["SM"] + x["KB"] for x in w) * 60 / menit
            if terbaik is None or kend > terbaik[0]:
                skr = "" if w[0]["skr_per_jam"] == "" else sum(x["skr_per_jam"] * x["durasi_menit"] for x in w) / menit
                terbaik = (kend, w[0], skr)
        if terbaik and terbaik[0] > 0:
            kend, x, skr = terbaik
            hasil.append({"garis": gid, "edge_model": x["edge_model"], "arah": arah, "mulai": x["mulai_interval"],
                          "kend_per_jam": round(kend, 1), "skr_per_jam": skr if skr == "" else round(skr, 1)})
    return hasil


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--keluar", type=Path, default=KELUAR)
    a = ap.parse_args()
    keluar = folder(a.keluar)
    cfg = yaml.safe_load(a.config.read_text())
    iv = cfg["interval_menit"]
    semua, puncak = [], []
    for t in cfg["titik"]:
        f = keluar / f"events_{t['id']}.csv"
        if not f.exists():
            continue
        meta = json.loads(f.with_suffix(".meta.json").read_text())
        if None in (t["ekr"].get("SM"), t["ekr"].get("KB")):
            print(f"{t['id']}: ekr SM/KB belum diisi dari tabel PKJI 2014, kolom skr_per_jam dikosongkan")
        garis = [(g["id"], g["edge_model"]) for g in meta["garis"]]
        searah = {g["id"]: g["arah_dihitung"] for g in meta["garis"]}
        baris = rekap(baca_events(f), rentang_valid(meta["bagian"]), iv, t["ekr"], garis, t.get("antrean"))
        for x in baris:
            x.update(titik=t["id"], searah_edge="ya" if x["arah"] == searah[x["garis"]] else "tidak")
        semua += baris
        p = jam_puncak(baris, iv)
        if not p:
            print(f"{t['id']}: rekaman kurang dari 60 menit tanpa celah, jam puncak tidak dihitung")
        puncak += [dict(x, titik=t["id"]) for x in p]

    if not semua:
        raise SystemExit(f"belum ada events_*.csv di {keluar}, jalankan hitung.py dulu")
    with open(keluar / "rekap.csv", "w", newline="") as f:
        w = csv.DictWriter(f, KOLOM)
        w.writeheader()
        for x in semua:
            w.writerow(dict(x, mulai_interval=x["mulai_interval"].isoformat(timespec="seconds")))
    with open(keluar / "jam_puncak.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["titik", "garis", "edge_model", "arah", "mulai", "kend_per_jam", "skr_per_jam"])
        w.writeheader()
        for x in puncak:
            w.writerow(dict(x, mulai=x["mulai"].isoformat(timespec="seconds")))
    print(f"rekap.csv: {len(semua)} baris, jam_puncak.csv: {len(puncak)} baris ({keluar})")


if __name__ == "__main__":
    main()
