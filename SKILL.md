---
name: matsne-gov-ge-scraping
description: >
  Complete API wrapper for matsne.gov.ge — Georgia's official legislative database.
  Reverse-engineered from Drupal's internal JavaScript. Replaces fragile HTML scraping
  with structured JSON API calls. Includes 12+ endpoints, rate limiting, retry logic.
---

# Matsne.gov.ge — Complete API Reference

## Overview

matsne.gov.ge is Georgia's official legislative database (საკანონმდებლო მაცნე).
It runs Drupal CMS with custom modules. No official public API exists, but the
site's JavaScript exposes **12+ internal JSON endpoints** that are significantly
more reliable than HTML scraping.

**API Wrapper:** `matsne_api.py`  
**MCP Server:** `mcp_server.py`

## Quick Start

### Python API
```python
from matsne_api import MatsneAPI

api = MatsneAPI()

# Autocomplete search (0.58s)
results = api.suggest("პერსონალური")

# Search with filters
docs = api.search(page=0, query="შრომის", limit=10)

# Full document
doc = api.get_document(6840140)

# Quick date check
api.has_today()  # → True/False
api.today_documents()  # → [{id, title, date}, ...]
```

## Complete Endpoint Catalog

### Public Endpoints (no auth required)

| # | Endpoint | Method | Response | Speed | Description |
|---|----------|--------|----------|-------|-------------|
| 1 | `/document/suggest` | POST | `[{id, state, title}]` | 0.58s | Autocomplete search |
| 2 | `/ka/document/search?page=N&is-ajax=1` | GET | `{documents_list, pagination}` | 1.3s | JSON search results |
| 3 | `/ka/document/tree/{id}/{part}` | GET | `{Title, Anchor, DocumentPart}` | 1.1s | Document structure tree |
| 4 | `/ka/document/backReferences/{id}?part_id=X` | GET | `[{ref}]` or `[]` | 1.0s | Back references |
| 5 | `/ka/document/comment/{id}/read?part_id=X` | GET | `[{comment}]` or `[]` | 1.0s | Read comments |
| 6 | `/ka/document/linked/{id}/{anchor}` | GET | `{html: "..."}` | 1.0s | Inline HTML fragment |
| 7 | `/annotation/api/search?uri=...` | GET | `{total, rows}` | 1.0s | Annotation search |

### Authenticated Endpoints (require login)

| # | Endpoint | Method | Description |
|---|----------|--------|-------------|
| 8 | `/ka/document/comment/{id}/create` | POST | Create comment |
| 9 | `/ka/document/comment/{cid}/update` | POST | Update comment |
| 10 | `/ka/document/comment/{cid}/remove` | GET | Delete comment |
| 11 | `/ka/document/comment/{cid}/rate` | GET | Rate comment |
| 12 | `/ka/document/highlight/{id}/create` | POST | Create highlight |
| 13 | `/favorites` | POST | Add/remove favorite |
| 14 | `/favorites?method=getFavoritesList` | GET | Get favorites list |

### Voice Server

| # | Endpoint | Method | Description |
|---|----------|--------|-------------|
| 15 | `speech.matsne.gov.ge:443/voice?t=TEXT` | GET | TTS for short text |
| 16 | `speech.matsne.gov.ge:443/voice/big` | POST | TTS for full document |

### MCP Server

The repo includes an MCP server (`mcp_server.py`) that exposes the API as 10 tools + 2 resources:

**Tools:**
- `matsne_suggest` — keyword autocomplete
- `matsne_search` — filtered search (date, type, organ, pagination)
- `matsne_get_document` — full document (meta + text + tree + back-refs + comments)
- `matsne_get_tree` — document structure tree
- `matsne_get_back_references` — citing documents
- `matsne_get_comments` — user comments
- `matsne_get_linked` — inline HTML fragment for a document part
- `matsne_search_by_keyword` — quick active-doc keyword search
- `matsne_has_today` — check today's publications
- `matsne_today_documents` — today's documents list

**Resources:**
- `matsne://document/{id}` — document as JSON
- `matsne://today` — today's documents as JSON

**Run:** `uv run mcp_server.py`

## Required Headers

```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: application/json          # for JSON endpoints
X-Requested-With: XMLHttpRequest  # for JSON endpoints
Accept-Language: ka,en;q=0.9
```

## Endpoint Details

### 1. POST /document/suggest — Autocomplete

