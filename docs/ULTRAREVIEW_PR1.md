# Ultrareview — PR #1: feat/web-plan-a → main

> Dijalankan: 2026-05-30  
> Repo: [gr0zhx/pusdatin-help#1](https://github.com/gr0zhx/pusdatin-help/pull/1)  
> Total temuan: 8 (4 × normal, 4 × nit)

---

## Ringkasan Temuan

| ID | Severity | File | Baris | Judul |
|----|----------|------|-------|-------|
| bug_004 | **normal** | `app/web/routes/pelapor.py` | 190–202 | IDOR: endpoint tiket tanpa autentikasi |
| bug_005 | **normal** | `app/web/routes/pelapor.py` | 161 | Reflected XSS via pesan UploadError |
| bug_019 | **normal** | `app/rag/retriever.py` | 84–95 | Parameter `search()` salah — semantic retrieval mati |
| bug_001 | **normal** | `app/agents/notifier.py` | 14–15 | Fallback chat ID hardcoded — notifikasi nyasar ke production |
| merged_bug_013 | **normal** | `app/web/services/chat_service.py` | 104–108 | Counter `clarification_rounds` menghitung pesan yang bukan klarifikasi |
| bug_007 | nit | `app/web/services/auth_service.py` | 60–65 | Username enumeration via pesan error akun dinonaktifkan |
| bug_025 | nit | `app/web/routes/admin_actions.py` | 157–159 | Header injection via filename di Content-Disposition |
| bug_054 | nit | `app/web/services/chat_service.py` | 207–233 | Redis DELETE sebelum DB commit — data upload hilang jika commit gagal |

---

## Detail Temuan

---

### [normal] bug_004 — IDOR: Endpoint Tiket Tanpa Autentikasi

**File:** `app/web/routes/pelapor.py:190–202`

**Deskripsi:**  
Endpoint `GET /lapor/tiket/{ticket_id}` tidak memiliki dependency autentikasi sama sekali. Semua endpoint lain di file yang sama (`/chat`, `/chat/message`, `/chat/upload`, `/chat/reset`) menggunakan `Depends(get_reporter_session)`, tapi endpoint tiket ini tidak.

Karena ticket ID bersifat sekuensial (`TICKET-2026-0001`, `TICKET-2026-0002`, ...), siapapun bisa mengenumerasi semua tiket tanpa login dan mendapatkan data sensitif: nama pelapor, deskripsi insiden, klasifikasi AI, rekomendasi mitigasi, severity, confidence score.

**Fix:**
```python
@router.get("/tiket/{ticket_id}", response_class=HTMLResponse)
def ticket_status(
    request: Request,
    ticket_id: str,
    reporter: dict = Depends(get_reporter_session),
    db: Session = Depends(get_db_session),
):
    ticket = db.query(IncidentTicket).filter_by(ticket_id=ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=404)
    if ticket.reporter_id != reporter["reporter_id"]:
        raise HTTPException(status_code=403)
    ...
```

---

### [normal] bug_005 — Reflected XSS via Pesan UploadError

**File:** `app/web/routes/pelapor.py:161`

**Deskripsi:**  
Pesan exception `UploadError` dirender langsung ke `HTMLResponse` tanpa escaping. Pesan error tersebut menyertakan ekstensi file dari input user (via `Path(filename).suffix`).

Contoh serangan: upload file bernama `x.<img src=x onerror=alert(document.cookie)>` → ekstensi diambil sebagai `.<img src=x onerror=alert(document.cookie)>` → dimasukkan ke HTML tanpa escape → XSS.

CSP yang ada (`'unsafe-inline'` di `script-src`) tidak memblokir inline event handler seperti `onerror=`.

**Fix:**
```python
except UploadError as exc:
    return HTMLResponse(
        f'<p style="color: #dc2626; font-size: 13px;">{_html.escape(str(exc))}</p>'
    )
```
(Modul `html` sudah diimport sebagai `_html` di file yang sama.)

---

### [normal] bug_019 — Parameter `search()` Salah — Semantic Retrieval Mati Diam-diam

**File:** `app/rag/retriever.py:84–95`

**Deskripsi:**  
Setelah refactor, `client.search()` dipanggil dengan parameter `query=query_vector`, padahal di `qdrant-client==1.13.x` (yang di-pin di `requirements.txt`) nama parameternya adalah `query_vector=`, bukan `query=`. Parameter `query=` adalah milik method `query_points()`.

Hasilnya: `search()` menerima `query` di `**kwargs`, `query_vector` missing → `TypeError` → ditangkap oleh `except Exception` yang bare → `semantic_points = []` → seluruh komponen semantic search hilang, retrieval terdegradasi menjadi keyword-only.

Kondisi `hasattr(self.client, "search")` selalu `True` untuk semua versi `QdrantClient`, sehingga branch `query_points()` tidak pernah dieksekusi.

**Fix:**
```python
resp = self.client.search(
    collection_name=COLLECTION_NAME,
    query_vector=query_vector,  # bukan query=
    query_filter=metadata_filter,
    limit=top_k,
    with_payload=True,
)
```

---

### [normal] bug_001 — Fallback Chat ID Hardcoded — Notifikasi Nyasar ke Production

**File:** `app/agents/notifier.py:14–15`

**Deskripsi:**  
`_CSIRT_CHAT_ID_FALLBACK = "-1003971618295"` dipakai sebagai default di `os.getenv()`:
```python
csirt_id = os.getenv(_CSIRT_CHAT_ID_ENV, _CSIRT_CHAT_ID_FALLBACK)
```

Sebelumnya defaultnya `""` (falsy → skip notifikasi). Sekarang fallback selalu truthy, sehingga di environment test/staging/dev yang tidak set `CSIRT_CHAT_ID`, notifikasi akan dikirim ke grup Telegram production.

`bot.py` justru melakukan hal yang benar — mengembalikan `None` jika env var tidak diset. `notifier.py` harus mengikuti pola yang sama.

**Fix:**
```python
csirt_id = os.getenv(_CSIRT_CHAT_ID_ENV, "")  # kembali ke perilaku semula
```
atau ikuti pola `bot.py`:
```python
csirt_id = os.getenv(_CSIRT_CHAT_ID_ENV)
if not csirt_id:
    return recipients
```

---

### [normal] merged_bug_013 — Counter `clarification_rounds` Menghitung Semua Pesan Bot

**File:** `app/web/services/chat_service.py:104–108`

**Deskripsi:**  
```python
clarification_rounds = sum(
    1 for m in history
    if m["role"] == "assistant" and not m["content"].startswith("Tiket insiden")
)
```

Counter ini menghitung **semua** pesan assistant yang bukan konfirmasi tiket — termasuk pesan timeout ("Maaf, sistem sedang sibuk..."), pesan error, dan respons umum lainnya. Padahal intent-nya adalah menghitung hanya permintaan klarifikasi aktual.

**Efek samping:** Setelah satu timeout, `clarification_rounds` menjadi 1, memenuhi kondisi hard limit di `graph.py:229` (`rounds >= 1 and intent == "report_incident"`), sehingga input yang masih ambigu langsung di-force-process menjadi tiket berkualitas rendah.

**Masalah turunan yang berinteraksi:**
- `orchestrator.py:44–45`: `clarification_message` kosong dari LLM memaksa `needs_clarification=False` tanpa fallback message
- `graph.py:229`: hard limit hanya cek `report_incident` intent, tidak `needs_clarification`

**Fix:**  
Tag pesan klarifikasi dengan metadata saat disimpan ke history:
```python
history.append({"role": "assistant", "content": bot_text, "ts": ts, "type": "clarification"})
```
Lalu hitung hanya yang `m.get("type") == "clarification"`.

---

### [nit] bug_007 — Username Enumeration via Error Akun Dinonaktifkan

**File:** `app/web/services/auth_service.py:60–65`

**Deskripsi:**  
Login dengan akun disabled mengembalikan error `"account_disabled"` yang ditampilkan sebagai "Akun dinonaktifkan" — berbeda dari pesan error credential salah. Ini memungkinkan enumerasi: penyerang bisa membedakan "username + password benar, akun disabled" vs "password salah". Padahal kode sudah ada `_DUMMY_HASH` untuk mencegah timing attack.

Selain itu, path disabled-account tidak memanggil `_increment_failure()`, jadi penyerang bisa probe password akun disabled tanpa batas.

**Fix:** Kembalikan `invalid_credentials` untuk akun disabled, atau cek `is_active` sebelum verifikasi password.

---

### [nit] bug_025 — Header Injection via Filename di Content-Disposition

**File:** `app/web/routes/admin_actions.py:157–159`

**Deskripsi:**  
`FileResponse` dibuat dengan parameter `filename=` (yang sudah aman via RFC 5987) sekaligus `headers={"Content-Disposition": f'attachment; filename="{filename}"'}`. Karena Starlette menggunakan `setdefault`, header manual yang tidak ter-escape menang.

Filename dengan tanda kutip ganda (misal `evil".pdf`) menghasilkan header rusak: `attachment; filename="evil".pdf"`.

**Fix:** Hapus parameter `headers=` dari `FileResponse`:
```python
return FileResponse(abs_path, filename=filename)
```

---

### [nit] bug_054 — Redis DELETE Sebelum DB Commit — Data Upload Hilang

**File:** `app/web/services/chat_service.py:207–233`

**Deskripsi:**  
Method `_flush_pending_uploads()` menggunakan Redis pipeline yang secara atomik GET dan DELETE key `pending_uploads` sebelum `db.commit()`. Jika commit gagal, data upload sudah terhapus dari Redis tapi `TicketAttachment` tidak tersimpan di DB → file di disk menjadi orphan dan tidak bisa dilampirkan ke tiket.

**Fix:**
```python
pending_raw = self._redis.get(key)   # GET dulu tanpa DELETE
if not pending_raw:
    return
# ... buat TicketAttachment records ...
db.commit()
self._redis.delete(key)              # DELETE hanya setelah commit sukses
```

---

## Prioritas Perbaikan

### Segera (sebelum demo/sidang)
1. **bug_004** — IDOR tiket (data seluruh user bisa diakses tanpa login)
2. **bug_005** — XSS di upload error (mudah dieksploitasi)
3. **bug_019** — Semantic retrieval mati (kontribusi utama skripsi tidak berfungsi!)
4. **bug_001** — Notifikasi nyasar ke production dari test/dev

### Setelah itu
5. **merged_bug_013** — Clarification flow counter salah
6. **bug_054** — Race condition data upload
7. **bug_007** — Username enumeration (nit)
8. **bug_025** — Header injection (nit, admin-only endpoint)
