"""Fetch PMC papers and convert to structured JSON with rich metadata."""

import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import time
from datetime import datetime, timezone

PMC_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_pmc_papers(query: str, max_results: int = 5) -> list[dict]:
    """Search PMC for open-access papers."""
    search_url = f"{PMC_API}/esearch.fcgi"
    params = {
        "db": "pmc",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }

    resp = requests.get(search_url, params=params)
    resp.raise_for_status()

    data = resp.json()
    pmcids = data.get("esearchresult", {}).get("idlist", [])

    return [{"pmcid": pmcid} for pmcid in pmcids]


def fetch_pmc_full_text(pmcid: str) -> dict:
    """Fetch full text and metadata from PMC paper."""
    fetch_url = f"{PMC_API}/efetch.fcgi"
    params = {
        "db": "pmc",
        "id": pmcid,
        "rettype": "xml",
    }

    resp = requests.get(fetch_url, params=params)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    # Extract title
    title_elem = root.find(".//article-title")
    title = title_elem.text if title_elem is not None else "Unknown"

    # Extract abstract
    abstract_elem = root.find(".//abstract")
    abstract = ""
    if abstract_elem is not None:
        abstract_parts = []
        for p in abstract_elem.findall(".//p"):
            text = "".join(p.itertext()).strip()
            if text:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

    # Extract full text body
    body_elem = root.find(".//body")
    full_text = ""
    if body_elem is not None:
        text_parts = []
        for p in body_elem.findall(".//p"):
            text = "".join(p.itertext()).strip()
            if text:
                text_parts.append(text)
        full_text = "\n\n".join(text_parts)

    # Extract authors
    authors = []
    for contrib in root.findall(".//contrib[@contrib-type='author']"):
        name_elem = contrib.find(".//name")
        if name_elem is not None:
            surname = name_elem.findtext("surname", "")
            given_names = name_elem.findtext("given-names", "")
            aff_elem = contrib.find(".//aff")
            affiliation = aff_elem.text if aff_elem is not None else ""
            authors.append(
                {
                    "name": f"{given_names} {surname}".strip(),
                    "affiliation": affiliation,
                    "role": "author",
                }
            )

    # Extract publication date
    pub_date_elem = root.find(".//pub-date[@pub-type='epub']") or root.find(
        ".//pub-date[@pub-type='ppub']"
    )
    pub_date = None
    if pub_date_elem is not None:
        year = pub_date_elem.findtext("year")
        month = pub_date_elem.findtext("month", "01")
        day = pub_date_elem.findtext("day", "01")
        try:
            pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pub_date = year

    # Extract keywords
    keywords = []
    for kwd in root.findall(".//kwd"):
        if kwd.text:
            keywords.append(kwd.text)

    # Extract journal info
    journal_elem = root.find(".//journal-title")
    journal = journal_elem.text if journal_elem is not None else ""

    # Extract volume, issue, pages
    volume = root.findtext(".//volume")
    issue = root.findtext(".//issue")
    fpage = root.findtext(".//fpage")
    lpage = root.findtext(".//lpage")

    return {
        "pmcid": pmcid,
        "title": title,
        "abstract": abstract,
        "full_text": full_text,
        "authors": authors,
        "publication_date": pub_date,
        "keywords": keywords,
        "journal": journal,
        "volume": volume,
        "issue": issue,
        "pages": f"{fpage}-{lpage}" if fpage and lpage else None,
    }


def papers_to_json(papers: list[dict], output_path: Path) -> str:
    """Convert fetched papers to JSON format with rich metadata."""
    json_docs = []

    for idx, paper in enumerate(papers):
        doc = {
            "id": f"PMC-{paper['pmcid']}",
            "title": paper["title"],
            "content": f"{paper['abstract']}\n\n{paper['full_text']}",
            "document_type": "research_paper",
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
            "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "source": {
                "type": "pubmed_central",
                "pmcid": paper["pmcid"],
                "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{paper['pmcid']}/",
                "accessed_at": datetime.now(timezone.utc).isoformat() + "Z",
            },
            "publication_info": {
                "title": paper["title"],
                "journal": paper["journal"],
                "publication_date": paper["publication_date"],
                "volume": paper["volume"],
                "issue": paper["issue"],
                "pages": paper["pages"],
            },
            "article_metadata": {
                "abstract": paper["abstract"],
                "keywords": paper["keywords"],
                "article_sections": [
                    "abstract",
                    "introduction",
                    "methods",
                    "results",
                    "discussion",
                    "conclusion",
                ],
            },
            "authors": paper["authors"],
            "research_data": {
                "study_type": "literature_review",
                "study_design": "unknown",
                "sample_size": None,
                "outcomes": paper["keywords"][:3] if paper["keywords"] else [],
            },
            "tags": ["pubmed_central", "research"] + paper["keywords"][:5],
            "status": "indexed",
            "confidentiality_level": "public",
        }
        json_docs.append(doc)

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_docs, f, indent=2, ensure_ascii=False)

    return str(output_path)


def fetch_and_save_json(query: str = "diabetes management", count: int = 3) -> str:
    """Fetch papers from PMC and save as JSON."""
    print(f"Searching PMC for: {query}")
    papers_info = search_pmc_papers(query, max_results=count * 2)

    if not papers_info:
        raise ValueError(f"No papers found for query: {query}")

    papers = []
    for i, info in enumerate(papers_info[:count], 1):
        try:
            print(f"Fetching paper {i}/{count} (PMC{info['pmcid']})...")
            paper = fetch_pmc_full_text(info["pmcid"])
            papers.append(paper)
            print(f"  Got: {paper['title'][:60]}...")
            time.sleep(0.5)  # Rate limit
        except Exception as e:
            print(f"  Error: {e}")

    if not papers:
        raise ValueError("Failed to fetch any papers")

    output_path = Path("dummy_docs/pmc_documents.json")
    output_file = papers_to_json(papers, output_path)
    print(f"\nSaved {len(papers)} papers to {output_file}")
    return output_file


if __name__ == "__main__":
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "diabetes management"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    fetch_and_save_json(query, count=count)
