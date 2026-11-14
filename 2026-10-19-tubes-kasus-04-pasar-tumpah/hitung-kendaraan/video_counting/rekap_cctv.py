"""Rekap satu hari rekaman CCTV (default Sabtu 14 Nov 2026 07.30-08.00, tanpa pasar tumpah).

1. salin events_*.csv + meta dari data/lapangan/cctv_14nov_sabtu ke hasil_hitung/cctv_14nov_sabtu
2. agregasi.py --keluar hasil_hitung/cctv_14nov_sabtu  (rekap.csv per 1 menit, jam_puncak.csv)
3. skr_per_jam kosong di rekap.csv diisi "menunggu ekr PKJI 2014"
4. ringkas_30menit_per_jam_cctv_14nov_sabtu.csv: per titik, garis, arah, kelas, kend/jam dari seluruh waktu bersih

Jalankan dari folder hitung-kendaraan: python video_counting/rekap_cctv.py [config] [lapangan] [hasil] [label]
Hasil cek kualitas per garis dibaca dari <hasil>/cek_<label>.json bila ada.
"""
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

P = Path(__file__).resolve().parents[1]   # folder hitung-kendaraan
sys.path.insert(0, str(P / "video_counting"))
import agregasi as ag  # noqa: E402

CONFIG = P / (sys.argv[1] if len(sys.argv) > 1 else "video_counting/config/cctv_14nov_sabtu.yaml")
LAPANGAN = P / (sys.argv[2] if len(sys.argv) > 2 else "data/lapangan/cctv_14nov_sabtu")
HASIL = P / (sys.argv[3] if len(sys.argv) > 3 else "hasil_hitung/cctv_14nov_sabtu")
LABEL = sys.argv[4] if len(sys.argv) > 4 else "cctv_14nov_sabtu"
MENUNGGU = "menunggu ekr PKJI 2014"
# hasil cek kualitas (diisi setelah melihat video anotasi). Kunci (titik, garis). Nilai: (dipakai, catatan)
CEK = json.loads((HASIL / f"cek_{LABEL}.json").read_text()) if (HASIL / f"cek_{LABEL}.json").exists() else {}

HASIL.mkdir(parents=True, exist_ok=True)
for f in sorted(LAPANGAN.glob("events_*")):
    shutil.copy2(f, HASIL / f.name)
subprocess.run([sys.executable, str(P / "video_counting/agregasi.py"), "--config", str(CONFIG), "--keluar", str(HASIL)],
               check=True, cwd=P)

with open(HASIL / "rekap.csv", newline="") as f:
    rows = list(csv.DictReader(f))
for r in rows:
    if r["skr_per_jam"] == "":
        r["skr_per_jam"] = MENUNGGU
with open(HASIL / "rekap.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ag.KOLOM)
    w.writeheader()
    w.writerows(rows)

cfg = yaml.safe_load(CONFIG.read_text())
ringkas = []
for t in cfg["titik"]:
    fe = HASIL / f"events_{t['id']}.csv"
    if not fe.exists():
        continue
    meta = json.loads(fe.with_suffix(".meta.json").read_text())
    rentang = ag.rentang_valid(meta["bagian"])
    detik = sum((z - a).total_seconds() for a, z in rentang)
    events = ag.baca_events(fe)
    lengkap = all(t["ekr"].get(k) is not None for k in ("KR", "SM", "KB"))
    for g in meta["garis"]:
        for arah in sorted(("negatif", "positif"), key=lambda a: a != g["arah_dihitung"]):  # searah dulu
            n = dict.fromkeys(ag.KELAS, 0)
            for e in events:
                if e["garis"] == g["id"] and e["arah"] == arah and e["kamera_geser"] != "ya" and e["kelas_pkji"] in n:
                    n[e["kelas_pkji"]] += 1
            ya = arah == g["arah_dihitung"]
            dipakai, catatan = CEK.get(f"{t['id']}/{g['id']}", ["belum dicek", ""])
            ringkas.append({
                "titik": t["id"], "garis": g["id"], "edge_model": g["edge_model"], "arah": arah,
                "searah_edge": "ya" if ya else "tidak",
                "mulai": rentang[0][0].isoformat(timespec="seconds"), "selesai": rentang[-1][1].isoformat(timespec="seconds"),
                "detik_bersih": round(detik, 1),
                "detik_kamera_geser": round(sum(z - a for b in meta["bagian"] for a, z in b["kamera_geser"]), 1),
                **n, "kend": n["KR"] + n["SM"] + n["KB"],
                **{f"{k}_per_jam": round(n[k] * 3600 / detik, 1) for k in ag.KELAS},
                "kend_per_jam": round((n["KR"] + n["SM"] + n["KB"]) * 3600 / detik, 1),
                "skr_per_jam": round(sum(n[k] * t["ekr"][k] for k in ("KR", "SM", "KB")) * 3600 / detik, 1) if lengkap else MENUNGGU,
                "dipakai_sebagai_arus_edge": dipakai if ya else "tidak (arah lawan, bukan edge di graf)",
                "catatan": catatan if ya else "",
                "sumber": str(fe.relative_to(P)),
            })
with open(HASIL / f"ringkas_30menit_per_jam_{LABEL}.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(ringkas[0]))
    w.writeheader()
    w.writerows(ringkas)
for x in ringkas:
    print(x["titik"], x["garis"], x["edge_model"], x["arah"], x["searah_edge"], x["detik_bersih"], x["kend"], x["kend_per_jam"],
          x["dipakai_sebagai_arus_edge"])