**Input:** `text=პერსონალური` (form-urlencoded)
**Output:**
```json
[
  {"id": 1244845, "state": "active", "title": "პერსონალური მონაცემების..."},
  {"id": 2352161, "state": "expired", "title": "..."}
]
```
- Returns up to 50 results
- `state` can be "active" or "expired"
- Fastest endpoint (~0.58s)

### 2. GET /ka/document/search?is-ajax=1 — Search

**Parameters:**
- `page` — Page number (0-indexed)
- `query` — Full-text search
- `limit` — Results per page (5, 10, 20, 30, 50, 100)
- `sort` — Sort order (e.g., `publishDate_desc`)
- `issuer` — Document issuer filter
- `type` — Document type filter
- `number` — Document number
- `registration_code` — Registration code
- `signing_date_fr[date]` — Date from (DD/MM/YYYY)
- `signing_date_to[date]` — Date to (DD/MM/YYYY)

**Output:** `{documents_list: "<HTML>", pagination: "<HTML>"}`
- `documents_list` contains panel-based HTML with document links
- The wrapper parses this into structured `{id, title, date, doc_type, organ}`

**HTML Structure (query search):**
```html
<div class="panel panel-success document-search-result-item">
  <div class="panel-heading">
    <p><a href="/ka/document/view/{id}">Title</a></p>
  </div>
  <div class="panel-body">
    <ul class="list-inline">
      <li><small>დოკუმენტის ტიპი</small></li>
      <li><small>●</small></li>
      <li><small>ორგანო</small></li>
      <li><small>●</small></li>
      <li><small>DD/MM/YYYY</small></li>
    </ul>
  </div>
</div>
```

### 3. GET /ka/document/tree/{id}/{part} — Document Tree

**Output:**
```json
{
  "Title": "დოკუმენტი. კანონის შაბლონი",
  "Anchor": "DOCUMENT:1;",
  "DocumentPart": {
    "Title": "საქართველოს კანონი",
    "Anchor": "DOCUMENT:1;HEADER:1;"
  }
}
```

**Variations by document type:**
- **Simple law:** Flat structure, single DocumentPart
- **Decree:** Multiple DocumentParts (HEADER, ARTICLE:1, ARTICLE:2)
- **Complex code:** Deep nested tree (506KB for Civil Code)
- **Resolution:** Same flat structure as simple law

**Tree node structure:**
```json
{
  "Title": "მუხლი 1",
  "Anchor": "DOCUMENT:1;ARTICLE:1;",
  "DocumentPart": [...]  // nested parts or single object
}
```

### 4. GET /ka/document/backReferences/{id} — Back References

**Output:** `[]` (empty array) or list of references
- Returns documents that cite/reference the given document
- New documents typically have 0 back-references

### 5. GET /ka/document/comment/{id}/read — Comments

**Output:**
```json
[{
  "cid": 12345,
  "text": "Comment text",
  "html": "<p>Comment HTML</p>",
  "anchor": "DOCUMENT:1;",
  "rating": 5,
  "author": {
    "name": "username",
    "fullName": "Full Name",
    "uid": 12345,
    "avatar": "..."
  },
  "created": 1234567890,
  "formattedCreate": "01/01/2026",
  "changed": 1234567890,
  "formattedChange": "01/01/2026"
}]
```

### 6. GET /ka/document/linked/{id}/{anchor} — Inline Fragment

**Output:** `{"html": "<a name='...'>...</a><table>..."}`
- Returns HTML fragment for inline display of linked documents
- Used when hovering over document links within other documents
- `anchor` format: `DOCUMENT:1;HEADER:1;` or `DOCUMENT:1;ARTICLE:1;`

### 7. GET /annotation/api/search — Annotations

**Parameters:** `uri=document/view/{id}` (URL-encoded)
**Output:** `{"total": 0, "rows": []}`

## Drupal.settings API Map

Found in `Drupal.settings.document_view.api` on document pages:

```json
{
  "document": "/ka/document/view/",
  "backReferences": "/ka/document/backReferences/{id}?part_id=%",
  "markerString": "/ka/document/view/{id}&getMarkers",
  "tree": "/ka/document/tree/{id}/{part}",
  "comments": {
    "read": "/ka/document/comment/{id}/read?part_id=%",
    "create": "/ka/document/comment/{id}/create",
    "update": "/ka/document/comment/%/update",
    "remove": "/ka/document/comment/%/remove",
    "rate": "/ka/document/comment/%/rate"
  },
  "highlights": {
    "create": "/ka/document/highlight/{id}/create?publication_id=0",
    "read": "/ka/annotation/api/search?uri=document/view/{id}",
    "update": "/ka/annotation/api/annotations/%?action=update",
    "remove": "/ka/annotation/api/annotations/%?action=destroy"
  },
  "voiceServer": "https://speech.matsne.gov.ge:443/voice/big"
}
```

