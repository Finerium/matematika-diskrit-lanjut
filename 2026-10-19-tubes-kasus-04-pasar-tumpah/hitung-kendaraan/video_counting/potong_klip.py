"""Potong klip untuk hitung manual (validasi): garis hitung dan panah arah digambar, ada penanda detik, bisa diperlambat.

  python video_counting/potong_klip.py --titik T1 --mulai 60 --durasi 120
  python video_counting/potong_klip.py --titik T1 --mulai 60 --durasi 120 --lambat 0.5 --video T1_20261101-061500.ts

Kotak deteksi YOLO sengaja tidak digambar supaya penghitung manual tidak terpengaruh hasil otomatis.
Detik di pojok kiri atas = detik dari awal file video, sama dengan kolom klip_mulai_detik di manual.csv.
Hasil: dokumentasi/validasi/klip_<titik>_<video>_<mulai>-<selesai>.mp4
"""
import argparse
from pathlib import Path

import yaml

from hitung import CONFIG, ROOT, daftar_video
from kalibrasi import gambar_garis


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--titik", required=True)
    ap.add_argument("--video", help="nama file bagian video, bawaan bagian pertama")
    ap.add_argument("--mulai", type=float, required=True, help="detik mulai klip")
    ap.add_argument("--durasi", type=float, default=120)
    ap.add_argument("--lambat", type=float, default=1.0, help="kecepatan putar, 0.5 = setengah kecepatan")
    a = ap.parse_args()

    import cv2
    cfg = yaml.safe_load(a.config.read_text())
    t = next((t for t in cfg["titik"] if t["id"] == a.titik), None)
    if t is None:
        raise SystemExit(f"titik {a.titik} tidak ada di config")
    video = next((v for v in daftar_video(t) if not a.video or v.name == a.video), None)
    if video is None:
        raise SystemExit(f"video {a.video or ''} titik {a.titik} tidak ketemu di {t['video']}")
    garis = [g for g in t.get("garis") or [] if g.get("koordinat")]

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    cap.set(cv2.CAP_PROP_POS_MSEC, a.mulai * 1000)
    keluar = ROOT / "dokumentasi" / "validasi"
    keluar.mkdir(parents=True, exist_ok=True)
    f = keluar / f"klip_{a.titik}_{video.stem}_{a.mulai:g}-{a.mulai + a.durasi:g}.mp4"
    tulis, n = None, 0
    while cap.grab():
        ok, img = cap.retrieve()
        detik = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if detik >= a.mulai + a.durasi:
            break
        if not ok or img is None or detik < a.mulai:
            continue
        for g in garis:
            gambar_garis(img, g["koordinat"], g.get("arah_dihitung"), f"{g['id']} {g['edge_model']}")
        cv2.rectangle(img, (0, 0), (170, 30), (0, 0, 0), -1)
        cv2.putText(img, f"detik {detik:7.1f}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if tulis is None:
            tulis = cv2.VideoWriter(str(f), cv2.VideoWriter_fourcc(*"mp4v"), fps * a.lambat,
                                    (img.shape[1], img.shape[0]))
        tulis.write(img)
        n += 1
    cap.release()
    if tulis is None:
        raise SystemExit("tidak ada frame di rentang itu")
    tulis.release()
    print(f"{f} ({n} frame, diputar {a.lambat:g}x)")


if __name__ == "__main__":
    main()
