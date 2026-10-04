# Backend API (port 8000)
Interactive docs: `http://localhost:8000/docs`. All endpoints are under `/api`. Errors always look like
`{"error": {"code": "...", "message": "...", "fields": [...]}}`.

Auth: log in, then send `Authorization: Bearer <token>`. Sessions expire after `SESSION_HOURS` (default 1) or on logout.

| Method + path | Auth | Purpose |
|---|---|---|
| POST `/auth/rfid` `{uid, language}` | no | Log in with card UID. 401 `card_not_registered` |
| POST `/auth/fingerprint` `{template_id?, language}` | no | Log in by fingerprint (mock mode accepts `template_id`) |
| POST `/auth/guest` `{language}` | no | Anonymous session |
| GET `/auth/me`, PUT `/auth/language`, POST `/auth/logout` | yes | Session info / language / end session |
| POST `/speech/transcribe` multipart `audio, language` | yes | Speech to text (`engine: mock` returns empty text + note) |
| POST `/ocr/scan` multipart `file, language` | yes | OCR an image, stores it in `scanned_documents` |
| GET `/ocr/documents` | yes | This session's scans |
| POST `/translate` `{text, source, target}` | yes | Translate; `translated:false` if no engine |
| POST `/ai/ask` `{text, language}` | yes | Translate in, AI core `/ask`, translate out, save history |
| POST `/ai/contract` `{text, explain, language}` | yes | Contract risk check |
| POST `/ai/notice` `{text, language}` | yes | Fake notice / SMS check |
| POST `/ai/schemes` profile + `language` | yes | Scheme recommendations |
| POST `/complaints` `{category, details, ...}` | yes | Create complaint: steps + letter + reference number |
| GET `/complaints`, GET `/complaints/{id}` | yes | Own complaints only |
| POST `/receipt/preview`, POST `/print` `{kind: complaint\|answer\|text, ...}` | yes | Receipt text / print (CUPS) |
| GET `/history`, GET `/history/{id}` | yes | Own history (by user, or by session for guests) |
| GET `/health` | no | Component status: `ok` / `degraded` / `down` |
| GET `/admin/logs`, POST `/admin/users` | `X-Admin-Key` | Logs, register member cards |

AI responses add `translation_ok` (false = the text is still English because no translation engine answered)
and `conversation_id` (use it to print the answer).

Tables: `users, sessions, conversations, complaints, scanned_documents, system_logs`.
