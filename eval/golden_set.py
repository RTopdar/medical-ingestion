"""Golden set generation script for retrieval eval.

Builds eval/golden_set.json from dummy_docs/pmc_documents.json: hand-picked
query -> relevant doc_id(s) pairs spanning easy (title/keyword overlap),
hard (paraphrased, no lexical overlap), multilingual, and no-match cases.
"""

import json
from pathlib import Path

DOCS_PATH = Path(__file__).parent.parent / "dummy_docs" / "pmc_documents.json"
OUTPUT_PATH = Path(__file__).parent / "golden_set.json"

GOLDEN_SET = [
    # --- easy: near-verbatim keyword/title overlap ---
    {
        "query": "developmental language disorder inflammation markers in preschoolers",
        "relevant_doc_ids": ["PMC-13461268"],
        "difficulty": "easy",
    },
    {
        "query": "adenovirus vector gene therapy for neonatal phenylketonuria",
        "relevant_doc_ids": ["PMC-13461269"],
        "difficulty": "easy",
    },
    {
        "query": "large language models in chronic disease care systematic review",
        "relevant_doc_ids": ["PMC-13460802"],
        "difficulty": "easy",
    },
    {
        "query": "house dust mite sublingual immunotherapy allergic rhinitis",
        "relevant_doc_ids": ["PMC-13460716"],
        "difficulty": "easy",
    },
    {
        "query": "bibliometric analysis of global stroke mortality research",
        "relevant_doc_ids": ["PMC-13461127"],
        "difficulty": "easy",
    },
    {
        "query": "CAR-T cell immunotherapy controlled by plant hormone switch",
        "relevant_doc_ids": ["PMC-13460283"],
        "difficulty": "easy",
    },
    {
        "query": "AAV RPGR gene therapy X-linked retinitis pigmentosa",
        "relevant_doc_ids": ["PMC-13459258"],
        "difficulty": "easy",
    },
    {
        "query": "diaphragmatic ultrasound predicting ventilator weaning outcomes",
        "relevant_doc_ids": ["PMC-13459330"],
        "difficulty": "easy",
    },
    # --- medium: partial lexical overlap, some rephrasing ---
    {
        "query": "does screen time in VR help kids with ADHD participate more at school",
        "relevant_doc_ids": ["PMC-13461272"],
        "difficulty": "medium",
    },
    {
        "query": "left atrial size predicting complications after kidney transplant",
        "relevant_doc_ids": ["PMC-13460372"],
        "difficulty": "medium",
    },
    {
        "query": "gut bacteria's role in breast cancer development",
        "relevant_doc_ids": ["PMC-13458463"],
        "difficulty": "medium",
    },
    {
        "query": "muscle loss risk from newer weight loss drugs",
        "relevant_doc_ids": ["PMC-13457776"],
        "difficulty": "medium",
    },
    {
        "query": "genetic reference panel for Taiwanese population imputation",
        "relevant_doc_ids": ["PMC-13459345"],
        "difficulty": "medium",
    },
    {
        "query": "barriers Canadian patients face getting treated for hepatitis B",
        "relevant_doc_ids": ["PMC-13458430"],
        "difficulty": "medium",
    },
    # --- hard: conceptual/paraphrased, little to no lexical overlap ---
    {
        "query": "why blood test ratios might flag language delays before speech evaluation",
        "relevant_doc_ids": ["PMC-13461268"],
        "difficulty": "hard",
    },
    {
        "query": "using a plant molecule as an on/off switch for engineered immune cells",
        "relevant_doc_ids": ["PMC-13460283"],
        "difficulty": "hard",
    },
    {
        "query": "nanoparticles disguised as blood cells for cancer heat therapy",
        "relevant_doc_ids": ["PMC-13460286"],
        "difficulty": "hard",
    },
    {
        "query": "lab-grown lung tissue models for studying flu infection",
        "relevant_doc_ids": ["PMC-13460282"],
        "difficulty": "hard",
    },
    {
        "query": "mumps causing infertility in males via immune signaling",
        "relevant_doc_ids": ["PMC-13458414"],
        "difficulty": "hard",
    },
    {
        "query": "brain imaging technique tracking cell loss in Huntington's disease",
        "relevant_doc_ids": ["PMC-13461150"],
        "difficulty": "hard",
    },
    {
        "query": "rare fatal inherited metabolic seizure disorder in newborns",
        "relevant_doc_ids": ["PMC-13459259"],
        "difficulty": "hard",
    },
    {
        "query": "parasitic worm infection causing spinal cord compression symptoms in a child",
        "relevant_doc_ids": ["PMC-13459161"],
        "difficulty": "hard",
    },
    # --- multilingual (Chinese) ---
    {
        "query": "唇腭裂与基因多态性的关联性研究",
        "relevant_doc_ids": ["PMC-13458849"],
        "difficulty": "medium_multilingual",
    },
    {
        "query": "急性牙痛的药物治疗指南",
        "relevant_doc_ids": ["PMC-13458855"],
        "difficulty": "easy_multilingual",
    },
    # --- no-match: plausible medical query with no doc in the set ---
    {
        "query": "mRNA vaccine efficacy against novel coronavirus variants",
        "relevant_doc_ids": [],
        "difficulty": "no_match",
    },
    {
        "query": "surgical technique for laparoscopic appendectomy in adults",
        "relevant_doc_ids": [],
        "difficulty": "no_match",
    },
]


def main() -> None:
    with open(DOCS_PATH, encoding="utf-8") as f:
        docs = json.load(f)
    doc_ids = {d["id"] for d in docs}

    missing = [
        doc_id
        for item in GOLDEN_SET
        for doc_id in item["relevant_doc_ids"]
        if doc_id not in doc_ids
    ]
    if missing:
        raise ValueError(f"golden set references unknown doc_ids: {missing}")

    OUTPUT_PATH.write_text(
        json.dumps(GOLDEN_SET, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"wrote {len(GOLDEN_SET)} queries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
