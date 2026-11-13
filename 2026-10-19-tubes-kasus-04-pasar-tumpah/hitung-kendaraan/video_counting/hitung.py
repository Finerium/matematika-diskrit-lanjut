"""Deteksi + tracking + lintasan garis untuk titik-titik di config.

Hasil per titik di folder keluaran (bawaan data/lapangan/):
  events_<titik>.csv        satu baris per kendaraan yang melintas salah satu garis hitung
  events_<titik>.meta.json  model, tracker, versi ultralytics, garis, dan daftar bagian video (jam mulai, fps,
                            durasi, rentang waktu saat kamera bergeser)
  anotasi_<bagian>.mp4      video beranotasi, hanya kalau pakai --anotasi

Contoh:
  python video_counting/hitung.py --titik T1
  python video_counting/hitung.py --titik T1 --detik 60 --anotasi                 # uji 1 menit dulu
  python video_counting/hitung.py --titik T1 --bobot yolo26m.pt --keluar data/uji/m
"""
import argparse
import csv
import glob
import json
import math
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "video_counting" / "config" / "titik_hitung.yaml"
KELUAR = ROOT / "data" / "lapangan"
NAMA_COCO = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PKJI = {1: "KTB", 2: "KR", 3: "SM", 5: "KB", 7: "KB"}
KOLOM = ["video", "titik", "garis", "edge_model", "track_id", "frame", "detik", "waktu", "kelas_coco", "kelas_pkji",
         "arah", "conf_rata", "kamera_geser"]


def iou(a, b):
    """Intersection over union dua kotak (x1, y1, x2, y2)."""
    w, h = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    irisan = w * h
    return irisan / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - irisan)


def sisi(a, b, p):
    """Tanda cross product (b - a) x (p - a): 1, -1, atau 0 kalau p tepat di garis."""
    c = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    return (c > 0) - (c < 0)


class PenghitungGaris:
    """Lintasan satu garis untuk semua track. Satu track_id paling banyak menghasilkan satu event.

    Lintasan dihitung saat tanda jarak titik acuan ke garis berbalik, asal sebelumnya kendaraan pernah berada cukup
    jauh di sisi asal: paling sedikit `kedalaman` x tinggi kotaknya. Kendaraan yang benar-benar lewat selalu datang
    dari jauh, sedangkan kotak kendaraan yang diam di garis (bus macet) hanya bergoyang beberapa piksel di sekitar
    garis, jadi tidak terhitung. Di sisi tujuan tidak ada syarat jarak, karena kendaraan yang menjauhi kamera sering
    hilang dari tracking sesaat setelah melewati garis.
    """

    def __init__(self, garis, min_frame_track, kedalaman=0.0):
        self.a, self.b = [tuple(p) for p in garis]
        self.min_frame, self.kedalaman = min_frame_track, kedalaman
        self.panjang = math.dist(self.a, self.b) or 1.0
        self.track = {}

    def update(self, tid, frame, titik, kelas, conf, tinggi=0.0):
        t = self.track.setdefault(tid, {"n": 0, "kelas": Counter(), "conf": 0.0, "akhir": None, "lintas": None,
                                        "dalam": {1: 0.0, -1: 0.0}})
        t["n"] += 1
        t["kelas"][kelas] += 1
        t["conf"] += conf
        a, b = self.a, self.b
        jarak = ((b[0] - a[0]) * (titik[1] - a[1]) - (b[1] - a[1]) * (titik[0] - a[0])) / self.panjang
        if jarak == 0:
            return  # tepat di atas garis, tunggu frame berikutnya
        s = 1 if jarak > 0 else -1
        if t["akhir"] and t["lintas"] is None:
            p, s_lama = t["akhir"]
            # tanda berubah, titik potongnya ada di dalam segmen garis (bukan di perpanjangannya), dan sebelumnya
            # kendaraan pernah cukup jauh di sisi asal
            if (s_lama != s and sisi(p, titik, self.a) * sisi(p, titik, self.b) <= 0
                    and t["dalam"][s_lama] >= self.kedalaman * tinggi):
                t["lintas"] = (frame, "positif" if s_lama > 0 else "negatif")
        t["dalam"][s] = max(t["dalam"][s], abs(jarak))
        t["akhir"] = (titik, s)

    def buang_ganda(self, kotak, frame, iou_min):
        """Satu kendaraan kadang dapat dua kotak sekaligus (angkot car + truck, motor dekat kamera) yang dua-duanya
        melintas. Track yang melintas di frame ini ditandai ganda kalau kotaknya bertumpuk (IoU >= iou_min) dengan
        kotak track lain di frame yang sama yang sudah melintas ke arah yang sama. kotak = {track_id: (x1, y1, x2, y2)}."""
        for tid, k in kotak.items():
            t = self.track.get(tid)
            if not t or not t["lintas"] or t["lintas"][0] != frame:
                continue
            for tid2, k2 in kotak.items():
                t2 = self.track.get(tid2)
                if (tid2 != tid and t2 and t2["lintas"] and t2["lintas"][1] == t["lintas"][1]
                        and not t2.get("ganda") and iou(k, k2) >= iou_min):
                    t["ganda"] = True
                    break

    def jumlah(self):
        return Counter(t["lintas"][1] for t in self.track.values() if t["lintas"] and not t.get("ganda"))

    def events(self):
        """Track pendek dan lintasan ganda dibuang. Kelas track = kelas yang paling sering muncul selama track hidup."""
        hasil = []
        for tid, t in self.track.items():
            if t["lintas"] and t["n"] >= self.min_frame and not t.get("ganda"):
                hasil.append({"track_id": tid, "frame": t["lintas"][0], "kelas": t["kelas"].most_common(1)[0][0],
                              "arah": t["lintas"][1], "conf_rata": round(t["conf"] / t["n"], 3)})
        return sorted(hasil, key=lambda e: e["frame"])


