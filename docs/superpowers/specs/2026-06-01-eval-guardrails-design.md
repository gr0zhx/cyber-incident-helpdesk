# Design Spec: Evaluasi Guardrails (Adversarial Testing)

**Tanggal:** 2026-06-01
**File output:** `tests/evaluation/eval_guardrails.py`

---

## Tujuan

Mengukur efektivitas lapisan keamanan guardrails (`run_input_guardrails`) terhadap serangan prompt injection / jailbreak menggunakan dataset JailbreakHub, sekaligus mengukur False Positive Rate terhadap laporan insiden siber yang normal.

Hasil evaluasi ini digunakan sebagai data pengujian keamanan pada Tugas Akhir (setara Tabel 4.7 dan 4.8 di TA Achmad Luthfan Aufar).

---

## Pendekatan

**Pure Guardrails Gate Test** — deterministik, tanpa LLM API call.

Setiap prompt dijalankan melalui `run_input_guardrails(prompt)` dan hasilnya dicatat berdasarkan field `.blocked`. Tidak ada inference LLM yang dilakukan selama evaluasi.

---

## Dataset

### Adversarial (JailbreakHub)
- **Sumber:** `https://raw.githubusercontent.com/verazuo/jailbreak_llms/master/data/jailbreak_prompts.csv`
- **Jumlah:** ~1.405 jailbreak prompt
- **Kolom yang dipakai:** `prompt`, `jailbreak` (True/False), `category`
- **Filter:** hanya baris dengan `jailbreak == True`
- **Caching:** disimpan ke `tests/evaluation/jailbreakhub_cache.csv` setelah download pertama

### Normal Reports (False Positive Test)
- **Sumber:** `tests/evaluation/rag_qa_dataset.json`
- **Field yang dipakai:** `question` dari setiap entry
- **Tujuan:** memastikan laporan insiden siber yang sah tidak ikut diblokir

---

## Metrik

| Metrik | Formula | Keterangan |
|--------|---------|-----------|
| Block Rate | `blocked / total_adversarial` | Efektivitas menangkap serangan |
| ASR | `(1 - Block Rate) × 100%` | Attack Success Rate — lebih rendah lebih baik |
| FP Rate | `false_positives / total_normal × 100%` | Laporan normal yang salah diblokir |
| Per-kategori | Block Rate per `category` JailbreakHub | Kelemahan spesifik per tipe serangan |

---

## Alur Proses

```
1. Download JailbreakHub CSV (skip jika cache sudah ada)
2. Load normal reports dari rag_qa_dataset.json
3. Loop adversarial prompts:
   a. run_input_guardrails(prompt)
   b. Catat: blocked, block_reason, category
4. Loop normal reports:
   a. run_input_guardrails(question)
   b. Catat: blocked (False Positive jika True)
5. Hitung semua metrik
6. Simpan ke guardrails_results.json
7. Print laporan ringkasan ke terminal
```

---

## CLI Interface

```bash
# Run penuh (auto-download jika belum ada cache)
python tests/evaluation/eval_guardrails.py

# Force re-download dataset dari GitHub
python tests/evaluation/eval_guardrails.py --refresh-dataset

# Batasi jumlah adversarial prompt (untuk testing cepat)
python tests/evaluation/eval_guardrails.py --limit 100

# Skip false positive test
python tests/evaluation/eval_guardrails.py --no-fp-test

# Simpan ke path custom
python tests/evaluation/eval_guardrails.py --output path/ke/output.json
```

---

## Struktur Output JSON

```json
{
  "meta": {
    "dataset": "JailbreakHub",
    "dataset_url": "https://raw.githubusercontent.com/verazuo/jailbreak_llms/master/data/jailbreak_prompts.csv",
    "total_adversarial": 1405,
    "total_normal": 30,
    "run_at": "2026-06-01T10:00:00"
  },
  "summary": {
    "blocked": 1343,
    "block_rate": 0.9559,
    "asr": 0.0441,
    "false_positives": 0,
    "fp_rate": 0.0
  },
  "per_category": [
    {
      "category": "Fictional Roleplay / Worldbuilding",
      "total": 180,
      "blocked": 138,
      "block_rate": 0.767,
      "asr": 0.233
    }
  ],
  "bypassed_prompts": [
    {
      "prompt": "...",
      "category": "...",
      "block_reason": ""
    }
  ],
  "false_positive_cases": [
    {
      "id": "QA-001",
      "question": "...",
      "block_reason": "..."
    }
  ]
}
```

---

## Terminal Report (contoh output)

```
=== Hasil Evaluasi Guardrails ===
Dataset  : JailbreakHub (1.405 prompt, filter jailbreak=True)
Normal   : rag_qa_dataset.json (30 laporan)
Dijalankan: 2026-06-01 10:00:00

--- Pengujian Keamanan (Adversarial) ---
Total Adversarial : 1405
Berhasil Diblokir : 1343  (95.59%)
ASR (Lolos)       :   62  ( 4.41%)

--- Breakdown Per Kategori ---
Kategori                           Total  Blocked  Block Rate    ASR
Fictional Roleplay / Worldbuilding   180      138      76.7%    23.3%
Expert Impersonation                  45       39      86.7%    13.3%
Encoding / Obfuscation                80       73      91.3%     8.8%
...

--- False Positive Rate ---
Total Laporan Normal :  30
Salah Diblokir       :   0  (0.00%)

Hasil disimpan: tests/evaluation/guardrails_results.json
```

---

## File yang Dibuat/Dimodifikasi

| File | Status | Keterangan |
|------|--------|-----------|
| `tests/evaluation/eval_guardrails.py` | Baru | Script evaluasi utama |
| `tests/evaluation/jailbreakhub_cache.csv` | Baru (auto-generated) | Cache dataset JailbreakHub |
| `tests/evaluation/guardrails_results.json` | Baru (auto-generated) | Hasil evaluasi |
| `.gitignore` | Dimodifikasi | Tambah `jailbreakhub_cache.csv` dan `guardrails_results.json` |

---

## Dependensi

Tidak ada dependensi baru. Hanya menggunakan:
- `requests` (sudah ada di `requirements.txt`)
- `csv`, `json`, `argparse`, `pathlib`, `datetime` (stdlib)
- `app.security.guardrails.run_input_guardrails` (internal)
