#!/usr/bin/env python3
"""
Matsne.gov.ge API Wrapper — Production Version
================================================
Reverse-engineered from Drupal's internal JavaScript API.

Endpoints discovered (2026-05-17):
  - POST /document/suggest              — autocomplete search
  - GET  /ka/document/search?is-ajax=1  — JSON search results
  - GET  /ka/document/tree/{id}/{part}  — document structure tree
  - GET  /ka/document/backReferences/{id} — back references
  - GET  /ka/document/comment/{id}/read — comments
  - GET  /ka/document/linked/{id}/{anchor} — inline HTML fragment
  - GET  /annotation/api/search         — annotation search
  - POST /favorites                     — favorites management (auth)
  - GET  /favorites?method=getFavoritesList — favorites list (auth)
  - GET  speech.matsne.gov.ge:443/voice — text-to-speech

Usage:
    from matsne_api import MatsneAPI
    api = MatsneAPI()
    results = api.suggest("პერსონალური")
    doc = api.get_document(6840140)
    tree = api.get_tree(6840140)
    recent = api.search(page=0)
"""

import json
import re
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentMeta:
    """Structured document metadata."""
    id: int
    title: str = ""
    number: str = ""
    organ: str = ""
    date_received: str = ""
    date_published: str = ""
    doc_type: str = ""
    registration_code: str = ""
    status: str = ""  # active/expired
    url: str = ""
    text: str = ""
    tree: dict = field(default_factory=dict)
    back_references: list = field(default_factory=list)
    comments: list = field(default_factory=list)


