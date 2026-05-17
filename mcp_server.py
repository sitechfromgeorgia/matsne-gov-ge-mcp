#!/usr/bin/env python3
"""
MCP server for matsne.gov.ge — Georgia's legislative database.

Exposes 10 tools and 2 resources built on the undocumented JSON API.
"""

import json

from mcp.server.fastmcp import FastMCP

from matsne_api import MatsneAPI

api = MatsneAPI()

app = FastMCP(
    "matsne-ge",
    instructions="Georgia's official legislative database — document search, metadata, and structure",
)


@app.tool(description="Quick keyword autocomplete search — fastest endpoint (~0.5s). Returns up to 50 results with id, title, and active/expired status.")
def matsne_suggest(text: str) -> list[dict]:
    return api.suggest(text)


@app.tool(description="Full-text search with filters. Supports pagination, date range (DD/MM/YYYY), document type, issuer organ, and sort order. Returns structured document list.")
def matsne_search(
    page: int = 0,
    query: str = "",
    limit: int = 20,
    sort: str = "",
    issuer: str = "",
    doc_type: str = "",
    number: str = "",
    registration_code: str = "",
    date_from: str = "",
    date_to: str = "",
) -> dict:
    return api.search(
        page=page, query=query, limit=limit, sort=sort,
        issuer=issuer, doc_type=doc_type, number=number,
        registration_code=registration_code,
        date_from=date_from, date_to=date_to,
    )


@app.tool(description="Get full document: metadata, text, structure tree, back-references, and comments in one call.")
def matsne_get_document(doc_id: int) -> dict:
    return api.get_document(doc_id)


@app.tool(description="Get document structure tree (hierarchical parts with Title and Anchor). Complex codes return deep nested trees.")
def matsne_get_tree(doc_id: int, part_id: int = 0) -> dict:
    return api.get_tree(doc_id, part_id)


@app.tool(description="List documents that cite or reference the given document.")
def matsne_get_back_references(doc_id: int, part_id: int = 0) -> list:
    return api.get_back_references(doc_id, part_id)


@app.tool(description="Get comments on a document or specific part. Returns author, text, rating, and timestamps.")
def matsne_get_comments(doc_id: int, part_id: int = 0) -> list:
    return api.get_comments(doc_id, part_id)


@app.tool(description="Get inline HTML fragment for a linked document part. Useful for viewing referenced document sections.")
def matsne_get_linked(doc_id: int, anchor: str = "DOCUMENT:1;HEADER:1;") -> dict:
    return api.get_linked(doc_id, anchor)


@app.tool(description="Quick keyword search using the suggest endpoint. Returns active documents matching the keyword.")
def matsne_search_by_keyword(keyword: str, max_results: int = 10) -> list[dict]:
    return api.search_by_keyword(keyword, max_results)


@app.tool(description="Check if any documents were published today.")
def matsne_has_today() -> str:
    return "yes" if api.has_today() else "no"


@app.tool(description="Get documents published today (if any).")
def matsne_today_documents() -> list[dict]:
    return api.today_documents()


@app.resource("matsne://document/{doc_id}")
def document_resource(doc_id: int) -> str:
    return json.dumps(api.get_document(doc_id), ensure_ascii=False, indent=2)


@app.resource("matsne://today")
def today_resource() -> str:
    return json.dumps(api.today_documents(), ensure_ascii=False, indent=2)


def main():
    app.run()


if __name__ == "__main__":
    main()
