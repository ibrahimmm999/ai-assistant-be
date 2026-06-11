# Marketing AI Assistant

## What I Implemented

### Backend (FastAPI + PostgreSQL)

**Natural language to SQL pipeline**
Setiap pertanyaan bisnis diproses melalui tiga tahap: schema database diinspect saat runtime via SQLAlchemy inspector, hasilnya di-inject ke SQL generation prompt bersama session history, lalu Gemini generate PostgreSQL query secara dinamis.

**Intent detection**
Sistem mengklasifikasikan setiap input ke tiga kategori: `data_query` (pertanyaan bisnis), `general` (sapaan/obrolan umum), dan `clarification` (input terlalu ambigu). Klasifikasi dilakukan via LLM dengan context-aware history injection dan `temperature=0` untuk konsistensi. Ada fallback validation — jika LLM return nilai di luar tiga token yang valid, sistem default ke `clarification`.

**Session memory**
Riwayat 6 percakapan terakhir di-inject ke setiap prompt, memungkinkan follow-up question seperti *"Yang mana dari Wardah?"* dijawab dengan konteks yang tepat. Disimpan in-memory per session_id — lightweight dan cukup untuk scope ini.

**Query safety guardrails (berlapis)**
- `is_query_safe()` menggunakan sqlglot — proper SQL parser, bukan sekadar regex. Memblokir operasi destruktif (DROP, DELETE, UPDATE, INSERT), membatasi query hanya ke tabel yang dikenal via whitelist, dan menolak SQL syntax yang tidak valid
- LIMIT 100 di-enforce di level kode sebagai fallback — bukan hanya instruksi ke LLM
- Null check sebelum eksekusi — jika Gemini safety filter trigger dan return `None`, sistem return pesan penolakan yang bersih tanpa expose error teknis

**Data summarization**
Hasil query mentah diubah menjadi jawaban Bahasa Indonesia yang ramah pengguna non-teknis. Ada instruksi eksplisit untuk tidak hallusinasi, tidak expose technical detail, dan hanya menyatakan fakta yang ada di hasil query.

### Frontend (React + TypeScript + Tailwind)
- Chat interface dengan bubble pesan, loading spinner, dan error state
- Sample questions yang bisa diklik langsung — persis skenario yang ada di requirement
- Session ID unik per tab browser untuk isolasi konteks percakapan

### Testing
36 automated test cases mencakup:
- Read-only enforcement (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, GRANT, REVOKE)
- Table whitelist validation (known tables, unknown tables, JOIN scenarios, subquery)
- Edge cases (case insensitive, empty string, CTE queries)
- API request validation (empty message, missing field, valid request)
- Response structure (required fields, intent-based behavior)
- Session handling dan health check

---

## What I Simplified

| Simplifikasi | Alasan |
|---|---|
| **Session memory in-memory** | Tidak persistent antar restart. Cukup untuk scope exercise yang tidak mensyaratkan multi-session persistence. Di production akan pindah ke Redis. |
| **Single LLM provider (Gemini)** | Tidak ada fallback ke provider lain. Multi-provider adalah bonus opsional di luar scope minimum. |
| **3 LLM calls per request** | Intent detection, SQL generation, dan summarization dipisah menjadi 3 call terpisah. Bisa dioptimasi menjadi 2 call dengan menggabungkan intent + SQL, tapi dipisah untuk clarity dan kemudahan debugging yang lebih baik per step. |
| **Tidak ada autentikasi** | Sesuai requirement — auth tidak diperlukan untuk exercise ini. |
| **Tidak ada streaming response** | Response dikirim sekaligus setelah LLM selesai. Loading spinner sudah cukup sebagai progress indicator. |
| **Pipeline linear** | Bukan agent architecture. Semua pertanyaan bisnis yang diminta bisa dijawab dengan satu SQL query — complexity agent tidak justified untuk scope ini. |

---

## What I Would Improve Next

**High priority:**
- **Streaming response** — SSE agar jawaban muncul token per token, mengurangi perceived latency
- **Persistent session storage** — pindah history percakapan ke Redis agar tidak hilang saat server restart dan support multiple server instance
- **Read-only database user** — koneksi DB hanya punya SELECT privilege, bukan superuser
- **Rate limiting** — mencegah abuse LLM quota per session

**Medium priority:**
- **Specific error handling** — tangani rate limit (429), SQL syntax error, dan network timeout secara terpisah, bukan generic `except Exception`
- **Request ID & audit logging** — setiap query yang dieksekusi dicatat untuk forensic dan monitoring
- **API versioning** — `/api/v1/chat` untuk support breaking changes

**Nice to have:**
- **Chart visualisasi** — render hasil query numerik sebagai bar/line chart menggunakan Recharts
- **Multi-provider LLM** — fallback ke OpenAI atau Claude jika Gemini rate limit atau down
- **Agent-like orchestration** — untuk pertanyaan multi-step yang butuh beberapa query dinamis

---

## How to Run Locally

### 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd ai-analytics-assistant
```

Buat file `.env` di folder `backend/`:
```bash
cp backend/.env.example backend/.env
```

Isi nilai yang diperlukan di `backend/.env`:
```
DATABASE_URL=postgresql://admin:password123@localhost:5433/analytics_db
GOOGLE_API_KEY=your_google_api_key_here
```

### 2. Jalankan Database

```bash
docker-compose up -d
```

PostgreSQL akan berjalan di port `5433`.

### 3. Setup & Jalankan Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Seed database dengan data awal:
```bash
make seed
```

Jalankan server:
```bash
make dev
```

Backend berjalan di `http://localhost:8000`.
Dokumentasi API tersedia di `http://localhost:8000/docs`.

### 4. Jalankan Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend berjalan di `http://localhost:5173`.

### 5. Jalankan Tests

```bash
cd backend
make test
```

### Makefile Commands (Backend)

| Command | Deskripsi |
|---|---|
| `make dev` | Jalankan development server dengan hot-reload |
| `make seed` | Reset dan isi ulang database dengan data awal |
| `make test` | Jalankan semua automated tests |

---