class MatsneAPI:
    """Production wrapper around matsne.gov.ge's hidden Drupal API."""

    BASE = "https://matsne.gov.ge"
    VOICE_BASE = "https://speech.matsne.gov.ge:443"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    def __init__(self, lang: str = "ka", rate_limit: float = 0.3):
        """
        Args:
            lang: Language prefix ('ka' for Georgian, 'en' for English)
            rate_limit: Minimum seconds between requests (default 0.3s)
        """
        self.lang = lang
        self.rate_limit = rate_limit
        self._cookies = {}
        self._last_request_time = 0

    def _wait_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _request(self, url: str, method: str = "GET",
                 data: Optional[dict] = None,
                 accept_json: bool = False,
                 retries: int = 2) -> str:
        """Make HTTP request with proper headers, cookies, and retry logic."""
        self._wait_rate_limit()

        headers = {
            "User-Agent": self.UA,
            "Accept": "application/json" if accept_json else "text/html,application/xhtml+xml",
            "Accept-Language": "ka,en;q=0.9",
        }
        if accept_json:
            headers["X-Requested-With"] = "XMLHttpRequest"

        # Add cookies
        if self._cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in self._cookies.items())
            headers["Cookie"] = cookie_str

        body = None
        if data:
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    # Save cookies
                    for header in resp.headers.get_all("Set-Cookie") or []:
                        m = re.match(r'([^=]+)=([^;]+)', header.strip())
                        if m:
                            self._cookies[m.group(1)] = m.group(2)
                    return resp.read().decode("utf-8")
            except Exception as e:
                if attempt < retries:
                    time.sleep(1 * (attempt + 1))  # exponential backoff
                    continue
                return f"ERROR: {e}"

    # ── Public API Endpoints ───────────────────────────────────

    def suggest(self, text: str) -> list[dict]:
        """
        POST /document/suggest — autocomplete search.

        Returns list of matching documents with {id, state, title}.
        Fast (~0.58s), returns up to 50 results.

        Args:
            text: Search query (Georgian text)

        Returns:
            [{"id": int, "state": "active"|"expired", "title": str}, ...]
        """
        url = f"{self.BASE}/document/suggest"
        raw = self._request(url, method="POST", data={"text": text})
        if raw.startswith("ERROR"):
            return [{"error": raw}]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return [{"error": "Invalid JSON", "raw": raw[:200]}]

    def search(self, page: int = 0, query: str = "",
               limit: int = 20, sort: str = "",
               issuer: str = "", doc_type: str = "",
               number: str = "", registration_code: str = "",
               date_from: str = "", date_to: str = "") -> dict:
        """
        GET /ka/document/search — search with JSON response.

        Uses is-ajax=1 parameter to get JSON instead of full HTML page.

        Args:
            page: Page number (0-indexed)
            query: Full-text search query
            limit: Results per page (5, 10, 20, 30, 50, 100)
            sort: Sort order (e.g., 'publishDate_desc')
            issuer: Document issuer/organ filter
            doc_type: Document type filter
            number: Document number filter
            registration_code: Registration code filter
            date_from: Date from (DD/MM/YYYY format)
            date_to: Date to (DD/MM/YYYY format)

        Returns:
            {"documents": [...], "count": int, "raw_pagination": str}
        """
        params = {"page": page, "is-ajax": 1}
        if query:
            params["query"] = query
        if limit != 20:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if issuer:
            params["issuer"] = issuer
        if doc_type:
            params["type"] = doc_type
        if number:
            params["number"] = number
        if registration_code:
            params["registration_code"] = registration_code
        if date_from:
            params["signing_date_fr[date]"] = date_from
        if date_to:
            params["signing_date_to[date]"] = date_to

        url = f"{self.BASE}/{self.lang}/document/search?{urllib.parse.urlencode(params)}"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

        # Parse documents_list HTML into structured data
        docs = []
        html = data.get("documents_list", "")

        # Try panel-based structure (used with query search)
        if '<div class="panel' in html:
            panels = re.split(r'<div class="panel panel-success document-search-result-item">', html)
            for panel in panels[1:]:
                doc = self._parse_panel(panel)
                if doc:
                    docs.append(doc)
        else:
            # Fallback: simple link-based structure
            blocks = re.split(r'<p><a href="/ka/document/view/', html)
            for block in blocks[1:]:
                doc_id_m = re.match(r'([0-9]+)', block)
                if not doc_id_m:
                    continue
                doc_id = int(doc_id_m.group(1))
                title_m = re.search(r'">([^<]+)</a>', block)
                title = title_m.group(1).strip() if title_m else "N/A"
                date_m = re.search(r'<small>(\d{2}/\d{2}/\d{4})', block)
                date = date_m.group(1) if date_m else "N/A"
                docs.append({
                    "id": doc_id,
                    "title": title,
                    "date": date,
                    "url": f"{self.BASE}/ka/document/view/{doc_id}"
                })

        return {
            "documents": docs,
            "count": len(docs),
            "raw_pagination": data.get("pagination", "")
        }

    def _parse_panel(self, panel_html: str) -> Optional[dict]:
        """Parse a single panel block from search results."""
        # Document link and title
        link_m = re.search(r'href="/ka/document/view/(\d+)"[^>]*>(.*?)</a>', panel_html, re.DOTALL)
        if not link_m:
            return None
        doc_id = int(link_m.group(1))
        title = re.sub(r'<[^>]+>', '', link_m.group(2)).strip()

        # Date
        date_m = re.search(r'<small>(\d{2}/\d{2}/\d{4})', panel_html)
        date = date_m.group(1) if date_m else ""

        # Document type
        type_m = re.search(r'<li>\s*<small>([^<●]+)</small>', panel_html)
        doc_type = type_m.group(1).strip() if type_m else ""

        # Organ
        organ_m = re.search(r'<small>●</small>\s*</li>\s*<li>\s*<small>([^<]+)</small>', panel_html)
        organ = organ_m.group(1).strip() if organ_m else ""

        return {
            "id": doc_id,
            "title": title,
            "date": date,
            "doc_type": doc_type,
            "organ": organ,
            "url": f"{self.BASE}/ka/document/view/{doc_id}"
        }

    def search_quick(self) -> list[str]:
        """
        Quick check: what dates are on the first search page?
        Returns list of unique dates (DD/MM/YYYY format), newest first.
        """
        url = f"{self.BASE}/{self.lang}/document/search?page=0"
        html = self._request(url)
        if html.startswith("ERROR"):
            return []
        dates = re.findall(r'<small>(\d{2}/\d{2}/\d{4})', html)
        return sorted(set(dates), reverse=True)

    def get_tree(self, doc_id: int, part_id: int = 0) -> dict:
        """
        GET /ka/document/tree/{id}/{part} — document structure tree.

        Returns hierarchical structure with Title, Anchor, DocumentPart.
        Complex documents (codes) return deep nested trees.

        Args:
            doc_id: Document ID
            part_id: Part ID (usually 0)

        Returns:
            {"Title": str, "Anchor": str, "DocumentPart": {...}|[...]}
        """
        url = f"{self.BASE}/ka/document/tree/{doc_id}/{part_id}"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def get_back_references(self, doc_id: int, part_id: int = 0) -> list:
        """
        GET /ka/document/backReferences/{id}?part_id=X

        Returns documents that reference this document.
        """
        url = f"{self.BASE}/ka/document/backReferences/{doc_id}?part_id={part_id}"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def get_comments(self, doc_id: int, part_id: int = 0) -> list:
        """
        GET /ka/document/comment/{id}/read?part_id=X

        Returns comments on a document. Each comment has:
        {cid, text, html, anchor, rating, author: {name, fullName, uid},
         created, formattedCreate, changed, formattedChange}
        """
        url = f"{self.BASE}/ka/document/comment/{doc_id}/read?part_id={part_id}"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def get_linked(self, doc_id: int, anchor: str = "document") -> dict:
        """
        GET /ka/document/linked/{id}/{anchor} — inline HTML fragment.

        Returns HTML content for a specific document part.
        Used for inline viewing of linked documents.

        Args:
            doc_id: Document ID
            anchor: Document anchor (e.g., "DOCUMENT:1;HEADER:1;")

        Returns:
            {"html": str}
        """
        url = f"{self.BASE}/ka/document/linked/{doc_id}/{anchor}"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def get_annotations(self, uri: str) -> dict:
        """
        GET /annotation/api/search?uri=...

        Returns annotations for a document URL.

        Args:
            uri: Document URI (e.g., "document/view/6840140")

        Returns:
            {"total": int, "rows": [...]}
        """
        url = f"{self.BASE}/annotation/api/search?uri={urllib.parse.quote(uri)}"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    # ── Authenticated Endpoints (require login) ────────────────

    def add_comment(self, doc_id: int, anchor: str, text: str, title: str = "") -> dict:
        """
        POST /ka/document/comment/{id}/create — create comment (AUTH REQUIRED).

        Args:
            doc_id: Document ID
            anchor: Document anchor (e.g., "DOCUMENT:1;")
            text: Comment text
            title: Comment title (optional)

        Returns:
            {"cid": int, ...} on success
        """
        url = f"{self.BASE}/ka/document/comment/{doc_id}/create"
        data = {"anchor": anchor, "text": text}
        if title:
            data["title"] = title
        raw = self._request(url, method="POST", data=data, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def update_comment(self, comment_id: int, text: str) -> dict:
        """
        POST /ka/document/comment/{cid}/update — update comment (AUTH REQUIRED).
        """
        url = f"{self.BASE}/ka/document/comment/{comment_id}/update"
        raw = self._request(url, method="POST", data={"text": text}, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def remove_comment(self, comment_id: int) -> dict:
        """
        GET /ka/document/comment/{cid}/remove — delete comment (AUTH REQUIRED).
        """
        url = f"{self.BASE}/ka/document/comment/{comment_id}/remove"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def add_favorite(self, doc_id: int) -> dict:
        """
        POST /favorites — add document to favorites (AUTH REQUIRED).
        """
        url = f"{self.BASE}/favorites"
        raw = self._request(url, method="POST",
                           data={"documentId": doc_id, "method": "add"},
                           accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def remove_favorite(self, doc_id: int) -> dict:
        """
        POST /favorites — remove document from favorites (AUTH REQUIRED).
        """
        url = f"{self.BASE}/favorites"
        raw = self._request(url, method="POST",
                           data={"documentId": doc_id, "method": "remove"},
                           accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    def get_favorites_list(self) -> dict:
        """
        GET /favorites?method=getFavoritesList — get favorites (AUTH REQUIRED).
        """
        url = f"{self.BASE}/favorites?method=getFavoritesList"
        raw = self._request(url, accept_json=True)
        if raw.startswith("ERROR"):
            return {"error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": raw[:200]}

    # ── Voice Server ───────────────────────────────────────────

    def get_voice_url(self, text: str) -> str:
        """
        Get text-to-speech URL for short text.
        Note: Uses anti-bot protection (XZCookie + document.ZXKey).
        """
        return f"{self.VOICE_BASE}/voice?t={urllib.parse.quote(text)}"

    def get_voice_url_big(self, doc_id: int) -> str:
        """
        Get text-to-speech URL for full document.
        POST to this URL with: t=text, r=rate, docId=id, pubId=0
        """
        return f"{self.VOICE_BASE}/voice/big"

    # ── Document HTML (may be blocked by bot detection) ─────────

    def get_document_html(self, doc_id: int) -> str:
        """
        GET /ka/document/view/{id} — raw HTML page.

        ⚠️ INTERMITTENTLY BLOCKED by bot detection.
        Some IDs work, some return "Access Denied".
        Use as primary attempt, fall back to browser tools.
        """
        url = f"{self.BASE}/{self.lang}/document/view/{doc_id}"
        return self._request(url)

    def parse_document_meta(self, html: str, doc_id: int) -> DocumentMeta:
        """Parse document metadata from HTML table."""
        meta = DocumentMeta(id=doc_id, title="", url=f"{self.BASE}/ka/document/view/{doc_id}")

        # Title from <title> tag
        m = re.search(r'<title>([^<|]+)', html)
        if m:
            meta.title = m.group(1).strip().strip('"').strip('\u201e').strip('\u201c')

        # Find metadata table
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
        for table_html in tables:
            if "დოკუმენტის ნომერი" not in table_html:
                continue
            rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) < 2:
                    continue
                label = re.sub(r'<[^>]+>', '', cells[0]).strip()
                value = re.sub(r'<[^>]+>', '', cells[1]).strip()
                if "ნომერი" in label:
                    meta.number = value
                elif "მიმღები" in label:
                    meta.organ = value
                elif "მიღების" in label:
                    meta.date_received = value
                elif "გამოქვეყნების" in label:
                    meta.date_published = value
                elif "ტიპი" in label:
                    meta.doc_type = value
                elif "რეგისტრაციო" in label:
                    meta.registration_code = value
            break

        # Main document text
        main = re.search(r'id="maindoc"[^>]*>(.*?)$', html, re.DOTALL)
        if main:
            text = re.sub(r'<[^>]+>', '\n', main.group(1)[:100000])
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            meta.text = '\n'.join(lines[:500])

        return meta

    def _collect_anchors(self, part: dict | list, max_depth: int = 10) -> list[str]:
        """Recursively collect all anchors from a document tree part."""
        anchors = []
        if isinstance(part, dict):
            anchor = part.get("Anchor", "")
            if anchor and anchor != "DOCUMENT:1;":
                anchors.append(anchor)
            dp = part.get("DocumentPart")
            if max_depth > 0:
                anchors.extend(self._collect_anchors(dp, max_depth - 1))
        elif isinstance(part, list):
            for item in part:
                if max_depth > 0:
                    anchors.extend(self._collect_anchors(item, max_depth - 1))
        return anchors

    def get_text_via_linked(self, doc_id: int, tree: dict) -> str:
        """Get document text by fetching linked fragments for every tree anchor.

        Always available (uses API endpoint, not HTML page).
        """
        anchors = self._collect_anchors(tree)
        texts = []
        for anchor in anchors[:100]:
            linked = self.get_linked(doc_id, anchor)
            if "error" not in linked:
                html = linked.get("html", "")
                text = re.sub(r'<[^>]+>', '\n', html)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                texts.extend(lines)
        return '\n'.join(texts)

    def get_document(self, doc_id: int) -> dict:
        """
        Get full document: metadata + text + tree + back-references + comments.

        Uses multiple endpoints:
        1. HTML page (may be blocked) → metadata + text
        2. get_text_via_linked() → reliable text via API (fallback)
        3. Tree endpoint → document structure
        4. Back-references → citing documents
        5. Comments → user comments

        Returns dict with all available data.
        """
        result = {
            "id": doc_id,
            "url": f"{self.BASE}/ka/document/view/{doc_id}",
            "meta": {},
            "text": "",
            "tree": {},
            "back_references": [],
            "comments": [],
            "linked_docs": [],
            "errors": []
        }

        # 1. Get tree structure — needed early for text fallback
        tree = self.get_tree(doc_id)
        if "error" not in tree:
            result["tree"] = tree

        # 2. Get text — try HTML first, fall back to linked fragments
        html = self.get_document_html(doc_id)
        if html.startswith("ERROR"):
            result["errors"].append(f"HTML fetch failed: {html}")
        elif "Access Denied" in html:
            result["errors"].append("HTML fetch blocked (Access Denied)")
        else:
            meta = self.parse_document_meta(html, doc_id)
            result["meta"] = {
                "title": meta.title,
                "number": meta.number,
                "organ": meta.organ,
                "date_received": meta.date_received,
                "date_published": meta.date_published,
                "doc_type": meta.doc_type,
                "registration_code": meta.registration_code,
            }
            result["text"] = meta.text

        # If HTML text is empty/missing, use tree-based fallback
        if result["tree"] and not result["text"]:
            result["text"] = self.get_text_via_linked(doc_id, result["tree"])
            if result["text"]:
                result["meta"]["title"] = result["tree"].get("Title", "")

        # 3. Get back-references
        refs = self.get_back_references(doc_id)
        result["back_references"] = refs

        # 4. Get comments
        comments = self.get_comments(doc_id)
        result["comments"] = comments

        return result

    def has_today(self) -> bool:
        """Check if today's documents are published."""
        from datetime import datetime
        today = datetime.now().strftime("%d/%m/%Y")
        dates = self.search_quick()
        return today in dates

    def today_documents(self) -> list[dict]:
        """Get today's documents (if any)."""
        from datetime import datetime
        today = datetime.now().strftime("%d/%m/%Y")
        result = self.search(page=0)
        if "error" in result:
            return []
        return [d for d in result.get("documents", []) if d.get("date") == today]

    def search_by_keyword(self, keyword: str, max_results: int = 10) -> list[dict]:
        """
        Search using suggest endpoint for quick keyword matching.
        Returns active documents matching the keyword.
        """
        suggestions = self.suggest(keyword)
        results = []
        for s in suggestions[:max_results]:
            if "error" in s:
                continue
            results.append({
                "id": s.get("id"),
                "title": s.get("title"),
                "status": s.get("state"),
                "url": f"{self.BASE}/ka/document/view/{s.get('id')}"
            })
        return results

    def get_document_by_type(self, doc_id: int) -> dict:
        """
        Get document and detect its type from tree structure.
        Returns document data with detected type.
        """
        doc = self.get_document(doc_id)
        tree = doc.get("tree", {})
        if tree and "Title" in tree:
            doc["detected_type"] = self._detect_doc_type(tree)
        return doc

    def _detect_doc_type(self, tree: dict) -> str:
        """Detect document type from tree structure."""
        title = tree.get("Title", "").lower()
        if "კანონი" in title:
            return "law"
        elif "ბრძანებულება" in title:
            return "decree"
        elif "დადგენილება" in title:
            return "resolution"
        elif "კოდექსი" in title:
            return "code"
        elif "ბრძანება" in title:
            return "order"
        else:
            return "other"


# ── CLI Test ───────────────────────────────────────────────────

if __name__ == "__main__":
    api = MatsneAPI()

    print("=" * 60)
    print("🔍 MATSNE.GOV.GE API WRAPPER — FULL TEST")
    print("=" * 60)

    # 1. Quick check — today's dates
    print("\n📅 Recent dates on search page:")
    dates = api.search_quick()
    for d in dates[:5]:
        print(f"  {d}")
    print(f"  Today published: {'✅ YES' if api.has_today() else '❌ NO'}")

    # 2. Search recent documents
    print("\n📄 Recent documents (first page):")
    recent = api.search(page=0)
    if "error" not in recent:
        for doc in recent["documents"][:5]:
            print(f"  {doc.get('date', 'N/A')} | ID:{doc['id']} | {doc['title'][:60]}")
    else:
        print(f"  Error: {recent['error']}")

    # 3. Search with query
    print("\n🔎 Search 'პერსონალური' (with query):")
    results = api.search(page=0, query="პერსონალური", limit=5)
    if "error" not in results:
        for doc in results["documents"][:5]:
            print(f"  {doc.get('date', 'N/A')} | ID:{doc['id']} | {doc['title'][:60]}")
    else:
        print(f"  Error: {results['error']}")

    # 4. Suggest search
    print("\n🔎 Suggest: 'შრომის':")
    suggest_results = api.suggest("შრომის")
    for r in suggest_results[:5]:
        if "error" not in r:
            print(f"  [{r['state']}] ID:{r['id']} | {r['title'][:60]}")

    # 5. Get full document
    print("\n📑 Document 6840140 (full):")
    doc = api.get_document(6840140)
    print(f"  Title: {doc['meta'].get('title', 'N/A')[:60]}")
    print(f"  Number: {doc['meta'].get('number', 'N/A')}")
    print(f"  Organ: {doc['meta'].get('organ', 'N/A')}")
    print(f"  Type: {doc['meta'].get('doc_type', 'N/A')}")
    print(f"  Tree: {'✅' if doc['tree'] else '❌'}")
    print(f"  Back-refs: {len(doc['back_references'])} refs")
    print(f"  Comments: {len(doc['comments'])} comments")
    print(f"  Text: {len(doc['text'])} chars")
    print(f"  Errors: {doc['errors'] or 'None'}")

    # 6. Tree endpoint
    print("\n🌳 Tree for 6840140:")
    tree = api.get_tree(6840140)
    if "error" not in tree:
        print(f"  Title: {tree.get('Title', 'N/A')}")
        print(f"  Anchor: {tree.get('Anchor', 'N/A')}")
        if "DocumentPart" in tree:
            dp = tree["DocumentPart"]
            if isinstance(dp, list):
                print(f"  Parts: {len(dp)}")
            elif isinstance(dp, dict):
                print(f"  Part: {dp.get('Title', 'N/A')}")

    # 7. Linked document
    print("\n🔗 Linked doc 6840140:")
    linked = api.get_linked(6840140, "DOCUMENT:1;HEADER:1;")
    if "error" not in linked:
        html = linked.get("html", "")
        print(f"  HTML length: {len(html)} chars")
        print(f"  Preview: {html[:100]}...")

    # 8. Back references
    print("\n📎 Back references for 6840140:")
    refs = api.get_back_references(6840140)
    print(f"  Count: {len(refs)}")
    if refs:
        for r in refs[:3]:
            print(f"  {r}")

    # 9. Comments
    print("\n💬 Comments for 6840140:")
    comments = api.get_comments(6840140)
    print(f"  Count: {len(comments)}")

    # 10. Today's documents
    print("\n📆 Today's documents:")
    today_docs = api.today_documents()
    if today_docs:
        for d in today_docs:
            print(f"  ID:{d['id']} | {d['title'][:60]}")
    else:
        print("  No documents published today")

    print("\n✅ Full test complete!")
