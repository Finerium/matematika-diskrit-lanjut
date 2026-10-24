# Kasus 4 Pasar Tumpah Gasibu (Max Flow)

Tambahan kelompok kelas 2B di atas starter kit. Kasus 4 dari dosen (`case_04_pasar_tumpah.yaml`, data dummy
5 node) tetap utuh. Di sampingnya ditambah skenario dengan jaringan jalan nyata kawasan Gasibu - Monumen
Perjuangan, Bandung, dan algoritma max flow yang belum ada di starter kit. Istilah graf memakai node dan edge.

## Skenario

| File | Isi |
|---|---|
| `cases/scenarios/case_04_pasar_tumpah_gasibu.yaml` | 18 node, 24 edge berarah, 34 event `DYNAMIC_EDGE_CAPACITY` dari lapak buka (06.00) sampai pasar bubar (11.00) |
| `cases/scenarios/case_04_pasar_tumpah_gasibu_penataan.yaml` | jaringan yang sama, 17 event usulan penataan (lapak keluar dari badan jalan) |

- Node V1 - V16 = persimpangan nyata dari OpenStreetMap (diunduh 19 Oktober 2026). S = super source, T = super sink.
- Pintu masuk (edge dari S): E01 Jl. Dipatiukur dari Monumen Perjuangan, E02 Flyover Pasupati dari arah Pasteur
  (2 lajur sesuai tag `lanes` OSM), E23 Jl. Surapati permukaan dari Cikapayang - Dago. Surapati permukaan bertemu
  Jl. Penata Yudha di V16 lalu menyatu dengan turunan flyover di V2.
- Pintu keluar (edge ke T): E18 Surapati ke timur, E19 Diponegoro ke timur, E20 Diponegoro ke barat.
- Kendaraan masuk koridor taman (Jl. Wirayuda Barat dan Timur) lewat Jl. Singaperbangsa (E21, E22). Penghubung dari
  Dipatiukur di Monumen Perjuangan punya gerbang `access=no` dan bagian utara Wirayuda punya portal `access=destination`
  di OSM, jadi bagian itu tidak dimodelkan sebagai jalan tembus.
- `capacity` = kapasitas ruas dalam skr/jam menurut PKJI 2014: C = C0 x FCLJ x FCPA x FCHS x FCUK.
- `weight` = waktu tempuh bebas (menit), supaya skenario ini juga lolos audit Dijkstra di `tests/test_all_scenarios.py`.
- `road_class` (arteri, kolektor, lokal) dari tag `highway` OSM, `heavy_vehicle` = boleh dilewati bus dan truk
  (arteri dan kolektor). Dua field ini dan `label`/`time` diabaikan loader, dipakai analisis dan narasi log.

## Algoritma

| Kelas | File | Peran |
|---|---|---|
| `FordFulkerson` | `algorithms/maxflow/ford_fulkerson.py` | baseline Edmonds-Karp (BFS). Event kapasitas = hitung ulang dari nol |
| `FordFulkersonDFS` | `algorithms/maxflow/ford_fulkerson_dfs.py` | baseline kedua, Ford-Fulkerson asli (DFS), hanya meng-override `_cari_jalur()` |
| `PushRelabel` | `algorithms/maxflow/push_relabel.py` | SOTA Goldberg - Tarjan (1988), FIFO + global relabeling. Override `run()` dan `handle_dynamic_event()`: aliran lama dilanjutkan |
| `DynamicDinic` | `algorithms/maxflow/dinic.py` | SOTA kedua: Dinic (level graph + blocking flow) dengan perbaikan aliran inkremental |

Key registry: `ford_fulkerson` (alias `edmonds_karp`), `ford_fulkerson_dfs` (alias `ff_dfs`), `push_relabel`
(alias `maxflow`), `dynamic_dinic` (alias `dinic`).

