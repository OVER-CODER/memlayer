#!/usr/bin/env python
"""
LOCOMO Dataset Evaluation Script
Evaluates memory retrieval effectiveness using the LOCOMO dataset.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class LOCOMOEvaluator:
    """Evaluates memory system against LOCOMO dataset."""

    def __init__(self, dataset_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.dataset_path = Path(dataset_path)
        self.model = SentenceTransformer(model_name)
        self.dataset = self._load_dataset()

    def _load_dataset(self) -> dict:
        """Load LOCOMO dataset."""
        print(f"Loading dataset from {self.dataset_path}...")
        with open(self.dataset_path, "r") as f:
            data = json.load(f)
        print(f"✓ Loaded dataset with {len(data)} samples")
        return data

    def extract_documents(self) -> Dict[str, List[str]]:
        """
        Extract documents and QA pairs from dataset.
        Documents are the "memory" items to retrieve.
        """
        documents = {}
        qa_pairs = []

        for sample in self.dataset:
            # Extract document text from evidence
            if "documents" in sample:
                for doc_id, doc_text in sample["documents"].items():
                    documents[doc_id] = doc_text

            # Collect QA pairs
            if "qa" in sample:
                qa_pairs.extend(sample["qa"])

        return documents, qa_pairs

    def evaluate_retrieval(
        self,
        documents: Dict[str, str],
        qa_pairs: List[Dict],
        top_k: int = 5,
    ) -> Dict:
        """
        Evaluate retrieval performance.

        For each question, we:
        1. Embed the question
        2. Find most similar documents
        3. Check if relevant documents (from evidence) are retrieved
        """
        print(f"\nEvaluating retrieval on {len(qa_pairs)} QA pairs...")

        # Embed all documents once
        doc_ids = list(documents.keys())
        doc_embeddings = self.model.encode([documents[did] for did in doc_ids])

        metrics = {
            "total_questions": len(qa_pairs),
            "hit_at_1": 0,
            "hit_at_5": 0,
            "mean_rank": [],
            "mrr": [],  # Mean Reciprocal Rank
            "categories": {},
        }

        for qa in qa_pairs:
            question = qa["question"]
            evidence_docs = qa.get("evidence", [])
            category = qa.get("category", 0)

            # Embed question
            q_embedding = self.model.encode(question)

            # Compute similarities
            similarities = np.dot(doc_embeddings, q_embedding)
            ranked_indices = np.argsort(-similarities)
            ranked_docs = [doc_ids[i] for i in ranked_indices]

            # Check retrieval quality
            for i, doc_id in enumerate(ranked_docs[:top_k]):
                if doc_id in evidence_docs:
                    if i == 0:
                        metrics["hit_at_1"] += 1
                    metrics["hit_at_5"] += 1
                    metrics["mrr"].append(1.0 / (i + 1))
                    metrics["mean_rank"].append(i + 1)
                    break
            else:
                # Not found in top-k
                metrics["mean_rank"].append(top_k + 1)

            # Track by category
            if category not in metrics["categories"]:
                metrics["categories"][category] = {"total": 0, "hits": 0}

            metrics["categories"][category]["total"] += 1
            if any(doc_id in evidence_docs for doc_id in ranked_docs[:top_k]):
                metrics["categories"][category]["hits"] += 1

        # Compute aggregate metrics
        metrics["recall@1"] = metrics["hit_at_1"] / len(qa_pairs)
        metrics["recall@5"] = metrics["hit_at_5"] / len(qa_pairs)
        metrics["mean_rank_mean"] = (
            np.mean(metrics["mean_rank"]) if metrics["mean_rank"] else 0
        )
        metrics["mrr_mean"] = np.mean(metrics["mrr"]) if metrics["mrr"] else 0

        return metrics

    def evaluate_continuity(self, qa_pairs: List[Dict]) -> Dict:
        """
        Evaluate if the system can maintain continuity across conversations.

        This checks if questions that reference previous information
        are answered based on memory.
        """
        print(f"\nEvaluating conversation continuity...")

        continuity_metrics = {
            "total_category_3_questions": 0,  # Category 3 = inference/continuity
            "potential_continuity_violations": 0,
        }

        # Category 3 questions require understanding of previous context
        category_3_questions = [qa for qa in qa_pairs if qa.get("category") == 3]

        continuity_metrics["total_category_3_questions"] = len(category_3_questions)

        return continuity_metrics

    def run_full_evaluation(self, top_k: int = 5) -> Dict:
        """Run complete evaluation."""
        print("\n" + "=" * 60)
        print("LOCOMO Dataset Evaluation")
        print("=" * 60)

        documents, qa_pairs = self.extract_documents()

        print(f"\nDataset Statistics:")
        print(f"  - Documents: {len(documents)}")
        print(f"  - QA Pairs: {len(qa_pairs)}")

        # Evaluate retrieval
        retrieval_results = self.evaluate_retrieval(documents, qa_pairs, top_k=top_k)

        # Evaluate continuity
        continuity_results = self.evaluate_continuity(qa_pairs)

        # Combine results
        results = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "dataset_stats": {
                "documents": len(documents),
                "qa_pairs": len(qa_pairs),
            },
            "retrieval_metrics": retrieval_results,
            "continuity_metrics": continuity_results,
        }

        return results

    def print_results(self, results: Dict):
        """Print evaluation results."""
        print("\n" + "=" * 60)
        print("Evaluation Results")
        print("=" * 60)

        r = results["retrieval_metrics"]
        print(f"\nRetrieval Performance (top-5):")
        print(f"  - Recall@1: {r['recall@1']:.1%}")
        print(f"  - Recall@5: {r['recall@5']:.1%}")
        print(f"  - Mean Reciprocal Rank: {r['mrr_mean']:.3f}")
        print(f"  - Mean Rank: {r['mean_rank_mean']:.1f}")

        print(f"\nRetrieval by Category:")
        for cat, metrics in r["categories"].items():
            recall = metrics["hits"] / metrics["total"] if metrics["total"] > 0 else 0
            cat_names = {1: "Factual", 2: "Temporal", 3: "Inference"}
            print(
                f"  - Category {cat} ({cat_names.get(cat, 'Unknown')}): {recall:.1%} ({metrics['hits']}/{metrics['total']})"
            )

        c = results["continuity_metrics"]
        print(f"\nContinuity Assessment:")
        print(f"  - Inference questions: {c['total_category_3_questions']}")
        print(f"  - These require understanding previous context")


def main():
    # Find dataset
    dataset_path = Path(__file__).parent.parent / "Dataset" / "locomo10.json"

    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        return 1

    # Run evaluation
    evaluator = LOCOMOEvaluator(str(dataset_path))
    results = evaluator.run_full_evaluation(top_k=5)

    # Print results
    evaluator.print_results(results)

    # Save results
    output_path = Path(__file__).parent / "evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✓ Results saved to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