class PenjagaKamera:
    """Tandai waktu saat kamera bergeser dari posisi awal (PTZ diputar, kamera kesenggol, siaran mati).

    Acuan = median 5 frame pertama (sekali per detik), jadi kendaraan yang lewat dan frame awal stream yang rusak
    tidak ikut jadi acuan. Setelah itu sekali per detik titik fitur ORB frame sekarang dicocokkan ke acuan, lalu
    transformasi geser + putar + skala diestimasi dengan RANSAC. Kendaraan yang lewat jadi outlier dan tidak
    memengaruhi estimasi. Kamera dianggap bergeser kalau pergeseran > ambang_px, skala berubah > ambang_skala, atau
    titik yang cocok < min_inlier (gambar berubah total atau siaran gelap), `berturut` kali berturut-turut.
    Ambang dipilih dari rekaman CCTV asli, lihat dokumentasi/Laporan_Uji.
    """

    LEBAR = 640

    def __init__(self, ambang_px=8.0, ambang_skala=0.03, min_inlier=15, berturut=3, pemanasan=5):
        self.ambang_px, self.ambang_skala, self.min_inlier = ambang_px, ambang_skala, min_inlier
        self.berturut, self.pemanasan = berturut, pemanasan
        self.acuan, self.awal = None, []
        self.cek_list = []  # (detik, geser, inlier, pergeseran_px)

    def _abu(self, img):
        import cv2
        s = self.LEBAR / img.shape[1]
        return cv2.cvtColor(cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)

    def cek(self, img, detik):
        import cv2
        import numpy as np
        g = self._abu(img)
        if self.acuan is None:
            self.awal.append(g)
            self.cek_list.append((detik, False, None, 0.0))
            if len(self.awal) == self.pemanasan:
                self.orb = cv2.ORB_create(1500)
                self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
                self.acuan = self.orb.detectAndCompute(np.median(np.stack(self.awal), axis=0).astype(np.uint8), None)
            return
        kp, des = self.orb.detectAndCompute(g, None)
        inlier, geser_px, geser = 0, 0.0, True
        if des is not None and self.acuan[1] is not None and len(kp) >= 10:
            cocok = [m for m, n in (x for x in self.bf.knnMatch(self.acuan[1], des, k=2) if len(x) == 2)
                     if m.distance < 0.75 * n.distance]
            if len(cocok) >= 6:
                a = np.float32([self.acuan[0][m.queryIdx].pt for m in cocok])
                b = np.float32([kp[m.trainIdx].pt for m in cocok])
                M, mask = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=3.0)
                if M is not None:
                    inlier = int(mask.sum())
                    geser_px = math.hypot(M[0, 2], M[1, 2])
                    skala = math.hypot(M[0, 0], M[1, 0])
                    geser = (inlier < self.min_inlier or geser_px > self.ambang_px
                             or abs(skala - 1) > self.ambang_skala)
        self.cek_list.append((detik, geser, inlier, round(geser_px, 2)))

    def geser_sekarang(self):
        akhir = self.cek_list[-self.berturut:]
        return len(akhir) == self.berturut and all(c[1] for c in akhir)

    def rentang(self):
        """Daftar [mulai, selesai] dalam detik video saat kamera bergeser."""
        hasil, run = [], []
        for c in self.cek_list + [(None, False, 0, 0)]:
            if c[1]:
                run.append(c[0])
                continue
            if len(run) >= self.berturut:
                hasil.append([round(run[0], 2), round(run[-1] + 1, 2)])
            run = []
        return hasil


