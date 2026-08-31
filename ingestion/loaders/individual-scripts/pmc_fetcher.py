"""Fetch full-text papers from PMC Open Access and save to dummy_docs."""

import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import time

PMC_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DUMMY_DOCS_DIR = Path("dummy_docs/pubmed")


def search_pmc_papers(query: str, max_results: int = 10) -> list[dict]:
    """
    Search PMC for open-access papers.

    Args:
        query: Search query
        max_results: Max papers to return

    Returns:
        List of dicts with pmcid, title, authors
    """
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

    results = []
    for pmcid in pmcids:
        results.append({"pmcid": pmcid})

    return results


def fetch_pmc_full_text(pmcid: str) -> dict:
    """
    Fetch full text of PMC paper.

    Args:
        pmcid: PMC ID

    Returns:
        Dict with title, abstract, full_text, pmcid
    """
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

    return {
        "pmcid": pmcid,
        "title": title,
        "abstract": abstract,
        "full_text": full_text,
    }


def save_paper(paper: dict, index: int) -> str:
    """
    Save paper to text file in dummy_docs.

    Args:
        paper: Paper dict from fetch_pmc_full_text
        index: Sequential index for filename

    Returns:
        Path to saved file
    """
    DUMMY_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Sanitize title for filename
    safe_title = "".join(c if c.isalnum() or c in " -" else "_" for c in paper["title"])
    safe_title = safe_title[:50].strip()

    filename = f"{index:02d}_{safe_title.replace(' ', '_')}.txt"
    filepath = DUMMY_DOCS_DIR / filename

    content = f"""TITLE
{paper['title']}

PMC ID
{paper['pmcid']}

ABSTRACT
{paper['abstract']}

FULL TEXT
{paper['full_text']}
"""

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def fetch_dummy_papers(query: str = "medical research", count: int = 6) -> list[str]:
    """
    Fetch and save dummy papers from PMC.

    Args:
        query: Search query
        count: Number of papers to fetch

    Returns:
        List of file paths saved
    """
    print(f"Searching PMC for: {query}")
    papers_info = search_pmc_papers(query, max_results=count * 2)

    if not papers_info:
        raise ValueError(f"No papers found for query: {query}")

    saved_files = []
    for i, info in enumerate(papers_info[:count], 1):
        try:
            print(f"Fetching paper {i}/{count} (PMC{info['pmcid']})...")
            paper = fetch_pmc_full_text(info["pmcid"])
            filepath = save_paper(paper, i)
            saved_files.append(filepath)
            print(f"  Saved to {filepath}")
            time.sleep(0.5)  # Rate limit
        except Exception as e:
            print(f"  Error: {e}")

    return saved_files


if __name__ == "__main__":
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "medical research"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    files = fetch_dummy_papers(query, count=count)
    print(f"\nSaved {len(files)} papers:")
    for f in files:
        print(f"  {f}")
