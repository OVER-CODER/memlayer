"""
Production Validation Runner - Phase D1.5
Orchestrates all production validation tests against the deployed Render backend.
"""

import os
import sys
import asyncio
import time
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Import from helpers
from helpers import TestResult

# Import test modules
from test_concurrent_ingestion import test_concurrent_ingestion
from test_longitudinal_growth import test_longitudinal_growth
from test_replay_integrity import test_replay_integrity
from test_governance_integrity import test_governance_integrity
from test_snapshot_recovery import test_snapshot_recovery
from test_redis_coordination import test_redis_coordination
from test_connection_resilience import test_connection_resilience
from test_partial_failure_recovery import test_partial_failure_recovery
from test_telemetry_pipeline import test_telemetry_pipeline
from test_cold_restart_recovery import test_cold_restart_recovery
from test_async_ordering import test_async_ordering
from test_pgvector_scaling import test_pgvector_scaling
from test_high_volume_replay import test_high_volume_replay
from test_tenant_isolation import test_tenant_isolation

# Configuration
PRODUCTION_URL = os.getenv("PRODUCTION_URL", "https://memlayer-prod.onrender.com")
REPORT_DIR = Path(__file__).parent.parent.parent / "docs" / "production_validation"

# JWT Token for authenticated API requests (generated with production secret key)
# Production uses the default dev secret key from config
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJ0ZW5hbnRfaWQiOiJ0ZXN0LXRlbmFudCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc3ODcwMDQ4NCwiaWF0IjoxNzc4NjE0MDg0fQ.7zoUZ8STuwHJ4maF_ZNAXFAW1euDT0SGc74_TVdCSOI"

# Ensure report directory exists
REPORT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TestResult:
    test_name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class TestSuite:
    name: str
    results: List[TestResult] = field(default_factory=list)

    def add_result(self, result: TestResult):
        self.results.append(result)

    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")

        return {
            "suite": self.name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": passed / total if total > 0 else 0,
        }


class ProductionValidator:
    """Main production validation orchestrator."""

    def __init__(self, base_url: str = PRODUCTION_URL):
        self.base_url = base_url
        self.suites: Dict[str, TestSuite] = {}
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all production validation tests."""
        self.start_time = datetime.now(timezone.utc)

        # Import all test modules
        test_modules = [
            ("concurrent_ingestion", test_concurrent_ingestion),
            ("longitudinal_growth", test_longitudinal_growth),
            ("replay_integrity", test_replay_integrity),
            ("governance_integrity", test_governance_integrity),
            ("snapshot_recovery", test_snapshot_recovery),
            ("redis_coordination", test_redis_coordination),
            ("connection_resilience", test_connection_resilience),
            ("partial_failure_recovery", test_partial_failure_recovery),
            ("telemetry_pipeline", test_telemetry_pipeline),
            ("cold_restart_recovery", test_cold_restart_recovery),
            ("async_ordering", test_async_ordering),
            ("pgvector_scaling", test_pgvector_scaling),
            ("high_volume_replay", test_high_volume_replay),
            ("tenant_isolation", test_tenant_isolation),
        ]

        print(f"\n{'=' * 60}")
        print(f"PRODUCTION VALIDATION - Phase D1.5")
        print(f"{'=' * 60}")
        print(f"Target: {self.base_url}")
        print(f"Started: {self.start_time.isoformat()}")
        print(f"{'=' * 60}\n")

        for module_name, test_func in test_modules:
            suite = TestSuite(name=module_name)
            self.suites[module_name] = suite

            try:
                print(f"Running: {module_name}...")
                result = await test_func(self.base_url)
                suite.add_result(result)

                status_icon = (
                    "✓"
                    if result.status == "PASS"
                    else "✗"
                    if result.status == "FAIL"
                    else "?"
                )
                print(f"  {status_icon} {result.status} ({result.duration:.2f}s)")

            except Exception as e:
                print(f"Error in {module_name}: {e}")
                import traceback

                traceback.print_exc()
                error_result = TestResult(
                    test_name=module_name, status="ERROR", duration=0, errors=[str(e)]
                )
                suite.add_result(error_result)

        self.end_time = datetime.now(timezone.utc)
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_tests = sum(len(s.results) for s in self.suites.values())
        total_passed = sum(
            1 for s in self.suites.values() for r in s.results if r.status == "PASS"
        )
        total_failed = sum(
            1 for s in self.suites.values() for r in s.results if r.status == "FAIL"
        )
        total_errors = sum(
            1 for s in self.suites.values() for r in s.results if r.status == "ERROR"
        )

        report = {
            "phase": "D1.5",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_url": self.base_url,
            "duration_seconds": (self.end_time - self.start_time).total_seconds()
            if self.end_time
            else 0,
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "errors": total_errors,
                "pass_rate": total_passed / total_tests if total_tests > 0 else 0,
            },
            "suites": {name: suite.summary() for name, suite in self.suites.items()},
            "results": [
                {
                    "suite": name,
                    "test": r.test_name,
                    "status": r.status,
                    "duration": r.duration,
                    "metrics": r.metrics,
                    "errors": r.errors,
                }
                for name, suite in self.suites.items()
                for r in suite.results
            ],
        }

        # Write JSON report
        report_path = REPORT_DIR / "phase_d15_results.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary
        print(f"\n{'=' * 60}")
        print(f"VALIDATION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print(f"Errors: {total_errors}")
        print(f"Pass Rate: {report['summary']['pass_rate'] * 100:.1f}%")
        print(f"Report: {report_path}")
        print(f"{'=' * 60}\n")

        return report


async def main():
    """Main entry point."""
    validator = ProductionValidator()
    report = await validator.run_all_tests()

    # Exit with error code if any tests failed
    if report["summary"]["failed"] > 0 or report["summary"]["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
