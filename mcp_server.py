#!/usr/bin/env python3
"""
MCP server for Georgia's legal ecosystem.

Sources:
  - matsne.gov.ge    - legislation (საკანონმდებლო მაცნე)
  - ecd.court.ge     - common courts' decisions & acts (საქმისწარმოების სისტემა)
  - supremecourt.ge  - Supreme Court cassation + Grand Chamber decisions

Exposes search / full-text / classifiers / verification tools so any AI agent
can research Georgian law and court practice end-to-end.
"""

import json

from mcp.server.fastmcp import FastMCP

from matsne_api import MatsneAPI
from court_api import EcdCourtAPI, SupremeCourtAPI
from higher_courts_api import ConstitutionalCourtAPI, EchrAPI

matsne = MatsneAPI()
ecd = EcdCourtAPI()
supreme = SupremeCourtAPI()
constcourt = ConstitutionalCourtAPI()
echr = EchrAPI()

app = FastMCP(
    "matsne-ge",
    instructions=(
        "Georgia's legal ecosystem: legislation (matsne.gov.ge), common-court "
        "decisions and acts (ecd.court.ge), Supreme Court cassation + Grand "
        "Chamber (supremecourt.ge), Constitutional Court (constcourt.ge), and "
        "the European Court of Human Rights (HUDOC). "
        "Every court result carries an authority_level so you weigh precedent "
        "correctly: 7=ECHR (supranational), 6=Constitutional Court, 5=Supreme "
        "Grand Chamber (binding on all common courts), 4=Supreme cassation, "
        "3=appeals, 2=first instance. "
        "IMPORTANT: HUDOC (echr_* tools) rate-limits aggressively — make echr "
        "requests sequentially (one at a time, wait between calls) and never "
        "fire many in parallel; if a call returns an empty/error result, pause "
        "a few seconds and retry once. Verify every citation against the "
        "returned stable URL before relying on it."
    ),
)


# ── Matsne (legislation) ─────────────────────────────────────

@app.tool(description="Quick keyword autocomplete search of legislation — fastest endpoint (~0.5s). Returns up to 50 results with id, title, and active/expired status.")
def matsne_suggest(text: str) -> list[dict]:
    return matsne.suggest(text)


@app.tool(description="Full-text legislative search with filters. Supports pagination, date range (DD/MM/YYYY), document type, issuer organ, and sort order.")
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
    return matsne.search(
        page=page, query=query, limit=limit, sort=sort,
        issuer=issuer, doc_type=doc_type, number=number,
        registration_code=registration_code,
        date_from=date_from, date_to=date_to,
    )


@app.tool(description="Get full legislative document: metadata, text, structure tree, back-references, and comments in one call.")
def matsne_get_document(doc_id: int) -> dict:
    return matsne.get_document(doc_id)


@app.tool(description="Get legislative document structure tree (hierarchical parts with Title and Anchor). Complex codes return deep nested trees.")
def matsne_get_tree(doc_id: int, part_id: int = 0) -> dict:
    return matsne.get_tree(doc_id, part_id)


@app.tool(description="List documents that cite or reference the given legislative document.")
def matsne_get_back_references(doc_id: int, part_id: int = 0) -> list:
    return matsne.get_back_references(doc_id, part_id)


@app.tool(description="Get comments on a legislative document or specific part.")
def matsne_get_comments(doc_id: int, part_id: int = 0) -> list:
    return matsne.get_comments(doc_id, part_id)


@app.tool(description="Get inline HTML fragment for a linked legislative document part.")
def matsne_get_linked(doc_id: int, anchor: str = "DOCUMENT:1;HEADER:1;") -> dict:
    return matsne.get_linked(doc_id, anchor)


@app.tool(description="Quick keyword search of active legislation using the suggest endpoint.")
def matsne_search_by_keyword(keyword: str, max_results: int = 10) -> list[dict]:
    return matsne.search_by_keyword(keyword, max_results)


