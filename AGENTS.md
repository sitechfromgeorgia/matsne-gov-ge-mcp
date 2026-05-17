# AGENTS.md — Matsne.gov.ge API Wrapper

## What this is

Pure stdlib Python wrapper for matsne.gov.ge's undocumented JSON API (Georgian legislative database),
plus an MCP server exposing it as tools/resources for AI agents.

**Files:** `matsne_api.py` (802 lines), `SKILL.md` (reference docs), `mcp_server.py` (MCP server),
`pyproject.toml`, `AGENTS.md`, `README.md`, `LICENSE`

## Key facts

- **API wrapper: zero dependencies** — stdlib only (`json`, `re`, `time`, `urllib`, `dataclasses`, `typing`)
- **MCP server: single dependency** (`mcp>=1.0.0`) listed in `pyproject.toml`
- **No tests, no CI/CD, no git repo**

## Commands

```sh
python matsne_api.py                        # runs comprehensive live API test against doc 6840140
uv run mcp_server.py                        # start MCP server (stdio transport)
uv run python -c "from mcp_server import *" # verify imports
```

### Claude Desktop config

```json
{
  "mcpServers": {
    "matsne-ge": {
      "command": "uv",
      "args": ["--directory", "PATH_TO_REPO", "run", "mcp_server.py"]
    }
  }
}
```

## Architecture

### API Wrapper (`matsne_api.py`)

- `MatsneAPI` class — wraps 12+ undocumented JSON endpoints reverse-engineered from Drupal JS
- `DocumentMeta` dataclass — structured container for document metadata
- Rate limit: 0.3s between requests (configurable), exponential backoff on retries (2 retries)
- Cookie tracking for session persistence across requests

### MCP Server (`mcp_server.py`)

- Imports `MatsneAPI` — API wrapper is untouched, MCP is a pure transport layer
- 10 tools (suggest, search, get_document, get_tree, back_references, comments, linked, search_by_keyword, has_today, today_documents)
- 2 resources (`matsne://document/{id}`, `matsne://today`)
- Tools named `matsne_*` to avoid namespace conflicts in clients

## Gotchas

- **`DocumentPart`** in tree response can be a **single object `{}` OR an array `[]`** — always type-check
- **HTML page fetch** (`/ka/document/view/{id}`) is **intermittently blocked** by bot detection — `get_document()` auto-falls back to `get_text_via_linked()` which always works via API
- **Voice server** uses `XZCookie` + `document.ZXKey` anti-bot — not bypassable without browser JS
- Search with `query` param returns different HTML structure than plain search (panel-based vs link-based)
- Titles may contain `<b>` tags from keyword highlighting — strip HTML when parsing
- `is-ajax=1` param converts search results from HTML to JSON
- All date params use `DD/MM/YYYY` format

## Reference

Full endpoint documentation in `SKILL.md` — read it before modifying API methods.