class IkutKamera:
    """Untuk video HP yang dipegang tangan: posisi jalan di gambar berubah terus, jadi garis yang diam tidak bisa
    dipakai. Tiap frame dicocokkan ke frame acuan (frame kalibrasi.py, bawaan detik ke-2) dengan titik fitur ORB +
    RANSAC seperti PenjagaKamera, tapi hasilnya homografi penuh (geser, putar, zoom, miring). Titik kendaraan lalu
    dipindah ke koordinat frame acuan sebelum dicek ke garis, jadi garis cukup dipasang sekali di frame acuan.
    Frame yang tidak cocok (kamera menoleh jauh, gambar kabur) dilewati dan dicatat sebagai kamera_geser.
    """

    LEBAR = 640

    def __init__(self, acuan, min_inlier=40):
        import cv2
        self.s = self.LEBAR / acuan.shape[1]
        self.orb, self.bf = cv2.ORB_create(3000), cv2.BFMatcher(cv2.NORM_HAMMING)
        self.acuan = self.orb.detectAndCompute(self._abu(acuan), None)
        self.min_inlier = min_inlier
        self.gagal = []  # detik tiap frame yang tidak cocok ke acuan

    def _abu(self, img):
        import cv2
        return cv2.cvtColor(cv2.resize(img, None, fx=self.s, fy=self.s, interpolation=cv2.INTER_AREA),
                            cv2.COLOR_BGR2GRAY)

    def ke_acuan(self, img, detik):
        """Homografi 3x3 dari piksel frame ini ke piksel frame acuan, None kalau tidak cocok."""
        import cv2
        import numpy as np
        H = None
        kp, des = self.orb.detectAndCompute(self._abu(img), None)
        if des is not None and len(kp) >= self.min_inlier:
            cocok = [m for m, n in (x for x in self.bf.knnMatch(des, self.acuan[1], k=2) if len(x) == 2)
                     if m.distance < 0.75 * n.distance]
            if len(cocok) >= self.min_inlier:
                a = np.float32([kp[m.queryIdx].pt for m in cocok])
                b = np.float32([self.acuan[0][m.trainIdx].pt for m in cocok])
                H, mask = cv2.findHomography(a, b, cv2.RANSAC, 3.0)
                # inlier sedikit atau skala tidak masuk akal (hasil cocok yang salah) dianggap gagal
                if H is None or mask.sum() < self.min_inlier or not 0.5 < abs(np.linalg.det(H[:2, :2])) < 2:
                    H = None
        if H is None:
            self.gagal.append(detik)
            return None
        S = np.diag([self.s, self.s, 1.0])
        return np.linalg.inv(S) @ H @ S

    def rentang(self, jeda=1.0):
        """[mulai, selesai] saat frame tidak cocok ke acuan; kegagalan yang jaraknya < jeda detik digabung."""
        hasil = []
        for d in self.gagal:
            if hasil and d - hasil[-1][1] < jeda:
                hasil[-1][1] = d
            else:
                hasil.append([d, d])
        return [[round(a, 2), round(z + 1 / 30, 2)] for a, z in hasil]


def pindah(H, titik):
    """Pindahkan daftar titik (x, y) dengan homografi H."""
    import numpy as np
    p = np.c_[np.float64(titik), np.ones(len(titik))] @ H.T
    return p[:, :2] / p[:, 2:]


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


def daftar_video(titik):
    # glob.glob, bukan ROOT.glob: video HP ditulis sebagai path absolut (~/Downloads) dan pathlib menolak pola absolut
    return sorted(Path(p) for p in glob.glob(str(ROOT / Path(titik["video"]).expanduser())))