@app.tool(description="Check if any legislative documents were published today.")
def matsne_has_today() -> str:
    return "yes" if matsne.has_today() else "no"


@app.tool(description="Get legislative documents published today (if any).")
def matsne_today_documents() -> list[dict]:
    return matsne.today_documents()


# ── Common courts (ecd.court.ge) ─────────────────────────────

@app.tool(description="Search common-court decisions. Filters: case number, decision date range (YYYY-MM-DD), instance (1=first, 2=appeals, 3=supreme), court code, case category, litigation type (dispute category/article/მუხლი), decision type, and full-text terms. Use court_classifiers to look up filter ids. Results carry authority_level.")
def court_search_decisions(
    case_no: str = "",
    date_from: str = "",
    date_to: str = "",
    instance_id: str = "",
    court_code: str = "",
    case_category_id: str = "",
    litigation_type_id: str = "",
    type_id: str = "",
    texts: list[str] = None,
    skip: int = 0,
    take: int = 20,
) -> dict:
    return ecd.search_decisions(
        case_no=case_no,
        date_from=date_from or None,
        date_to=date_to or None,
        instance_id=instance_id or "",
        court_code=court_code or "",
        case_category_id=case_category_id or "",
        litigation_type_id=litigation_type_id or "",
        type_id=type_id or "",
        texts=texts or [],
        skip=skip, take=take,
    )


@app.tool(description="Get the full text of a common-court decision by its DecisionDocumentId and InstanceId (both come from court_search_decisions results).")
def court_get_decision(decision_document_id: int, instance_id: int) -> dict:
    return ecd.get_decision(decision_document_id, instance_id)


@app.tool(description="Look up classifier dictionaries for decision search filters. kind: instances, courts, case_categories, litigation_types, decision_types. Pass instance_id and/or case_category_id to cascade.")
def court_classifiers(
    kind: str = "instances",
    instance_id: str = "",
    case_category_id: str = "",
    filter_text: str = "",
) -> dict:
    iid = instance_id or None
    cid = case_category_id or None
    if kind == "instances":
        return ecd.get_instances()
    if kind == "courts":
        return ecd.get_courts(iid)
    if kind == "case_categories":
        return ecd.get_case_categories(iid, filter_text)
    if kind == "litigation_types":
        return ecd.get_litigation_types(iid, cid, filter_text)
    if kind == "decision_types":
        return ecd.get_decision_types(iid, filter_text)
    return {"error": f"Unknown kind: {kind}"}


@app.tool(description="Verify a court act (სასამართლო აქტი) by its barcode (შტრიხკოდი) and case number. Returns the document name and a PDF download link.")
def court_verify_act(barcode: str, case_no: str) -> dict:
    return ecd.verify_act(barcode, case_no)


# ── Supreme Court (supremecourt.ge) ──────────────────────────

@app.tool(description="Search Supreme Court cassation decisions. palata: 0=administrative, 1=civil, 2=criminal. Filters: case number, date range (YYYY/MM/DD), judge, result code, appeal-type code, category/kind, and up to 6 full-text terms. Result codes are in the tool description of supreme_classifiers.")
def supreme_search(
    palata: int = 1,
    page: int = 1,
    texts: list[str] = None,
    case_number: str = "",
    date_from: str = "",
    date_to: str = "",
    judge: str = "",
    result: str = "",
    appeal_type: str = "",
    category: str = "",
    kind: str = "",
) -> dict:
    return supreme.search_cases(
        palata=palata, page=page, texts=texts or [],
        case_number=case_number, date_from=date_from, date_to=date_to,
        judge=judge, result=result, appeal_type=appeal_type,
        category=category, kind=kind,
    )


@app.tool(description="Get the full text of a Supreme Court cassation decision by case id and palata (both come from supreme_search results).")
def supreme_get_case(case_id: int, palata: int) -> dict:
    return supreme.get_case(case_id, palata)


