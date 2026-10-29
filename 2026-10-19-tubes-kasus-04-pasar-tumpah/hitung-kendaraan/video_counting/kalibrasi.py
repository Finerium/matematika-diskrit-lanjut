"""Pasang satu garis hitung (satu edge) di satu titik, lalu simpan ke config. Komentar di config tetap utuh.

Mode klik (perlu layar):
  python video_counting/kalibrasi.py --titik T1 --garis L1
  klik 1 dan 2 = ujung garis, klik 3 = sisi tempat kendaraan DATANG untuk arah edge itu,
  s = simpan, r = ulang, q = batal

Mode tanpa klik:
  python video_counting/kalibrasi.py --titik T1 --frame cek_T1.jpg
      simpan satu frame (plus semua garis yang sudah ada, dengan panah arah datang) untuk dicek atau untuk membaca
      koordinat piksel di aplikasi gambar apa saja; frame diberi kisi koordinat tiap 50 piksel
  python video_counting/kalibrasi.py --titik T1 --frame cek_T1.jpg --lintasan 60
      sama, ditambah jejak kendaraan selama 60 detik pertama (warna = arah gerak), supaya lajur dan arah arus
      kelihatan jelas sebelum memasang garis. Garis paling baik dipasang tegak lurus jejak, di bagian yang jejaknya
      rapat tapi tidak saling tumpang tindih.
  python video_counting/kalibrasi.py --titik T1 --garis L1 --koordinat 412 690 1530 655 --datang 960 900

Frame diambil dari bagian video pertama titik itu pada detik ke-2 (--detik), karena frame paling awal rekaman CCTV
sering rusak (stream belum dapat keyframe).
"""
import argparse
import json
import math
from pathlib import Path

import yaml

from hitung import CONFIG, ROOT, daftar_video, pilih_device, sisi


def ambil_frame(video, detik):
    import cv2
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, detik * 1000)
    ok, img = cap.read()
    if not ok:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, img = cap.read()
    cap.release()
    if not ok:
        raise SystemExit(f"video tidak bisa dibaca: {video}")
    return img