def info_video(video, titik):
    """Jam mulai, fps, dan ukuran. Video dari rekam_cctv.py punya file .json berisi jam mulai dan jumlah frame asli,
    jadi fps-nya fps efektif (frame / durasi), bukan angka di header yang bisa beda untuk stream CCTV."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"video tidak bisa dibuka: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    ukuran = [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]
    cap.release()
    sidecar = video.with_suffix(".json")
    if sidecar.exists():
        s = json.loads(sidecar.read_text())
        mulai = s["mulai"]
        if s.get("frame") and s.get("durasi_detik"):
            fps = s["frame"] / s["durasi_detik"]
    else:
        mulai = titik.get("mulai")
        if not mulai:
            raise SystemExit(f"{video.name}: jam mulai tidak ada, isi `mulai` di config")
    return datetime.fromisoformat(mulai), fps, ukuran


def garis_siap(titik):
    g = [x for x in titik.get("garis") or [] if x.get("koordinat") and x.get("arah_dihitung")]
    if not g:
        raise SystemExit(f"{titik['id']}: belum ada garis yang dikalibrasi, jalankan kalibrasi.py dulu")
    return g


def pilih_device(pilihan):
    if pilihan != "auto":
        return int(pilihan) if pilihan.isdigit() else pilihan
    import torch
    if torch.cuda.is_available():
        return 0
    return "mps" if torch.backends.mps.is_available() else "cpu"


def gambar(r, garis, penghitung, geser, H_balik=None):
    """H_balik (titik ikut_kamera): homografi frame acuan -> frame ini, supaya garis digambar menempel di jalan."""
    import cv2
    img = r.plot(line_width=1)
    for i, g in enumerate(garis):
        k = g["koordinat"] if H_balik is None else pindah(H_balik, g["koordinat"])
        a, b = [tuple(map(int, p)) for p in k]
        cv2.line(img, a, b, (0, 255, 255), 2)
        cv2.putText(img, g["id"], (a[0] + 4, a[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        n = penghitung[g["id"]].jumlah()
        lawan = "negatif" if g["arah_dihitung"] == "positif" else "positif"
        teks = f"{g['id']} searah {n.get(g['arah_dihitung'], 0)}  lawan {n.get(lawan, 0)}"
        cv2.putText(img, teks, (10, 28 + 26 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
        cv2.putText(img, teks, (10, 28 + 26 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    if geser:
        cv2.putText(img, "KAMERA BERGESER", (10, img.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
    return img


def proses(cfg, titik, device, detik, anotasi, bobot, keluar, imgsz=None, simpan_jejak=False):
    import cv2
    import numpy as np
    import ultralytics
    from ultralytics import YOLO

    tid, m = titik["id"], cfg["model"]
    garis = garis_siap(titik)
    bobot, imgsz = bobot or m["bobot"], imgsz or titik.get("imgsz") or m["imgsz"]
    keluar.mkdir(parents=True, exist_ok=True)
    baris, bagian, total_frame, t0 = [], [], 0, time.time()
    jejak = None
    if simpan_jejak:  # kotak tiap track tiap frame, untuk verifikasi dan mencari penyebab kendaraan terlewat
        f_jejak = open(keluar / f"jejak_{tid}.csv", "w", newline="")
        jejak = csv.writer(f_jejak)
        jejak.writerow(["video", "frame", "detik", "track_id", "kelas_coco", "conf", "x1", "y1", "x2", "y2"])

    for video in daftar_video(titik):
        mulai, fps, ukuran = info_video(video, titik)
        penghitung = {g["id"]: PenghitungGaris(g["koordinat"], m["min_frame_track"], m.get("kedalaman_asal", 0.2))
                      for g in garis}
        jaga = PenjagaKamera()
        ikut = IkutKamera(ambil_frame(video, titik["ikut_kamera"])) if titik.get("ikut_kamera") is not None else None
        terlihat = Counter()  # detik tiap garis tampak di gambar, dibobot bagian garis yang masuk (titik ikut_kamera)
        model = YOLO(str(ROOT / "models" / bobot))  # model baru tiap bagian supaya tracker mulai dari nol
        tulis = None
        if anotasi:
            tulis = cv2.VideoWriter(str(keluar / f"anotasi_{video.stem}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                    fps, tuple(ukuran))
        # Frame dibaca sendiri (bukan model.track(source=video)): loader Ultralytics berhenti di jumlah frame
        # menurut header file, yang untuk rekaman stream CCTV cuma perkiraan, dan pindah file kalau satu frame gagal
        # didecode. Di sini frame rusak cukup dilewati, dan waktu tiap frame diambil dari timestamp aslinya.
        cap = cv2.VideoCapture(str(video))
        waktu_frame, rusak, cek_berikut, t_bagian = [], 0, 0.0, time.time()
        while cap.grab():
            ok, img = cap.retrieve()
            t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if not ok or img is None:
                rusak += 1
                continue
            if waktu_frame and t <= waktu_frame[-1]:
                t = waktu_frame[-1] + 1 / fps  # timestamp tidak naik (jarang, di stream rusak), pakai fps
            if detik and t > detik:
                break
            frame = len(waktu_frame)
            waktu_frame.append(t)
            if t >= cek_berikut and titik.get("cek_kamera", True):
                jaga.cek(img, t)
                cek_berikut = t + 1
            H = H_balik = None
            if ikut:
                H = ikut.ke_acuan(img, t)
                if H is not None:
                    H_balik = np.linalg.inv(H)
                    for g in garis:  # bagian garis yang masuk gambar, dari 11 titik sepanjang garis
                        p = pindah(H_balik, np.linspace(*g["koordinat"], 11))
                        terlihat[g["id"]] += ((p >= 0) & (p <= ukuran)).all(axis=1).mean() / fps
            r = model.track(img, persist=True, tracker=m["tracker"], classes=m["kelas"], conf=m["conf"],
                            imgsz=imgsz, device=device, agnostic_nms=m.get("agnostic_nms", False), verbose=False)[0]
            b = r.boxes
            if b.id is not None:
                for k_id, k, (x1, y1, x2, y2), c in zip(b.id.int().tolist(), b.cls.int().tolist(), b.xyxy.tolist(),
                                                        b.conf.tolist()):
                    kaki, tinggi = ((x1 + x2) / 2, y2), y2 - y1  # acuan = tengah sisi bawah kotak
                    if H is not None:  # pindah ke koordinat frame acuan
                        kaki, atas = pindah(H, [kaki, ((x1 + x2) / 2, y1)]).tolist()  # float biasa, bukan numpy
                        kaki, tinggi = tuple(kaki), kaki[1] - atas[1]
                    if not ikut or H is not None:  # frame yang tidak cocok ke acuan dilewati
                        for p in penghitung.values():
                            p.update(k_id, frame, kaki, k, c, tinggi)
                    if jejak:
                        jejak.writerow([video.name, frame, round(t, 3), k_id, NAMA_COCO.get(k, k), round(c, 3),
                                        *(round(v) for v in (x1, y1, x2, y2))])
                if m.get("iou_ganda"):  # satu kendaraan dua kotak yang dua-duanya melintas = satu event
                    kotak = dict(zip(b.id.int().tolist(), b.xyxy.tolist()))
                    for p in penghitung.values():
                        p.buang_ganda(kotak, frame, m["iou_ganda"])
            if tulis:
                tulis.write(gambar(r, garis, penghitung, jaga.geser_sekarang() or (ikut and H is None), H_balik))
            if frame and frame % 1500 == 0:
                print(f"  {video.name}: frame {frame}, {frame / (time.time() - t_bagian):.1f} frame/detik", flush=True)
        cap.release()
        if tulis:
            tulis.release()
        n_frame = len(waktu_frame)
        if not n_frame:
            print(f"  {video.name}: tidak ada frame yang bisa dibaca, dilewati")
            continue

        geser = jaga.rentang() + (ikut.rentang() if ikut else [])
        for g in garis:
            for e in penghitung[g["id"]].events():
                d = waktu_frame[e["frame"]]
                baris.append({"video": video.name, "titik": tid, "garis": g["id"], "edge_model": g["edge_model"],
                              "track_id": e["track_id"], "frame": e["frame"], "detik": round(d, 2),
                              "waktu": (mulai + timedelta(seconds=d)).isoformat(timespec="milliseconds"),
                              "kelas_coco": NAMA_COCO.get(e["kelas"], e["kelas"]),
                              "kelas_pkji": PKJI.get(e["kelas"], "?"), "arah": e["arah"], "conf_rata": e["conf_rata"],
                              "kamera_geser": "ya" if any(a <= d <= z for a, z in geser) else "tidak"})
        inlier = [c[2] for c in jaga.cek_list if c[2] is not None]
        bagian.append({"video": str(video.relative_to(ROOT) if video.is_relative_to(ROOT) else video), "mulai": mulai.isoformat(timespec="seconds"),
                       "fps": round(fps, 3), "frame_diproses": n_frame, "frame_rusak": rusak,
                       "durasi_detik": round(waktu_frame[-1] + 1 / fps, 3), "ukuran": ukuran, "kamera_geser": geser,
                       "inlier_min": min(inlier, default=None),
                       "geser_maks_px": max((c[3] for c in jaga.cek_list), default=None)})
        if ikut:  # arus per jam suatu garis = jumlah / detik garis itu tampak utuh
            bagian[-1]["garis_terlihat_detik"] = {g["id"]: round(terlihat[g["id"]], 1) for g in garis}
        total_frame += n_frame

    if jejak:
        f_jejak.close()
    if not bagian:
        return
    lama = time.time() - t0
    baris.sort(key=lambda e: e["waktu"])
    with open(keluar / f"events_{tid}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, KOLOM)
        w.writeheader()
        w.writerows(baris)
    meta = {"titik": tid, "cctv": titik.get("cctv"), "garis": garis, "bobot": bobot, "tracker": m["tracker"],
            "imgsz": imgsz, "conf": m["conf"], "agnostic_nms": m.get("agnostic_nms", False), "iou_ganda": m.get("iou_ganda"), "kelas": m["kelas"], "min_frame_track": m["min_frame_track"],
            "device": str(device), "ultralytics": ultralytics.__version__, "lama_proses_detik": round(lama, 1),
            "frame_per_detik_proses": round(total_frame / lama, 1), "bagian": bagian,
            "dibuat": datetime.now().astimezone().isoformat(timespec="seconds")}
    (keluar / f"events_{tid}.meta.json").write_text(json.dumps(meta, indent=2))

    durasi = sum(b["durasi_detik"] for b in bagian)
    print(f"{tid}: {len(baris)} kendaraan melintas dalam {durasi:.0f} detik video, {len(bagian)} bagian "
          f"({total_frame / lama:.1f} frame/detik, {bobot}, imgsz {imgsz}, device {device})")
    for b in bagian:
        if b["kamera_geser"]:
            print(f"  {Path(b['video']).name}: kamera bergeser di detik {b['kamera_geser']}")
    rekap = Counter((e["garis"], e["arah"], e["kelas_pkji"]) for e in baris)
    for (g, arah, kelas), n in sorted(rekap.items()):
        print(f"  {g:4} {arah:8} {kelas:4} {n}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--titik", nargs="*", help="id titik, kosong = semua titik yang videonya ada")
    ap.add_argument("--detik", type=float, help="proses N detik pertama tiap bagian video saja (uji kecepatan)")
    ap.add_argument("--anotasi", action="store_true", help="tulis juga video beranotasi untuk dicek mata")
    ap.add_argument("--device", default="auto", help="auto, mps, cpu, atau 0 (cuda)")
    ap.add_argument("--bobot", help="ganti bobot model dari config, misalnya yolo26m.pt (file di models/)")
    ap.add_argument("--imgsz", type=int, help="ganti ukuran input model dari config, misalnya 640")
    ap.add_argument("--keluar", type=Path, default=KELUAR, help="folder hasil, bawaan data/lapangan")
    ap.add_argument("--simpan-jejak", action="store_true", help="simpan kotak tiap track tiap frame ke jejak_<titik>.csv")
    a = ap.parse_args()
    cfg = yaml.safe_load(a.config.read_text())
    for x in set(a.titik or []) - {t["id"] for t in cfg["titik"]}:
        print(f"titik {x} tidak ada di config")
    daftar = []
    for t in cfg["titik"]:
        if a.titik and t["id"] not in a.titik:
            continue
        if daftar_video(t):
            daftar.append(t)
        else:
            print(f"{t['id']}: belum ada video di {t['video']}, dilewati")
    device = pilih_device(a.device) if daftar else None
    for t in daftar:
        proses(cfg, t, device, a.detik, a.anotasi, a.bobot, folder(a.keluar), a.imgsz, a.simpan_jejak)


def folder(p):
    """Path relatif dianggap relatif ke folder proyek, jadi perintah bisa dijalankan dari mana saja."""
    return p if p.is_absolute() else ROOT / p


if __name__ == "__main__":
    main()
