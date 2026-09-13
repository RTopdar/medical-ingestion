"""RAGAS evaluation runner — scores the live retrieval+generation pipeline
(retrieval/search.py::SearchService) against eval/llm_golden_set.json.

For each golden set query, calls SearchService.search() and SearchService.answer()
live (not the golden set's pre-baked `contexts` field), then scores the resulting
(query, retrieved_contexts, response, reference) tuples with RAGAS metrics using
this repo's existing OpenRouter stack as the judge LLM/embeddings
(see eval/ragas_adapters.py). See doc/feature/ragas_runner.md for architecture
diagrams and metric explanations.
"""

import argparse
import csv
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path

# Must precede all ragas imports — installs vertexai stub workaround
from eval.ragas_adapters import build_ragas_embeddings, build_ragas_llm

from ragas import EvaluationDataset, RunConfig, evaluate
from ragas.metrics import (
    AnswerCorrectness,
    ContextEntityRecall,
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    NoiseSensitivity,
    ResponseRelevancy,
)
from retrieval.search import SearchService
from settings import settings

logger = logging.getLogger(__name__)

DEFAULT_GOLDEN_SET_PATH = Path(__file__).parent / "llm_golden_set.json"
RESULTS_DIR = Path(__file__).parent / "results"

# Column name -> (short label, plain-English meaning). Used to make the terminal
# report readable at a glance instead of dumping raw metric identifiers.
_METRIC_INFO = {
    "faithfulness": ("Faithfulness", "answer stays grounded in the retrieved context"),
    "response_relevancy": ("Response relevance", "answer actually addresses the question"),
    "answer_relevancy": ("Response relevance", "answer actually addresses the question"),
    "llm_context_precision_with_reference": ("Context precision (w/ ref)", "only chunks above the reference are relevant"),
    "context_recall": ("Context recall", "reference facts are covered by the retrieved chunks"),
    "answer_correctness": ("Answer correctness", "answer matches the ground-truth reference"),
    "noise_sensitivity": ("Noise sensitivity", "irrelevant chunks do not degrade the answer"),
    "context_entity_recall": ("Entity recall", "ground-truth entities appear in the retrieved context"),
}

# Look up metric info by a punctuation/underscore/case-insensitive key, so both
# ragas's snake_case column names and CamelCase metric names resolve.
_NORMALIZED_METRIC_INFO = {
    key.replace("_", "").lower(): value for key, value in _METRIC_INFO.items()
}

# Non-metric columns that must be excluded when picking score columns.
_NON_SCORE_COLS = ("user_input", "retrieved_contexts", "response", "reference", "difficulty")


def _bar(value: float, width: int = 22) -> str:
    """A horizontal filled/empty bar for a score assumed to be in [0, 1]."""
    score = max(0.0, min(float(value), 1.0))
    filled = round(score * width)
    return "▰" * filled + "▱" * (width - filled)


def _grade(score: float) -> str:
    if score >= 0.8:
        return "EXCELLENT"
    if score >= 0.6:
        return "GOOD"
    if score >= 0.4:
        return "FAIR"
    return "POOR"


def _pretty_name(name: str) -> str:
    """Title-case a snake_case column name (fallback for unknown metrics)."""
    return " ".join(
        "LLM" if word.lower() == "llm" else word.title() for word in name.replace("_", " ").split()
    )


def _metric_label(column: str) -> str:
    """Best-effort human label for a metric column, falling back to a title-cased name."""
    info = _NORMALIZED_METRIC_INFO.get(column.replace("_", "").lower())
    return info[0] if info else _pretty_name(column)


def _metric_meaning(column: str) -> str | None:
    info = _NORMALIZED_METRIC_INFO.get(column.replace("_", "").lower())
    return info[1] if info else None


