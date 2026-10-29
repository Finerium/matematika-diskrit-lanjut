"""Rekam stream CCTV pelindung.bandung.go.id ke data/video/<titik>/ untuk diproses hitung.py.

  python video_counting/rekam_cctv.py --menit 240                    # semua titik yang punya cctv, paralel
  python video_counting/rekam_cctv.py --titik T1 S2 --menit 10

Video disalin apa adanya (tanpa encode ulang, CPU ringan) ke file MPEG-TS (.ts), format asli potongan HLS. MP4 tidak
dipakai karena stream H.264 sebagian kamera Hikvision jadi rusak kalau disalin ke MP4, dan file .ts tetap bisa
dibaca walaupun perekaman terputus di tengah. Kalau stream putus, perekaman diulang otomatis sebagai bagian baru.
Tiap bagian punya file .json berisi jam mulai (dari jam laptop, bukan jam di layar CCTV yang bisa meleset beberapa
menit), durasi, dan jumlah frame.
"""
import argparse
import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from hitung import CONFIG, ROOT

HEADER = ["-user_agent", "Mozilla/5.0", "-headers", "Referer: https://pelindung.bandung.go.id/\r\n"]


def probe(video):
    """Durasi dan jumlah frame asli (dihitung dari paket, cepat dan tidak perlu decode)."""
    out = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0", "-count_packets", "-show_entries",
                          "stream=width,height,nb_read_packets,codec_name:format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True).stdout
    d = json.loads(out or "{}")
    s = (d.get("streams") or [{}])[0]
    return {"durasi_detik": round(float(d.get("format", {}).get("duration", 0)), 3),
            "frame": int(s.get("nb_read_packets", 0)), "ukuran": [s.get("width"), s.get("height")],
            "codec": s.get("codec_name")}


def rekam(titik, menit, cetak):
    folder = ROOT / Path(titik["video"]).parent
    folder.mkdir(parents=True, exist_ok=True)
    url, batas = titik["cctv"]["url"], datetime.now().astimezone() + timedelta(minutes=menit)
    gagal = 0
    while (sisa := (batas - datetime.now().astimezone()).total_seconds()) > 30:
        jam_mulai = datetime.now().astimezone()
        f = folder / f"{titik['id']}_{jam_mulai:%Y%m%d-%H%M%S}.ts"
        # -live_start_index -1: mulai dari potongan HLS terbaru. Bawaan ffmpeg mulai 3 potongan ke belakang
        # (sekitar 40 detik), dan kalau perekaman diulang, potongan lama itu terekam dua kali.
        cmd = ["ffmpeg", "-v", "error", "-nostdin", "-rw_timeout", "20000000", *HEADER, "-live_start_index", "-1",
               "-i", url, "-t", f"{sisa:.0f}", "-map", "0:v:0", "-c", "copy", "-f", "mpegts", "-y", str(f)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        jam_selesai = datetime.now().astimezone()
        info = probe(f) if f.exists() else {"durasi_detik": 0, "frame": 0}
        if info["frame"] == 0:
            if f.exists():
                f.rename(f.with_suffix(".gagal"))  # disisihkan, tidak ikut terbaca hitung.py
            gagal += 1
            cetak(f"{titik['id']}: stream gagal ({p.stderr.strip()[-120:] or 'tanpa pesan'}), coba lagi ({gagal})")
            if gagal >= 5:
                cetak(f"{titik['id']}: berhenti setelah 5 kali gagal berturut-turut")
                return
            time.sleep(10)
            continue
        gagal = 0
        # frame terakhir terekam saat ffmpeg selesai (ujung siaran langsung), jadi jam frame pertama =
        # jam selesai - durasi. Ini lebih tepat daripada jam ffmpeg mulai, yang bisa lebih lambat 1 potongan HLS.
        mulai = jam_selesai - timedelta(seconds=info["durasi_detik"])
        meta = {"titik": titik["id"], "cctv": titik["cctv"]["nama"], "url": url,
                "mulai": mulai.isoformat(timespec="seconds"),
                "jam_laptop_mulai": jam_mulai.isoformat(timespec="seconds"),
                "jam_laptop_selesai": jam_selesai.isoformat(timespec="seconds"), **info,
                "catatan": "mulai = jam laptop selesai - durasi; ketelitian sekitar 1 potongan HLS (<= 15 detik). "
                           "Jam di layar CCTV tidak dipakai karena bisa meleset beberapa menit."}
        f.with_suffix(".json").write_text(json.dumps(meta, indent=2))
        cetak(f"{titik['id']}: {f.name} {info['durasi_detik']:.0f} detik, {info['frame']} frame")
        if p.returncode == 0 and info["durasi_detik"] >= sisa - 30:
            return  # selesai normal
        cetak(f"{titik['id']}: stream terputus ({p.stderr.strip()[-120:] or 'tanpa pesan'}), lanjut bagian baru")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--titik", nargs="*", help="id titik, kosong = semua titik yang punya cctv")
    ap.add_argument("--menit", type=float, required=True)
    a = ap.parse_args()
    cfg = yaml.safe_load(a.config.read_text())
    daftar = [t for t in cfg["titik"] if t.get("cctv") and (not a.titik or t["id"] in a.titik)]
    if not daftar:
        raise SystemExit("tidak ada titik CCTV yang cocok di config")
    kunci = threading.Lock()

    def cetak(pesan):
        with kunci:
            print(f"[{datetime.now():%H:%M:%S}] {pesan}", flush=True)

    cetak(f"merekam {len(daftar)} titik selama {a.menit:g} menit: {', '.join(t['id'] for t in daftar)}")
    th = [threading.Thread(target=rekam, args=(t, a.menit, cetak)) for t in daftar]
    for t in th:
        t.start()
    for t in th:
        t.join()
    cetak("selesai")


if __name__ == "__main__":
    main()