def gambar_garis(img, koordinat, arah=None, label="", datang=None):
    """Garis kuning; panah merah dari sisi kendaraan datang menuju garis."""
    import cv2
    a, b = [tuple(map(int, p)) for p in koordinat]
    cv2.line(img, a, b, (0, 255, 255), 2)
    if label:
        cv2.putText(img, label, (a[0] + 4, a[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    if arah:
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        tanda = 1 if arah == "positif" else -1  # sisi positif ada di arah normal (-dy, dx)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        asal = (int(mx - tanda * dy / n * 45), int(my + tanda * dx / n * 45))
        cv2.arrowedLine(img, asal, (int(mx), int(my)), (0, 0, 255), 2, tipLength=0.3)
    if datang:
        cv2.circle(img, tuple(map(int, datang)), 7, (0, 0, 255), -1)


def kisi(img, jarak=50):
    import cv2
    h, w = img.shape[:2]
    for x in range(0, w, jarak):
        cv2.line(img, (x, 0), (x, h), (110, 110, 110), 1)
        cv2.putText(img, str(x), (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    for y in range(0, h, jarak):
        cv2.line(img, (0, y), (w, y), (110, 110, 110), 1)
        cv2.putText(img, str(y), (2, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)


def lintasan(img, video, cfg, detik):
    """Gambar jejak titik acuan (tengah sisi bawah kotak) tiap kendaraan selama `detik` detik pertama."""
    import cv2
    import numpy as np
    from ultralytics import YOLO
    m, device = cfg["model"], pilih_device("auto")
    model, jejak = YOLO(str(ROOT / "models" / m["bobot"])), {}
    cap = cv2.VideoCapture(str(video))
    while cap.grab():
        ok, frame = cap.retrieve()
        if cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 > detik:
            break
        if not ok or frame is None:
            continue
        b = model.track(frame, persist=True, tracker=m["tracker"], classes=m["kelas"], conf=m["conf"],
                        imgsz=m["imgsz"], device=device, verbose=False)[0].boxes
        if b.id is not None:
            for i, (x1, _, x2, y2) in zip(b.id.int().tolist(), b.xyxy.tolist()):
                jejak.setdefault(i, []).append((int((x1 + x2) / 2), int(y2)))
    cap.release()
    lapis = img.copy()
    for pts in jejak.values():
        if len(pts) < 5 or math.dist(pts[0], pts[-1]) < 20:
            continue  # diam atau terlalu pendek
        sudut = math.degrees(math.atan2(pts[-1][1] - pts[0][1], pts[-1][0] - pts[0][0])) % 360
        warna = cv2.cvtColor(np.uint8([[[int(sudut / 2), 255, 255]]]), cv2.COLOR_HSV2BGR)[0, 0].tolist()
        cv2.polylines(lapis, [np.int32(pts)], False, warna, 2)
        cv2.arrowedLine(lapis, pts[-2], pts[-1], warna, 2, tipLength=2)
    cv2.addWeighted(lapis, 0.8, img, 0.2, 0, img)
    return len(jejak)


def klik(img):
    import cv2
    titik = []

    def cb(ev, x, y, *_):
        if ev == cv2.EVENT_LBUTTONDOWN and len(titik) < 3:
            titik.append((x, y))

    cv2.namedWindow("kalibrasi", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("kalibrasi", cb)
    while True:
        tampil = img.copy()
        for p in titik:
            cv2.circle(tampil, p, 5, (0, 255, 255), -1)
        if len(titik) >= 2:
            gambar_garis(tampil, titik[:2], datang=titik[2] if len(titik) == 3 else None)
        cv2.imshow("kalibrasi", tampil)
        k = cv2.waitKey(30) & 0xFF
        if k == ord("r"):
            titik.clear()
        elif k == ord("q"):
            raise SystemExit("batal, config tidak diubah")
        elif k == ord("s") and len(titik) == 3:
            break
    cv2.destroyAllWindows()
    return titik[:2], titik[2]


def lebar(b):
    return len(b) - len(b.lstrip())


def nilai(b):
    return b.split(":", 1)[1].split("#")[0].strip().strip("\"'")


def blok(baris, mulai, akhir, indent, nama):
    """Rentang baris [i, j) milik entri '- id: nama' dengan indentasi tertentu."""
    i = next((k for k in range(mulai, akhir) if baris[k].strip().startswith("- id:") and lebar(baris[k]) == indent
              and nilai(baris[k]) == nama), None)
    if i is None:
        return None
    j = next((k for k in range(i + 1, akhir) if baris[k].strip() and lebar(baris[k]) <= indent), akhir)
    return i, j


def simpan(path, tid, gid, koordinat, arah):
    """Ganti baris koordinat dan arah_dihitung milik garis gid di titik tid. Baris lain tidak disentuh."""
    baris = path.read_text().splitlines(keepends=True)
    t0 = next(k for k, b in enumerate(baris) if b.rstrip() == "titik:")
    bt = blok(baris, t0, len(baris), next(lebar(b) for b in baris[t0:] if b.strip().startswith("- id:")), tid)
    if bt is None:
        raise SystemExit(f"titik {tid} tidak ada di {path.name}")
    g0 = next((k for k in range(*bt) if baris[k].strip() == "garis:"), None)
    ind = next((lebar(baris[k]) for k in range(g0, bt[1]) if baris[k].strip().startswith("- id:")), None) if g0 else None
    bg = blok(baris, g0, bt[1], ind, gid) if ind is not None else None
    if bg is None:
        raise SystemExit(f"garis {gid} tidak ada di titik {tid}, tambahkan dulu di config")
    diganti = 0
    for k in range(*bg):
        isi = baris[k].strip()
        if isi.startswith(("koordinat:", "arah_dihitung:")):
            kunci = isi.split(":", 1)[0]
            v = json.dumps([[round(x) for x in p] for p in koordinat]) if kunci == "koordinat" else arah
            komentar = "  # " + baris[k].split("#", 1)[1].strip() if "#" in baris[k] else ""
            baris[k] = f"{' ' * lebar(baris[k])}{kunci}: {v}{komentar}\n"
            diganti += 1
    if diganti != 2:
        raise SystemExit(f"kunci koordinat/arah_dihitung di garis {gid} titik {tid} tidak lengkap")
    path.write_text("".join(baris))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--titik", required=True)
    ap.add_argument("--garis", help="id garis di titik itu, bawaan garis pertama")
    ap.add_argument("--frame", type=Path, help="simpan frame + garis yang sudah ada ke gambar ini lalu selesai")
    ap.add_argument("--detik", type=float, default=2.0, help="detik ke berapa frame diambil")
    ap.add_argument("--lintasan", type=float, metavar="DETIK", help="gambar jejak kendaraan selama N detik pertama")
    ap.add_argument("--koordinat", type=float, nargs=4, metavar=("X1", "Y1", "X2", "Y2"))
    ap.add_argument("--datang", type=float, nargs=2, metavar=("X", "Y"), help="titik di sisi kendaraan datang")
    a = ap.parse_args()

    cfg = yaml.safe_load(a.config.read_text())
    t = next((t for t in cfg["titik"] if t["id"] == a.titik), None)
    if t is None:
        raise SystemExit(f"titik {a.titik} tidak ada di config")
    video = next(iter(daftar_video(t)), None)
    if video is None:
        raise SystemExit(f"{a.titik}: belum ada video di {t['video']}")

    if a.frame:
        import cv2
        img = ambil_frame(video, a.detik)
        if a.lintasan:
            print(f"{lintasan(img, video, cfg, a.lintasan)} track dalam {a.lintasan:g} detik pertama")
        kisi(img)
        for g in t.get("garis") or []:
            if g.get("koordinat"):
                gambar_garis(img, g["koordinat"], g.get("arah_dihitung"), f"{g['id']} {g['edge_model']}")
        cv2.imwrite(str(a.frame), img)
        print(f"{a.frame} ({img.shape[1]} x {img.shape[0]} piksel, dari {video.name})")
        return
    gid = a.garis or (t.get("garis") or [{}])[0].get("id")
    if not gid:
        raise SystemExit(f"titik {a.titik} belum punya daftar garis di config")
    if a.koordinat:
        if not a.datang:
            raise SystemExit("--koordinat harus disertai --datang")
        koordinat, datang = [a.koordinat[:2], a.koordinat[2:]], a.datang
    else:
        koordinat, datang = klik(ambil_frame(video, a.detik))

    s = sisi(koordinat[0], koordinat[1], datang)
    if s == 0:
        raise SystemExit("titik datang tepat di garis, pilih titik lain")
    arah = "positif" if s > 0 else "negatif"
    simpan(a.config, a.titik, gid, koordinat, arah)
    print(f"{a.titik} {gid}: koordinat {[[round(x) for x in p] for p in koordinat]}, arah_dihitung {arah}")


if __name__ == "__main__":
    main()