## Anti-Bot / Bot Detection

### What's Protected
- `/ka/document/view/{id}` — INTERMITTENTLY blocked (some IDs work, some don't)
- `/ka/document/recent` — CONSISTENTLY blocked
- Search form date pickers — Non-functional via automation
- Direct URL search with `date_from/date_to` — Blocked

### What's NOT Protected (API endpoints work reliably)
- `/document/suggest` — Always works ✅
- `/ka/document/search?is-ajax=1` — Always works ✅
- `/ka/document/tree/{id}/{part}` — Always works ✅
- `/ka/document/backReferences/{id}` — Always works ✅
- `/ka/document/comment/{id}/read` — Always works ✅
- `/ka/document/linked/{id}/{anchor}` — Always works ✅
- `/annotation/api/search` — Always works ✅

### Document Text Fallback

`get_document()` auto-falls back to `_collect_anchors()` + `get_text_via_linked()` when HTML page is blocked. It walks the document tree, fetches each anchor via the `/ka/document/linked/` API endpoint (never blocked), and concatenates the plain text.

### Voice Server Anti-Bot
The voice server uses a special anti-bot mechanism:
- Cookie name: `XZCookie` (set on first visit)
- JavaScript reads `document.ZXKey` and sends it as header
- Not easily bypassable without browser execution

## Rate Limiting

No explicit rate limiting observed on API endpoints (5 rapid requests all returned 200).
The wrapper enforces 0.3s delay between requests as a safety measure.

## Pitfalls

- ⚠️ `curl` for `/ka/document/view/{id}` pages is **INTERMITTENTLY blocked** — some IDs work via curl, others return "Access Denied". Use API endpoints instead.
- ❌ `curl` for `/ka/document/recent` is **CONSISTENTLY blocked**
- ❌ matsne homepage sidebar "ცვლილებების მაცნე" shows **OLD content** (2023 and earlier)
- ❌ UI date pickers and `additional_status=normative` parameter are **non-functional**
- ❌ Direct URL search (`/ka/search?text=...`) is **blocked by anti-bot**
- ❌ Search results with `query` parameter return different HTML structure than plain search
- ⚠️ `DocumentPart` in tree can be a single object OR an array — always check type
- ⚠️ Title parsing: some titles contain `<b>` tags (keyword highlighting) — strip HTML
- ⚠️ Speech server uses XZCookie anti-bot — not easily bypassable
- ✅ API endpoints (tree, comments, search, suggest) are **reliably unprotected**
- ✅ `is-ajax=1` parameter converts search results to JSON
- ✅ `limit` parameter works (5, 10, 20, 30, 50, 100)
- ✅ `sort` parameter works (e.g., `publishDate_desc`)

## Workflow Examples

### Daily Scan (Cron Job)
```python
from matsne_api import MatsneAPI
api = MatsneAPI()

# Quick check
dates = api.search_quick()
if not api.has_today():
    print("დღეს რელევანტური ცვლილება არ არის")
    exit()

# Get today's documents
today_docs = api.today_documents()
for doc in today_docs:
    print(f"ID:{doc['id']} | {doc['title']}")
```

### Keyword Monitoring
```python
keywords = ["პერსონალური", "მონაცემ", "ელექტრონული", "შრომის", "საგადასახადო"]
for kw in keywords:
    results = api.suggest(kw)
    active = [r for r in results if r.get("state") == "active"]
    print(f"'{kw}': {len(active)} active laws")
```

### Full Document Analysis
```python
doc = api.get_document(6840140)
print(f"Title: {doc['meta']['title']}")
print(f"Number: {doc['meta']['number']}")
print(f"Organ: {doc['meta']['organ']}")
print(f"Tree: {doc['tree']}")
print(f"Back-refs: {len(doc['back_references'])}")
print(f"Text: {len(doc['text'])} chars")
```

## Files

- **Wrapper:** `matsne_api.py`
- **MCP Server:** `mcp_server.py`
- **Skill:** `SKILL.md`
- **AGENTS.md** — agent instructions (OpenCode / Claude Code)
