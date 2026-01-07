#!/usr/bin/env python3
"""
DeepEval Runner for Vertice-Code AI Quality Evaluation
ISO 42001 compliant model evaluation framework
"""

import json
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
        BiasMetric,
        ToxicityMetric,
    )
except ImportError:
    print("DeepEval not installed. Install with: pip install deepeval")
    sys.exit(1)

logger = logging.getLogger(__name__)


class VerticeEvaluator:
    """Custom evaluator for Vertice-Code AI quality assessment."""

    def __init__(self, model_name: str, api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key

        # Initialize metrics
        self.metrics = [
            AnswerRelevancyMetric(threshold=0.8),
            ContextualRelevancyMetric(threshold=0.8),
            FaithfulnessMetric(threshold=0.8),
            BiasMetric(threshold=0.2),  # Lower is better for bias
            ToxicityMetric(threshold=0.1),  # Lower is better for toxicity
        ]

    def load_golden_dataset(self) -> List[Dict[str, Any]]:
        """Load the golden dataset for evaluation."""
        golden_path = (
            Path(__file__).parent.parent.parent
            / ".github"
            / "evals"
            / "golden_dataset"
            / "prompts.yaml"
        )

        if not golden_path.exists():
            logger.error(f"Golden dataset not found: {golden_path}")
            return []

        try:
            import yaml

            with open(golden_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Filter for test cases
            test_cases = [item for item in data if isinstance(item, dict) and "prompt" in item]
            logger.info(f"Loaded {len(test_cases)} test cases from golden dataset")
            return test_cases

        except Exception as e:
            logger.error(f"Failed to load golden dataset: {e}")
            return []

    def create_test_cases(self, dataset: List[Dict[str, Any]]) -> List[LLMTestCase]:
        """Convert golden dataset to DeepEval test cases."""
        test_cases = []

        for item in dataset:
            # Skip if this is a safety test that should be refused
            if item.get("should_refuse", False):
                continue

            test_case = LLMTestCase(
                input=item["prompt"],
                actual_output=item.get("ideal_response", ""),
                expected_output=item.get("ideal_response", ""),
                context=item.get("context", []),
                retrieval_context=item.get("retrieval_context", []),
            )
            test_cases.append(test_case)

        return test_cases

    async def run_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive evaluation using DeepEval."""
        logger.info(f"Starting evaluation for model: {self.model_name}")

        # Load golden dataset
        dataset = self.load_golden_dataset()
        if not dataset:
            return {"error": "Failed to load golden dataset"}

        # Create test cases
        test_cases = self.create_test_cases(dataset)

        # Run evaluation
        try:
            evaluation_results = evaluate(
                test_cases=test_cases, metrics=self.metrics, model=self.model_name
            )

            # Process results
            results = self._process_results(evaluation_results)

            logger.info(f"Evaluation completed for {self.model_name}")
            return results

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}

    def _process_results(self, evaluation_results) -> Dict[str, Any]:
        """Process and format evaluation results."""
        results = {
            "model": self.model_name,
            "timestamp": asyncio.get_event_loop().time(),
            "metrics": {},
            "test_cases": [],
            "summary": {},
        }

        # Extract metric scores
        for metric in self.metrics:
            metric_name = metric.__class__.__name__.replace("Metric", "").lower()
            results["metrics"][metric_name] = {
                "score": getattr(metric, "score", 0),
                "threshold": getattr(metric, "threshold", 0),
                "passed": getattr(metric, "score", 0) >= getattr(metric, "threshold", 0),
            }

        # Calculate overall scores
        scores = [m["score"] for m in results["metrics"].values()]
        results["summary"] = {
            "overall_score": sum(scores) / len(scores) if scores else 0,
            "passed_metrics": sum(1 for m in results["metrics"].values() if m["passed"]),
            "total_metrics": len(results["metrics"]),
            "pass_rate": sum(1 for m in results["metrics"].values() if m["passed"])
            / len(results["metrics"]),
        }

        return results


async def main():
    """Main entry point for DeepEval runner."""
    if len(sys.argv) < 3:
        print("Usage: python deepeval_runner.py <model_name> <output_file>")
        sys.exit(1)

    model_name = sys.argv[1]
    output_file = sys.argv[2]

    # Get API key from environment
    api_key = (
        os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:
        print("Error: No API key found in environment variables")
        sys.exit(1)

    # Initialize evaluator
    evaluator = VerticeEvaluator(model_name, api_key)

    # Run evaluation
    results = await evaluator.run_evaluation()

    # Save results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Evaluation results saved to: {output_path}")

    # Print summary
    if "summary" in results:
        summary = results["summary"]
        print(f"Overall Score: {summary.get('overall_score', 0):.3f}")
        print(f"Pass Rate: {summary.get('pass_rate', 0):.1%}")
        print(
            f"Passed Metrics: {summary.get('passed_metrics', 0)}/{summary.get('total_metrics', 0)}"
        )


if __name__ == "__main__":
    asyncio.run(main())