@app.tool(description="Supreme Court result (shedegi) and appeal-type (sSaxe) codes for the supreme_search filters.")
def supreme_classifiers() -> dict:
    return {
        "result_codes": supreme.RESULT_CODES,
        "appeal_type_codes": supreme.APPEAL_TYPE_CODES,
        "palata": supreme.PALATA,
    }


@app.tool(description="Supreme Court GRAND CHAMBER decisions — the binding norm interpretations (authority_level 5, mandatory for all common courts). category: civil, criminal, admin, or norms (compiled norm interpretations). Returns PDF links; the title includes date + case number + summary.")
def supreme_grand_chamber(category: str = "civil") -> dict:
    return supreme.grand_chamber(category)


# ── Constitutional Court (constcourt.ge) ─────────────────────

@app.tool(description="Search Constitutional Court of Georgia judicial acts. Filters: fullsearch (name/number/result), intext (full-text inside act texts), number (e.g. 'N1/21/1727'), name, date range, quantity (10-100), sort. Results carry authority_level 6.")
def constitutional_search_acts(
    fullsearch: str = "",
    intext: str = "",
    number: str = "",
    name: str = "",
    date_from: str = "",
    date_to: str = "",
    quantity: int = 20,
    sort: str = "",
) -> dict:
    return constcourt.search_acts(
        fullsearch=fullsearch, intext=intext, number=number, name=name,
        date_from=date_from, date_to=date_to, quantity=quantity, sort=sort,
    )


@app.tool(description="Get the full text of a Constitutional Court act by its legal id (from constitutional_search_acts results).")
def constitutional_get_act(legal_id: int) -> dict:
    return constcourt.get_act(legal_id)


# ── European Court of Human Rights (HUDOC) ───────────────────

@app.tool(description="Search European Court of Human Rights case law (HUDOC). Filters: respondent state code (e.g. 'GEO' for Georgia), Convention article (e.g. '6', '8'), application number, free-text keyword, language. Results carry authority_level 7. NOTE: HUDOC rate-limits aggressively — call sequentially (not in parallel), and if a call returns empty/error, pause a few seconds and retry once.")
def echr_search(
    respondent: str = "",
    article: str = "",
    appno: str = "",
    text: str = "",
    language: str = "ENG",
    start: int = 0,
    length: int = 20,
) -> dict:
    return echr.search(
        respondent=respondent, article=article, appno=appno, text=text,
        language=language, start=start, length=length,
    )


@app.tool(description="Get the full text of an ECHR decision by its HUDOC itemid (from echr_search results). NOTE: HUDOC rate-limits — call sequentially and retry once if empty/error.")
def echr_get_case(itemid: str) -> dict:
    return echr.get_case(itemid)


# ── Resources ────────────────────────────────────────────────

@app.resource("matsne://document/{doc_id}")
def document_resource(doc_id: int) -> str:
    return json.dumps(matsne.get_document(doc_id), ensure_ascii=False, indent=2)


@app.resource("matsne://today")
def today_resource() -> str:
    return json.dumps(matsne.today_documents(), ensure_ascii=False, indent=2)


@app.resource("court://decision/{decision_document_id}/{instance_id}")
def court_decision_resource(decision_document_id: int, instance_id: int) -> str:
    return json.dumps(ecd.get_decision(decision_document_id, instance_id),
                      ensure_ascii=False, indent=2)


@app.resource("supreme://case/{case_id}/{palata}")
def supreme_case_resource(case_id: int, palata: int) -> str:
    return json.dumps(supreme.get_case(case_id, palata),
                      ensure_ascii=False, indent=2)


@app.resource("constitutional://act/{legal_id}")
def constitutional_act_resource(legal_id: int) -> str:
    return json.dumps(constcourt.get_act(legal_id), ensure_ascii=False, indent=2)


@app.resource("echr://case/{itemid}")
def echr_case_resource(itemid: str) -> str:
    return json.dumps(echr.get_case(itemid), ensure_ascii=False, indent=2)


def main():
    app.run()


if __name__ == "__main__":
    main()
