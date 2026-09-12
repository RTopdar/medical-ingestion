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
from datetime import datetime, timezone
from pathlib import Path

from eval.ragas_adapters import build_ragas_embeddings, build_ragas_llm  # noqa: E402 (must precede ragas import — installs vertexai stub workaround)
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

logger = logging.getLogger(__name__)

DEFAULT_GOLDEN_SET_PATH = Path(__file__).parent / "llm_golden_set.json"
RESULTS_DIR = Path(__file__).parent / "results"

DEFAULT_METRICS = [
    Faithfulness(),
    ResponseRelevancy(),
    LLMContextPrecisionWithReference(),
    LLMContextRecall(),
    AnswerCorrectness(),
]
OPTIONAL_METRICS = [NoiseSensitivity(), ContextEntityRecall()]


class RagasEvalRunner:
    """Owns the golden-set-to-scored-result lifecycle: load golden set, run the
    live pipeline per query, build a RAGAS EvaluationDataset, score it, and
    write/print results. Mirrors the repo's existing service-class pattern
    (SearchService, HybridRetriever, Embedder)."""

    def __init__(self, search_service: SearchService | None = None, judge_model: str | None = None):
        self.search_service = search_service or SearchService()
        self.llm = build_ragas_llm(judge_model)
        self.embeddings = build_ragas_embeddings()

    def load_golden_set(
        self, path: Path = DEFAULT_GOLDEN_SET_PATH, limit: int | None = None
    ) -> list[dict]:
        with open(path, encoding="utf-8") as f:
            golden_set = json.load(f)
        return golden_set[:limit] if limit else golden_set

    def collect_live_records(self, golden_set: list[dict]) -> list[dict]:
        """Run the live pipeline once per golden set item. Sequential — SearchService
        holds mutable state (self.last_results) and isn't documented thread-safe."""
        records = []
        for i, item in enumerate(golden_set, start=1):
            logger.info("collecting live record %d/%d: %s", i, len(golden_set), item["query"])
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

            records.append(
                {
                    "user_input": item["query"],
                    "retrieved_contexts": retrieved_contexts,
                    "response": answer_text,
                    "reference": item["ground_truth"],
                }
            )
        return records

    def build_dataset(self, records: list[dict]) -> EvaluationDataset:
        return EvaluationDataset.from_list(records)

    def run(
        self,
        golden_set_path: Path = DEFAULT_GOLDEN_SET_PATH,
        limit: int | None = None,
        include_optional: bool = False,
    ):
        golden_set = self.load_golden_set(golden_set_path, limit)
        records = self.collect_live_records(golden_set)
        dataset = self.build_dataset(records)

        metrics = list(DEFAULT_METRICS) + (list(OPTIONAL_METRICS) if include_optional else [])
        run_config = RunConfig(timeout=300, max_workers=4, max_retries=10, max_wait=60)
        result = evaluate(
            dataset=dataset, metrics=metrics, llm=self.llm, embeddings=self.embeddings, run_config=run_config
        )

        self.write_results(result, golden_set)
        self.print_summary(result, golden_set)
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

    def print_summary(self, result, golden_set: list[dict]) -> None:
        df = result.to_pandas()
        df["difficulty"] = [item["difficulty"] for item in golden_set[: len(df)]]
        metric_cols = [c for c in df.columns if c not in ("user_input", "retrieved_contexts", "response", "reference", "difficulty")]

        print("\n=== Overall mean scores ===")
        print(df[metric_cols].mean().to_string())

        print("\n=== Mean scores by difficulty tier ===")
        print(df.groupby("difficulty")[metric_cols].mean().to_string())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run RAGAS eval against the live pipeline.")
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N golden set items (smoke test).")
    parser.add_argument("--include-optional", action="store_true", help="Also run NoiseSensitivity and ContextEntityRecall.")
    parser.add_argument("--judge-model", type=str, default=None, help="Override the RAGAS judge model (defaults to RAGAS_JUDGE_MODEL or CHAT_MODEL).")
    args = parser.parse_args()

    runner = RagasEvalRunner(judge_model=args.judge_model)
    runner.run(limit=args.limit, include_optional=args.include_optional)


if __name__ == "__main__":
    main()