class RagasEvalRunner:
    """Owns the golden-set-to-scored-result lifecycle: load golden set, run the
    live pipeline per query, build a RAGAS EvaluationDataset, score it, and
    write/print results. Mirrors the repo's existing service-class pattern
    (SearchService, HybridRetriever, Embedder)."""

    def __init__(self, search_service: SearchService | None = None, judge_model: str | None = None):
        self.search_service = search_service or SearchService()
        self.llm = build_ragas_llm(judge_model)
        self.embeddings = build_ragas_embeddings()
        self.judge_model = judge_model or settings.ragas_judge_model or settings.chat_model

    def load_golden_set(
        self, path: Path = DEFAULT_GOLDEN_SET_PATH, limit: int | None = None
    ) -> list[dict]:
        with open(path, encoding="utf-8") as f:
            golden_set = json.load(f)
        return golden_set[:limit] if limit else golden_set

    def collect_live_records(self, golden_set: list[dict]) -> list[dict]:
        """Run the live pipeline once per golden set item. Sequential — SearchService
        holds mutable state (self.last_results) and isn't documented thread-safe."""
        return [self._collect_live_record(item, i, len(golden_set))
                for i, item in enumerate(golden_set, start=1)]

    def _collect_live_record(self, item: dict, index: int, total: int) -> dict:
        """Run the live pipeline for one golden set query and build its record."""
        logger.info("collecting live record %d/%d: %s", index, total, item["query"])
        results = self.search_service.search(item["query"], top_k=5, fetch_k=20)
        retrieved_contexts = [r["text"] for r in results]
        citations = [r["citation"] for r in results]

        # SearchService.answer() streams str chunks — must join the generator to
        # get a full string; passing the generator itself to ragas fails deep
        # inside its dataset validation rather than at the actual bug site.
        answer_text = "".join(
            self.search_service.answer(item["query"], retrieved_contexts, citations=citations)
        )
        assert isinstance(answer_text, str) and answer_text, (
            f"expected non-empty str answer for query {item['query']!r}, got {answer_text!r}"
        )

        return {
            "user_input": item["query"],
            "retrieved_contexts": retrieved_contexts,
            "response": answer_text,
            "reference": item["ground_truth"],
        }

    def build_dataset(self, records: list[dict]) -> EvaluationDataset:
        return EvaluationDataset.from_list(records)

    def run(
        self,
        golden_set_path: Path = DEFAULT_GOLDEN_SET_PATH,
        limit: int | None = None,
        include_optional: bool = False,
    ):
        golden_set = self.load_golden_set(golden_set_path, limit)
        records = []
        total = len(golden_set)
        interrupted = False
        for i, item in enumerate(golden_set, start=1):
            try:
                records.append(self._collect_live_record(item, i, total))
            except KeyboardInterrupt:
                interrupted = True
                break

        if interrupted:
            if records:
                print(
                    f"\nInterrupted during collection — scoring the {len(records)}/{total} "
                    "answers gathered so far.\n"
                )
            else:
                print("\nInterrupted before any answers were gathered — nothing to score.\n")
                return None

        dataset = self.build_dataset(records)

        metrics = [
            Faithfulness(),
            ResponseRelevancy(),
            LLMContextPrecisionWithReference(),
            LLMContextRecall(),
            AnswerCorrectness(),
        ]
        if include_optional:
            metrics += [NoiseSensitivity(), ContextEntityRecall()]

        run_config = RunConfig(timeout=300, max_workers=4, max_retries=10, max_wait=60)
        try:
            result = evaluate(
                dataset=dataset, metrics=metrics, llm=self.llm, embeddings=self.embeddings, run_config=run_config
            )
        except KeyboardInterrupt:
            print("\nInterrupted during scoring — scoring aborted, nothing was written.\n")
            return None

        json_path = self.write_results(result, golden_set)
        self.print_summary(result, golden_set, results_path=json_path)
        return result

    def write_results(self, result, golden_set: list[dict]) -> Path:
        RESULTS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        df = result.to_pandas()
        df["difficulty"] = [item["difficulty"] for item in golden_set[: len(df)]]

        json_path = RESULTS_DIR / f"ragas_run_{timestamp}.json"
        json_path.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")

        csv_path = RESULTS_DIR / f"ragas_run_{timestamp}.csv"
        df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)

        logger.info("wrote results to %s and %s", json_path, csv_path)
        return json_path

    def print_summary(self, result, golden_set: list[dict], results_path: Path | None = None) -> None:
        df = result.to_pandas()
        df["difficulty"] = [item["difficulty"] for item in golden_set[: len(df)]]
        metric_cols = [c for c in df.columns if c not in _NON_SCORE_COLS]
        means = df[metric_cols].mean().sort_values(ascending=False)
        width = 78

        print()
        print("═" * width)
        print(" RAGAS Evaluation Report")
        print("═" * width)
        print(f" queries evaluated : {len(df):>3}   (difficulty tiers: {', '.join(sorted(df['difficulty'].dropna().unique())) or 'n/a'})")
        print(f" answer model      : {settings.chat_model}")
        print(f" judge model       : {self.judge_model}")
        print(f" results written   : {results_path or 'n/a'}")
        print("─" * width)

        print("\n MEAN SCORES  (0–1, higher is better)\n")
        for column in means.index:
            label = _metric_label(column)
            raw = float(means[column])
            if math.isnan(raw):
                print(f"   {label:<24}  n/a   — not computed for this run")
                continue
            score = raw
            print(f"   {label:<24} {_bar(score)} {score:.2f}  {_grade(score)}")
            meaning = _metric_meaning(column)
            if meaning:
                print(f"   {'':<24} {meaning}")

        if df["difficulty"].nunique() > 1:
            print("\n SCORES BY DIFFICULTY TIER\n")
            tier_table = df.groupby("difficulty")[metric_cols].mean()
            header = "  " + "  ".join(f"{_metric_label(c):>20}" for c in metric_cols)
            print(header)
            print("  " + "─" * len(header))
            for tier, row in tier_table.iterrows():
                cells = "  ".join(
                    "n/a" if math.isnan(float(row[c])) else f"{float(row[c]):>20.2f}"
                    for c in metric_cols
                )
                print(f"  {tier:<20}{cells}")
        print("\n" + "═" * width)
        print(" Legend: ▰ filled = score achieved · ▱ empty = room for improvement")
        print()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run RAGAS eval against the live pipeline.")
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N golden set items (smoke test).")
    parser.add_argument("--include-optional", action="store_true", help="Also run NoiseSensitivity and ContextEntityRecall.")
    parser.add_argument("--judge-model", type=str, default=None, help="Override the RAGAS judge model (defaults to RAGAS_JUDGE_MODEL or CHAT_MODEL).")
    args = parser.parse_args()

    runner = RagasEvalRunner(judge_model=args.judge_model)
    try:
        runner.run(limit=args.limit, include_optional=args.include_optional)
    except KeyboardInterrupt:
        print("\nEvaluation cancelled (Ctrl+C). No further work was started.\n")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
