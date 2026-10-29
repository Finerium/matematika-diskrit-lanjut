"""Uji logika lintasan garis dengan track buatan, plus agregasi, validasi, penjaga kamera, dan penyimpanan config.

  python -m pytest video_counting/tests      atau      python video_counting/tests/test_lintasan.py
Tes penjaga kamera butuh OpenCV (venv proyek); tanpa OpenCV tes itu dilewati.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agregasi import jam_puncak, rekap, rentang_valid  # noqa: E402
from hitung import CONFIG, PenghitungGaris, PenjagaKamera  # noqa: E402
from kalibrasi import simpan  # noqa: E402
from validasi import bandingkan, error  # noqa: E402

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None

GARIS = [(0, 100), (200, 100)]  # garis mendatar y = 100, dari x = 0 sampai x = 200
MULAI = datetime(2026, 11, 1, 8, 0)
EKR_KOSONG = {"KR": 1.0, "SM": None, "KB": None}


def jalan(*track, min_frame=1):
    """track = (track_id, kelas_coco, [titik acuan tiap frame])"""
    p = PenghitungGaris(GARIS, min_frame)
    for tid, kelas, titik in track:
        for f, xy in enumerate(titik):
            p.update(tid, f, xy, kelas, 0.9)
    return p.events()


def test_melintas_sekali():
    ev = jalan((1, 2, [(100, 50), (100, 90), (100, 110), (100, 150)]))
    assert len(ev) == 1 and ev[0]["frame"] == 2


def test_menyentuh_tanpa_melintas():
    assert jalan((1, 2, [(100, 50), (100, 100), (100, 60)])) == []


def test_menyentuh_lalu_melintas():
    ev = jalan((1, 2, [(100, 50), (100, 100), (100, 150)]))
    assert len(ev) == 1 and ev[0]["frame"] == 2


def test_bolak_balik_dihitung_sekali():
    assert len(jalan((1, 3, [(100, 50), (100, 150), (100, 50), (100, 150)]))) == 1


def test_lewat_di_luar_ujung_segmen():
    assert jalan((1, 2, [(250, 50), (250, 150)]), (2, 2, [(-30, 50), (-30, 150)])) == []


def test_arah_berlawanan():
    turun = jalan((1, 2, [(100, 50), (100, 150)]))[0]["arah"]
    naik = jalan((1, 2, [(100, 150), (100, 50)]))[0]["arah"]
    assert {turun, naik} == {"positif", "negatif"}


def test_dua_kendaraan_dua_event():
    assert len(jalan((1, 3, [(50, 50), (50, 150)]), (2, 2, [(150, 150), (150, 50)]))) == 2


def test_track_pendek_dibuang():
    assert jalan((1, 2, [(100, 50), (100, 150)]), min_frame=5) == []


def test_kotak_goyang_di_garis_tidak_terhitung():
    p = PenghitungGaris(GARIS, 1, kedalaman=0.2)
    for f, y in enumerate([95, 104, 97, 106, 93, 105, 98, 108]):  # bus diam di garis, kotak (tinggi 50) goyang
        p.update(1, f, (100, y), 5, 0.9, 50)
    assert p.events() == []


def test_hilang_sesaat_setelah_melintas_tetap_terhitung():
    p = PenghitungGaris(GARIS, 1, kedalaman=0.2)
    for f, y in enumerate([40, 60, 80, 95, 101]):  # datang dari jauh, lewat 1 piksel, lalu track hilang
        p.update(1, f, (100, y), 2, 0.9, 25)
    assert len(p.events()) == 1


def test_kelas_terbanyak_selama_track():
    p = PenghitungGaris(GARIS, 1)
    for f, (xy, k) in enumerate([((100, 50), 2), ((100, 150), 7), ((100, 160), 2)]):
        p.update(1, f, xy, k, 0.8)
    assert [e["kelas"] for e in p.events()] == [2]  # car, bukan truck


def ev(menit, kelas, arah="positif", garis="L1", geser="tidak"):
    return {"garis": garis, "arah": arah, "kelas_pkji": kelas, "waktu": MULAI + timedelta(minutes=menit),
            "kamera_geser": geser}


def rentang(menit_mulai, menit_selesai):
    return [(MULAI + timedelta(minutes=menit_mulai), MULAI + timedelta(minutes=menit_selesai))]


def pos(baris, garis="L1"):
    return [x for x in baris if x["arah"] == "positif" and x["garis"] == garis]


def test_rekap_interval_ikut_jam_dan_terpotong():
    # rekaman 08:02 sampai 08:13: interval 08:00 terekam 3 menit, 08:05 penuh, 08:10 terekam 3 menit
    b = pos(rekap([ev(3, "SM"), ev(6, "KR"), ev(6.5, "KTB"), ev(11, "KB")], rentang(2, 13), 5, EKR_KOSONG,
                  [("L1", "A->B")]))
    assert [x["mulai_interval"].minute for x in b] == [0, 5, 10]
    assert [x["durasi_menit"] for x in b] == [3, 5, 3]
    assert [x["kend_per_jam"] for x in b] == [20, 12, 20]  # KTB tidak ikut kend/jam
    assert b[1]["KTB"] == 1 and b[0]["skr_per_jam"] == ""


def test_rekap_buang_interval_yang_terekam_kurang_dari_setengah():
    b = pos(rekap([ev(1, "KR")], rentang(0, 6), 5, EKR_KOSONG, [("L1", "A->B")]))
    assert [x["mulai_interval"].minute for x in b] == [0]  # 08:05 cuma terekam 1 menit


def test_rekap_skr_antrean_dan_dua_garis():
    antrean = [["2026-11-01T08:06:00", "2026-11-01T08:08:00"]]
    b = rekap([ev(1, "SM"), ev(2, "KB"), ev(3, "KR", garis="L2")], rentang(0, 10), 5,
              {"KR": 1.0, "SM": 0.5, "KB": 2.0}, [("L1", "A->B"), ("L2", "B->C")], antrean)
    assert pos(b)[0]["skr_per_jam"] == (0.5 + 2.0) * 12
    assert pos(b, "L2")[0]["KR"] == 1 and pos(b)[0]["KR"] == 0
    assert [x["ada_antrean"] for x in pos(b)] == ["tidak", "ya"]


def test_kamera_geser_dikeluarkan_dari_rekap():
    bagian = [{"mulai": MULAI.isoformat(), "durasi_detik": 600, "kamera_geser": [[300, 480]]}]
    r = rentang_valid(bagian)
    assert r == [(MULAI, MULAI + timedelta(minutes=5)), (MULAI + timedelta(minutes=8), MULAI + timedelta(minutes=10))]
    b = pos(rekap([ev(1, "KR"), ev(6, "KR", geser="ya")], r, 5, EKR_KOSONG, [("L1", "A->B")]))
    assert [x["mulai_interval"].minute for x in b] == [0]  # 08:05 cuma 2 menit yang valid


def test_jam_puncak_jendela_60_menit():
    events = [ev(m, "KR") for m in range(0, 90, 2)] + [ev(m + 0.5, "KR") for m in range(60, 90, 2)]
    b = rekap(events, rentang(0, 90), 15, EKR_KOSONG, [("L1", "A->B")])
    p = jam_puncak(b, 15)
    assert len(p) == 1 and p[0]["mulai"] == MULAI + timedelta(minutes=30) and p[0]["kend_per_jam"] == 45
    assert jam_puncak(rekap(events, rentang(0, 50), 15, EKR_KOSONG, [("L1", "A->B")]), 15) == []


def test_jam_puncak_tidak_melompati_celah():
    r = rentang(0, 30) + rentang(40, 80)
    assert jam_puncak(rekap([ev(m, "KR") for m in range(0, 80)], r, 10, EKR_KOSONG, [("L1", "A->B")]), 10) == []


def test_validasi_rata_rata_penghitung():
    manual = [{"titik": "T1", "garis": "L1", "arah": "positif", "video": "v.mp4", "klip_mulai_detik": "0",
               "klip_selesai_detik": "120", "penghitung": p, "KR": "0", "SM": n, "KB": "0", "KTB": "0"}
              for p, n in (("A", "10"), ("B", "12"))]
    events = [dict(ev(0.5, "SM"), video="v.mp4", detik="30")] * 10 + [dict(ev(3, "SM"), video="v.mp4", detik="180")]
    hasil = bandingkan(manual, events)
    assert hasil[("L1", "positif", "SM")] == (11, 10) and hasil[("L1", "positif", "TOTAL")] == (11, 10)
    assert round(error(11, 10), 3) == 0.091 and error(0, 0) == 0.0 and error(0, 2) is None


class Mem:
    """Pengganti file config di memori, supaya tes tidak menulis config asli."""

    def __init__(self, teks):
        self.teks = teks

    def read_text(self):
        return self.teks

    def write_text(self, teks):
        self.teks = teks


def test_simpan_kalibrasi_hanya_mengubah_garis_yang_dimaksud():
    import yaml
    asli = CONFIG.read_text()
    m = Mem(asli)
    simpan(m, "V_Surapati_Merak", "L1", [[10.4, 20], [300.6, 40]], "negatif")
    cfg = yaml.safe_load(m.teks)
    for t in cfg["titik"]:
        g = t["garis"][0]
        if t["id"] == "V_Surapati_Merak":
            assert g["koordinat"] == [[10, 20], [301, 40]] and g["arah_dihitung"] == "negatif"
        else:
            assert g["koordinat"] == yaml.safe_load(asli)["titik"][[x["id"] for x in cfg["titik"]].index(t["id"])][
                "garis"][0]["koordinat"]
    assert m.teks.count("#") == asli.count("#") and CONFIG.read_text() == asli


def test_penjaga_kamera():
    if cv2 is None:
        return
    rng = np.random.default_rng(0)
    latar = np.full((480, 640, 3), 90, np.uint8)  # adegan buatan: kotak dan garis seperti bangunan dan marka jalan
    for _ in range(80):
        x, y, w, h = rng.integers(0, 600), rng.integers(0, 440), rng.integers(10, 80), rng.integers(10, 80)
        cv2.rectangle(latar, (int(x), int(y)), (int(x + w), int(y + h)), [int(c) for c in rng.integers(0, 255, 3)], -1)
    for _ in range(30):
        a, b = rng.integers(0, 640, 2), rng.integers(0, 480, 2)
        cv2.line(latar, (int(a[0]), int(b[0])), (int(a[1]), int(b[1])), (255, 255, 255), 2)
    p = PenjagaKamera()
    for d in range(10):  # kamera diam, ada "kendaraan" kotak lewat
        img = latar.copy()
        cv2.rectangle(img, (40 * d, 300), (40 * d + 80, 360), (255, 255, 255), -1)
        p.cek(img, d)
    for d in range(10, 16):  # kamera diputar 40 piksel ke kanan
        p.cek(np.roll(latar, 40, axis=1), d)
    for d in range(16, 18):  # kembali ke posisi awal
        p.cek(latar, d)
    assert p.rentang() == [[10, 16]]


if __name__ == "__main__":
    for nama, f in list(globals().items()):
        if nama.startswith("test_"):
            f()
            print("lulus" if (cv2 or nama != "test_penjaga_kamera") else "dilewati", nama)