Kontrak `run()` tetap `(path, nilai)`: `path` = jalur s -> t yang membawa aliran terbesar pada dekomposisi aliran,
`nilai` = max flow. Min cut tersimpan di `solver.min_cut_edges`, aliran tiap edge di `solver.flow`.
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
- `core/simulation_observers.py`, `core/visualizer.py`: label nilai "Max flow" dan label kapasitas edge untuk max flow.
- `tests/test_scaffolding.py`: auditor membaca `new_weight` atau `new_capacity`.

## Menjalankan

```bash
pip install -r requirements.txt matplotlib
python -m pytest                                                     # 83 tes
python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml
python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml -a dinic
python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu_penataan.yaml
python -m scripts.analisis_kasus4                                    # kendaraan berat + sensitivitas edge
python -m scripts.run_benchmark_maxflow                              # 4 algoritma, semua skenario max flow
python -m scripts.run_benchmark_skala                                # 4 algoritma, graf kisi 27 - 402 node
python -m scripts.run_simulation cases/scenarios/case_04_pasar_tumpah_gasibu.yaml   # runner bawaan dosen
```

`scripts/run_maxflow.py` mencetak max flow setelah setiap event, lalu menyimpan trace JSON
(`output/output_<case>_<algoritma>.json`), tabel `timeline_max_flow.csv`, dan gambar snapshot ke
`output/<case>_<algoritma>/`.

## Hasil

| Kondisi | Max flow (skr/jam) | Min cut | Subgraf bus dan truk |
|---|---|---|---|
| Normal (Minggu tanpa lapak) | 5.055,1 | E12 Surapati sisi utara Gasibu + E09 Jl. Japati | 4.324,3 |
| Puncak pasar tumpah (07.00 - 10.00) | 3.296,9 (turun 34,8%) | E12 + E09 (E07 portal ditutup, kapasitas 0) | 2.566,1 |
| Usulan penataan | 4.817,5 (95,3% dari normal) | E12 + E09 | 4.086,7 |

- E09 (Jl. Japati) dan E10 (Jl. Merak) seri dengan kapasitas sama. Yang dilaporkan adalah min cut yang paling dekat
  ke source, yaitu himpunan node yang masih terjangkau dari S di residual graph akhir. Himpunan ini sama untuk max flow
  apa pun, jadi keempat algoritma selalu melaporkan min cut yang sama.
- Selisih 730,8 skr/jam di kolom terakhir adalah jalur Japati - Merak yang hanya bisa dipakai mobil dan motor.
- Sensitivitas saat pasar: kalau E12 tidak lagi membatasi max flow naik 1.441,4, E09 + E10 hanya 127,0 (tertahan E22).
- Benchmark: Dinic dinamis paling sedikit langkahnya di skenario Gasibu dan paling cepat di graf kisi sampai 402 node.
  Push-Relabel kalah dari Edmonds-Karp di graf kisi besar karena setiap event mengisi ulang edge dari S lalu
  mengembalikan kelebihannya lewat banyak push kecil.

## Pengujian (`tests/test_maxflow.py`)

- 9 skenario max flow (7 dari dosen + 2 Gasibu) x 4 algoritma: nilai max flow sama dengan `networkx.maximum_flow_value`
  setelah `run()` dan setelah setiap event, aliran tidak melebihi kapasitas, konservasi aliran di setiap node,
  dan kapasitas min cut = max flow.
- 120 graf berarah acak per algoritma, masing-masing dengan 6 perubahan kapasitas acak.
- `SOTAScaffoldingAuditor` untuk `PushRelabel` dan `DynamicDinic` di skenario Gasibu.
- Min cut yang dilaporkan keempat algoritma sama persis setelah `run()` dan setelah setiap event.
- Angka utama (5.055,1, 3.296,9, 4.817,5, min cut E12 + E09) dikunci di `test_hasil_kasus_gasibu` dan
  `test_min_cut_sama_di_semua_algoritma`, angka subgraf bus dan truk di `test_analisis_kendaraan_berat`.
