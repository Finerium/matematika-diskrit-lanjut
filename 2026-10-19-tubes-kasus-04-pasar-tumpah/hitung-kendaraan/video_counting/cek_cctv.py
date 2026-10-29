"""Cek CCTV sebelum merekam: hidup atau mati, resolusi, fps, dan satu frame untuk mengecek sudut kamera.

  python video_counting/cek_cctv.py                      # semua titik CCTV di config
  python video_counting/cek_cctv.py --alternatif 400     # plus CCTV lain dalam radius 400 m dari tiap titik

Hasil di dokumentasi/cek_cctv/<tanggal-jam>_<nama config>/: cek_cctv.csv, frame per CCTV, dan lembar_cctv.jpg (semua frame
dalam satu gambar). Jalankan beberapa menit sebelum rekam_cctv.py, karena CCTV taman (DPKP3) dan Dishub
kadang mati.
"""
import argparse
import csv
import json
import math
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import yaml

from hitung import CONFIG, ROOT
from rekam_cctv import HEADER

API = "https://pelindung.bandung.go.id:8443/api/cek"


def ambil(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                               "Referer": "https://pelindung.bandung.go.id/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def cek(url, foto):
    """Status stream dan satu frame. Frame diambil 1 detik setelah stream terbuka supaya tidak rusak."""
    try:
        ambil(url)
    except Exception as e:
        return {"status": f"mati ({getattr(e, 'code', type(e).__name__)})"}
    out = subprocess.run(["ffprobe", "-v", "quiet", "-rw_timeout", "15000000", *HEADER, "-select_streams", "v:0",
                          "-show_entries", "stream=codec_name,width,height,avg_frame_rate", "-of", "json", url],
                         capture_output=True, text=True).stdout
    s = (json.loads(out or "{}").get("streams") or [{}])[0]
    subprocess.run(["ffmpeg", "-v", "quiet", "-rw_timeout", "15000000", *HEADER, "-live_start_index", "-1", "-i", url,
                    "-ss", "1", "-frames:v", "1", "-y", str(foto)], capture_output=True)
    a, b = (s.get("avg_frame_rate") or "0/1").split("/")
    return {"status": "hidup" if foto.exists() else "hidup, frame gagal", "codec": s.get("codec_name", ""),
            "resolusi": f"{s.get('width')}x{s.get('height')}" if s.get("width") else "",
            "fps": round(int(a) / int(b), 1) if int(b) else ""}


def jarak(p, q):
    return 6371000 * math.hypot(math.radians(q[0] - p[0]), math.radians(q[1] - p[1]) * math.cos(math.radians(p[0])))


def lembar(baris, folder):
    import cv2
    import numpy as np
    ubin = []
    for b in baris:
        img = cv2.imread(str(folder / b["foto"])) if b.get("foto") else None
        img = cv2.resize(img, (400, 270)) if img is not None else np.zeros((270, 400, 3), np.uint8)
        cv2.rectangle(img, (0, 0), (400, 22), (0, 0, 0), -1)
        cv2.putText(img, f"{b['titik']}: {b['cctv'][:30]}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        if b["status"] != "hidup":
            cv2.putText(img, b["status"], (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        ubin.append(img)
    while len(ubin) % 4:
        ubin.append(np.zeros_like(ubin[0]))
    cv2.imwrite(str(folder / "lembar_cctv.jpg"), np.vstack([np.hstack(ubin[i:i + 4]) for i in range(0, len(ubin), 4)]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--alternatif", type=float, metavar="METER", help="cari juga CCTV lain dalam radius ini")
    a = ap.parse_args()
    cfg = yaml.safe_load(a.config.read_text())
    daftar = [(t["id"], t["cctv"]["nama"], t["cctv"]["url"], "") for t in cfg["titik"] if t.get("cctv")]
    if a.alternatif:
        semua = [x for x in json.loads(ambil(API)) if x["lat"] and x["lng"]]
        posisi = {x["stream_cctv"]: (float(x["lat"]), float(x["lng"])) for x in semua}
        dipakai = {u for _, _, u, _ in daftar}
        for tid, _, url, _ in list(daftar):
            if url not in posisi:
                continue
            for x in semua:
                j = jarak(posisi[url], (float(x["lat"]), float(x["lng"])))
                if x["stream_cctv"] not in dipakai and j <= a.alternatif:
                    daftar.append((f"{tid} (alternatif)", x["cctv_name"].strip(), x["stream_cctv"], round(j)))
                    dipakai.add(x["stream_cctv"])

    folder = ROOT / "dokumentasi" / "cek_cctv" / f"{datetime.now():%Y%m%d-%H%M}_{a.config.stem}"
    folder.mkdir(parents=True, exist_ok=True)

    def satu(i_item):
        i, (tid, nama, url, j) = i_item
        foto = folder / f"{i:02d}_{tid.split()[0]}.jpg"
        return {"titik": tid, "cctv": nama, "jarak_m": j, "url": url, **cek(url, foto),
                "foto": foto.name if foto.exists() else ""}

    with ThreadPoolExecutor(8) as ex:
        baris = list(ex.map(satu, enumerate(daftar)))
    with open(folder / "cek_cctv.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["titik", "cctv", "jarak_m", "status", "codec", "resolusi", "fps", "url", "foto"])
        w.writeheader()
        w.writerows(baris)
    lembar(baris, folder)
    for b in baris:
        print(f"{b['titik']:32} {b['cctv'][:34]:34} {b['status']:14} {b.get('resolusi', ''):9} {b.get('fps', '')}")
    print(folder)


if __name__ == "__main__":
    main()
