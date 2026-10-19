# Kasus 4 Pasar Tumpah Gasibu (Max Flow)

Tambahan kelompok kelas 2B di atas starter kit. Kasus 4 dari dosen (`case_04_pasar_tumpah.yaml`, data dummy
5 simpul) tetap utuh. Di sampingnya ditambah skenario dengan jaringan jalan nyata kawasan Gasibu - Monumen
Perjuangan, Bandung, dan algoritma max flow yang belum ada di starter kit.

## Skenario

| File | Isi |
|---|---|
| `cases/scenarios/case_04_pasar_tumpah_gasibu.yaml` | 17 simpul, 22 busur berarah, 34 event `DYNAMIC_EDGE_CAPACITY` dari lapak buka (06.00) sampai pasar bubar (11.00) |
| `cases/scenarios/case_04_pasar_tumpah_gasibu_penataan.yaml` | jaringan yang sama, 17 event usulan penataan (lapak keluar dari badan jalan) |

- Simpul V1 - V15 = persimpangan nyata dari OpenStreetMap (diunduh 19 Oktober 2026). S = super source (pintu masuk
  Jl. Dipatiukur dan Flyover Pasupati), T = super sink (pintu keluar Surapati timur, Diponegoro timur dan barat).
- Kendaraan masuk koridor taman (Jl. Wirayuda Barat dan Timur) lewat Jl. Singaperbangsa (E21, E22). Penghubung dari
  Dipatiukur di Monumen Perjuangan punya gerbang `access=no` dan bagian utara Wirayuda punya portal `access=destination`
  di OSM, jadi bagian itu tidak dimodelkan sebagai jalan tembus.
- `capacity` = kapasitas ruas dalam skr/jam menurut PKJI 2014: C = C0 x FCLJ x FCPA x FCHS x FCUK.
- `weight` = waktu tempuh bebas (menit), supaya skenario ini juga lolos audit Dijkstra di `tests/test_all_scenarios.py`.
- `label` di setiap busur dan field `time` di setiap event dipakai untuk narasi log, loader lama mengabaikannya.

## Algoritma

| Kelas | File | Peran |
|---|---|---|
| `FordFulkerson` | `algorithms/maxflow/ford_fulkerson.py` | baseline Ford-Fulkerson varian Edmonds-Karp (BFS). Event kapasitas = hitung ulang dari nol |
| `PushRelabel` | `algorithms/maxflow/push_relabel.py` | SOTA Goldberg - Tarjan (1988), FIFO + global relabeling. Mewarisi baseline, override `run()` dan `handle_dynamic_event()`: aliran lama dilanjutkan, bukan dibuang |
| `DynamicDinic` | `algorithms/maxflow/dinic.py` | pembanding SOTA kedua: Dinic (level graph + blocking flow) dengan perbaikan aliran inkremental |

Key registry: `ford_fulkerson` (alias `edmonds_karp`), `push_relabel` (alias `maxflow`), `dynamic_dinic` (alias `dinic`).

Kontrak `run()` tetap `(path, nilai)`: `path` = jalur s -> t yang membawa aliran terbesar pada dekomposisi aliran,
`nilai` = max flow. Min cut tersimpan di `solver.min_cut_edges`, aliran tiap busur di `solver.flow`.
Setiap langkah dicatat dengan `action_narrative` berbahasa Indonesia sesuai GLOSSARY.md.

## Perubahan kecil di inti starter kit

Supaya event kapasitas bisa jalan, beberapa bagian inti disesuaikan. Perilaku untuk skenario lain tidak berubah
(semua tes lama tetap lulus).

- `cases/scenario_loader.py`: `capacity` dan `label` di YAML sekarang ikut dibaca (sebelumnya hanya `weight`,
  jadi max flow selalu memakai bobot 1.0).
- `core/graph_model.py`: `add_weighted_edge()` menerima `capacity` dan `label`, tambah `update_edge_capacity()`
  dan `get_edge_label()`.
- `core/simulation_runner.py`: event diteruskan dengan `new_weight` atau `new_capacity` (sebelumnya event kapasitas
  akan `KeyError` karena runner selalu membaca `new_weight`).
- `core/base_algorithm.py`: `log_step()` menerima `narrative` opsional.
- `core/simulation_observers.py`, `core/visualizer.py`: label nilai "Max flow" dan label busur kapasitas untuk max flow.
- `tests/test_scaffolding.py`: auditor membaca `new_weight` atau `new_capacity`.

## Menjalankan

```bash
pip install -r requirements.txt matplotlib
python -m pytest                                                     # 72 tes
python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml
python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml -a ford_fulkerson
python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu_penataan.yaml
python -m scripts.run_benchmark_maxflow                              # baseline vs SOTA, semua skenario max flow
python -m scripts.run_simulation cases/scenarios/case_04_pasar_tumpah_gasibu.yaml   # runner bawaan dosen
```

`scripts/run_maxflow.py` mencetak max flow setelah setiap event, lalu menyimpan trace JSON
(`output/output_<case>_<algoritma>.json`), tabel `timeline_max_flow.csv`, dan gambar snapshot ke
`output/<case>_<algoritma>/`.

## Hasil

| Kondisi | Max flow (skr/jam) | Min cut |
|---|---|---|
| Normal (Minggu tanpa lapak) | 5.055,1 | E12 Surapati sisi utara Gasibu + E09 Jl. Japati |
| Puncak pasar tumpah (07.00 - 10.00) | 3.296,9 (turun 34,8%) | E12 + E09 (E07 portal ditutup, kapasitas 0) |
| Usulan penataan | 4.817,5 (95,3% dari normal) | E12 + E09 |

E09 (Jl. Japati) dan E10 (Jl. Merak) seri dengan kapasitas sama. Yang dilaporkan adalah min cut yang paling dekat
ke source, yaitu himpunan simpul yang masih terjangkau dari S di residual graph akhir. Himpunan ini sama untuk
max flow apa pun, jadi ketiga algoritma selalu melaporkan min cut yang sama.

## Pengujian (`tests/test_maxflow.py`)

- 9 skenario max flow (7 dari dosen + 2 Gasibu) x 3 algoritma: nilai max flow sama dengan `networkx.maximum_flow_value`
  setelah `run()` dan setelah setiap event, aliran tidak melebihi kapasitas, konservasi aliran di setiap simpul,
  dan kapasitas min cut = max flow.
- 120 graf berarah acak per algoritma, masing-masing dengan 6 perubahan kapasitas acak.
- `SOTAScaffoldingAuditor` untuk `PushRelabel` dan `DynamicDinic` di skenario Gasibu.
- Min cut yang dilaporkan ketiga algoritma sama persis setelah `run()` dan setelah setiap event
  (`test_min_cut_sama_di_semua_algoritma`).
- Angka yang dipakai di slide (5.055,1, 3.296,9, min cut E12 + E09) dikunci di `test_hasil_kasus_gasibu`,
  angka penataan 4.817,5 dikunci di `test_min_cut_sama_di_semua_algoritma`.
