# Snapshot analytics — UMKM nasi goreng Medan

Total 847 review dari 9 UMKM. 
Hasil ABSA model di-aggregate per (UMKM, aspek) untuk lihat posisi 
kompetitif tiap UMKM relatif terhadap median pasar.

## Median pasar

Acuan kompetitif lintas 9 UMKM (cuma masuk hitung kalau volume mention ≥ 5):

| Aspek | median positive_share | median net_sentiment | n_umkm |
|---|---:|---:|---:|
| rasa | 93.2% | +0.66 | 9 |
| harga | 57.1% | +0.20 | 7 |
| pelayanan | 52.9% | +0.06 | 9 |

## Ranking per UMKM — rasa

| UMKM | positive_share | volume | pos | neg | strategy |
|---|---:|---:|---:|---:|---|
| nasi_olengg | 98.6% | 78 | 73 | 1 | MONITOR |
| nasi_goreng_pandu | 97.4% | 45 | 37 | 1 | MONITOR |
| istana_nasi_goreng | 97.0% | 38 | 32 | 1 | MONITOR |
| nasi_goreng_pemuda | 95.7% | 64 | 44 | 2 | MONITOR |
| nasi_goreng_surya | 93.2% | 68 | 55 | 4 | MONITOR |
| nasi_goreng_komdak | 88.6% | 55 | 39 | 5 | MONITOR |
| nasi_goreng_semalam_suntuk | 84.6% | 61 | 44 | 8 | MONITOR |
| naste | 81.6% | 63 | 40 | 9 | FIX |
| nasi_goreng_wak_ribut | 75.7% | 45 | 28 | 9 | FIX |

## Ranking per UMKM — harga

| UMKM | positive_share | volume | pos | neg | strategy |
|---|---:|---:|---:|---:|---|
| nasi_goreng_pandu | 100.0% | 9 | 9 | 0 | DEFEND |
| istana_nasi_goreng | 87.5% | 8 | 7 | 1 | DEFEND |
| nasi_goreng_komdak | 71.4% | 10 | 5 | 2 | DEFEND |
| nasi_goreng_surya | 57.1% | 15 | 4 | 3 | MONITOR |
| nasi_goreng_pemuda | 56.2% | 22 | 9 | 7 | MONITOR |
| nasi_goreng_semalam_suntuk | 45.5% | 13 | 5 | 6 | ATTACK |
| naste | 14.3% | 11 | 1 | 6 | ATTACK |

## Ranking per UMKM — pelayanan

| UMKM | positive_share | volume | pos | neg | strategy |
|---|---:|---:|---:|---:|---|
| istana_nasi_goreng | 100.0% | 5 | 5 | 0 | DEFEND |
| nasi_olengg | 86.7% | 45 | 39 | 6 | DEFEND |
| nasi_goreng_surya | 66.7% | 13 | 8 | 4 | PROMOTE |
| nasi_goreng_wak_ribut | 54.5% | 11 | 6 | 5 | MONITOR |
| nasi_goreng_semalam_suntuk | 52.9% | 17 | 9 | 8 | MONITOR |
| nasi_goreng_pemuda | 44.4% | 19 | 8 | 10 | MONITOR |
| nasi_goreng_komdak | 40.0% | 11 | 4 | 6 | ATTACK |
| nasi_goreng_pandu | 16.7% | 6 | 1 | 5 | ATTACK |
| naste | 11.4% | 35 | 4 | 31 | ATTACK |

## Ringkasan per UMKM

### istana_nasi_goreng (57 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 32 | 1 | 5 | 19 | 97.0% | MONITOR |
| harga | 7 | 1 | 0 | 49 | 87.5% | DEFEND |
| pelayanan | 5 | 0 | 0 | 52 | 100.0% | DEFEND |

### nasi_goreng_komdak (105 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 39 | 5 | 11 | 50 | 88.6% | MONITOR |
| harga | 5 | 2 | 3 | 95 | 71.4% | DEFEND |
| pelayanan | 4 | 6 | 1 | 94 | 40.0% | ATTACK |

### nasi_goreng_pandu (82 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 37 | 1 | 7 | 37 | 97.4% | MONITOR |
| harga | 9 | 0 | 0 | 73 | 100.0% | DEFEND |
| pelayanan | 1 | 5 | 0 | 76 | 16.7% | ATTACK |

### nasi_goreng_pemuda (102 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 44 | 2 | 18 | 38 | 95.7% | MONITOR |
| harga | 9 | 7 | 6 | 80 | 56.2% | MONITOR |
| pelayanan | 8 | 10 | 1 | 83 | 44.4% | MONITOR |

### nasi_goreng_semalam_suntuk (97 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 44 | 8 | 9 | 36 | 84.6% | MONITOR |
| harga | 5 | 6 | 2 | 84 | 45.5% | ATTACK |
| pelayanan | 9 | 8 | 0 | 80 | 52.9% | MONITOR |

### nasi_goreng_surya (105 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 55 | 4 | 9 | 37 | 93.2% | MONITOR |
| harga | 4 | 3 | 8 | 90 | 57.1% | MONITOR |
| pelayanan | 8 | 4 | 1 | 92 | 66.7% | PROMOTE |

### nasi_goreng_wak_ribut (80 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 28 | 9 | 8 | 35 | 75.7% | FIX |
| harga | 4 | 0 | 3 | 73 | 100.0% | DEFEND |
| pelayanan | 6 | 5 | 0 | 69 | 54.5% | MONITOR |

### nasi_olengg (118 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 73 | 1 | 4 | 40 | 98.6% | MONITOR |
| harga | 3 | 0 | 0 | 115 | 100.0% | NO_DATA |
| pelayanan | 39 | 6 | 0 | 73 | 86.7% | DEFEND |

### naste (101 review)

| Aspek | pos | neg | neu | TD | share | strategy |
|---|---:|---:|---:|---:|---:|---|
| rasa | 40 | 9 | 14 | 38 | 81.6% | FIX |
| harga | 1 | 6 | 4 | 90 | 14.3% | ATTACK |
| pelayanan | 4 | 31 | 0 | 66 | 11.4% | ATTACK |
