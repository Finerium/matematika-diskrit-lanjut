"""Bandingkan hitungan otomatis dengan hitungan manual -> validasi.csv di folder keluaran.

Format manual.csv (bawaan data/lapangan/manual.csv), satu baris per klip per penghitung. Detik dihitung dari
awal file video yang disebut di kolom video:
  titik,garis,arah,video,klip_mulai_detik,klip_selesai_detik,penghitung,KR,SM,KB,KTB
  T1,L1,positif,T1_20261101-081500.ts,60,180,penghitung1,40,95,2,0
  T1,L1,positif,T1_20261101-081500.ts,60,180,penghitung2,41,99,2,0

arah positif/negatif sama dengan kolom arah di events (lihat panah di gambar kalibrasi.py --frame).
Hitungan manual tiap klip = rata-rata semua penghitung. Error = |otomatis - manual| / manual.
Target spec: error TOTAL (KR + SM + KB) paling besar 10%, SM paling besar 15%.

  python video_counting/validasi.py
  python video_counting/validasi.py --manual data/uji/manual.csv --keluar data/uji/m
"""
import argparse
import csv
from pathlib import Path

import yaml

from agregasi import KELAS, baca_events
from hitung import CONFIG, KELUAR, folder

TARGET = {"TOTAL": 0.10, "SM": 0.15}


def bandingkan(manual, events):
    """manual = baris manual.csv satu titik. Hasil: {(garis, arah, kelas): (manual, otomatis)}, dijumlah semua klip."""
    klip = {}
    for r in manual:
        kunci = (r["garis"], r["arah"], r["video"], float(r["klip_mulai_detik"]), float(r["klip_selesai_detik"]))
        klip.setdefault(kunci, []).append(r)
    hasil = {}
    for (g, arah, video, a, b), rs in klip.items():
        for k in KELAS:
            man = sum(float(r[k]) for r in rs) / len(rs)
            oto = sum(1 for e in events if e["garis"] == g and e["arah"] == arah and e["video"] == video
                      and e["kelas_pkji"] == k and a <= float(e["detik"]) < b)
            m0, o0 = hasil.get((g, arah, k), (0, 0))
            hasil[(g, arah, k)] = (m0 + man, o0 + oto)
    for g, arah in {(g, arah) for g, arah, _ in hasil}:
        hasil[(g, arah, "TOTAL")] = tuple(sum(hasil[(g, arah, k)][i] for k in ("KR", "SM", "KB")) for i in (0, 1))
    return hasil


def error(man, oto):
    if man == 0:
        return 0.0 if oto == 0 else None
    return abs(oto - man) / man


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--keluar", type=Path, default=KELUAR)
    ap.add_argument("--manual", type=Path, help="bawaan <keluar>/manual.csv")
    a = ap.parse_args()
    keluar = folder(a.keluar)
    path_manual = folder(a.manual) if a.manual else keluar / "manual.csv"
    if not path_manual.exists():
        raise SystemExit(f"{path_manual} belum ada, formatnya lihat: python video_counting/validasi.py -h")
    with open(path_manual, newline="") as f:
        manual = list(csv.DictReader(f))
    cfg = yaml.safe_load(a.config.read_text())

    baris = []
    for t in cfg["titik"]:
        m = [r for r in manual if r["titik"] == t["id"]]
        if not m:
            continue
        hasil = bandingkan(m, baca_events(keluar / f"events_{t['id']}.csv"))
        for (g, arah, k), (man, oto) in sorted(hasil.items()):
            e = error(man, oto)
            target = TARGET.get(k)
            lulus = "" if target is None or e is None else ("ya" if e <= target else "tidak")
            baris.append({"titik": t["id"], "garis": g, "arah": arah, "kelas": k, "manual": round(man, 1),
                          "otomatis": oto, "error_persen": "" if e is None else round(100 * e, 1),
                          "target_persen": "" if target is None else round(100 * target), "lulus": lulus})

    with open(keluar / "validasi.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["titik", "garis", "arah", "kelas", "manual", "otomatis", "error_persen",
                               "target_persen", "lulus"])
        w.writeheader()
        w.writerows(baris)
    for b in baris:
        print(f"{b['titik']} {b['garis']} {b['arah']:8} {b['kelas']:5} manual {b['manual']:>6} "
              f"otomatis {b['otomatis']:>4} error {b['error_persen']}% {b['lulus']}")


if __name__ == "__main__":
    main()
