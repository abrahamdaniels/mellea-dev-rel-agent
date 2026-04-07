"""Demo test runner — NOT an LLM agent.

Runs pytest on a generated demo directory and returns structured results.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from core.config import get_config
from core.models import TestResult
from core.pipeline import StageResult

logger = logging.getLogger(__name__)


def _parse_pytest_output(output: str) -> tuple[int, int, list[str]]:
    """Parse pytest short output for pass/fail counts and failing test names.

    Returns (total, failed, failing_names).
    """
    # Match summary line like "3 passed, 1 failed" or "4 passed"
    passed = 0
    failed = 0

    passed_match = re.search(r"(\d+) passed", output)
    if passed_match:
        passed = int(passed_match.group(1))

    failed_match = re.search(r"(\d+) failed", output)
    if failed_match:
        failed = int(failed_match.group(1))

    # Extract failing test names from FAILED lines
    failing_names = re.findall(r"FAILED\s+(\S+)", output)

    total = passed + failed
    return total, failed, failing_names


def run(
    path: str,
    timeout: int | None = None,
    **kwargs,
) -> StageResult:
    """Run tests on a generated demo.

    Args:
        path: Directory containing the demo files.
        timeout: Test timeout in seconds. Defaults to config value.

    Returns:
        StageResult with test outcome. On failure, error_context contains
        the combined stdout/stderr for use in pipeline retries.
    """
    config = get_config()
    timeout = timeout or config.demo_test_timeout
    demo_path = Path(path)

    if not demo_path.exists():
        return StageResult(
            stage_name="test",
            success=False,
            error_context=f"Demo path does not exist: {path}",
        )

    # Install requirements if present
    req_file = demo_path / "requirements.txt"
    if req_file.exists():
        try:
            subprocess.run(
                ["pip", "install", "-r", str(req_file), "-q"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Dependency installation timed out")

    # Check for test files
    test_files = list(demo_path.glob("test_*.py")) + list(demo_path.glob("*_test.py"))

    if not test_files:
        # Smoke test: try importing the main module
        main_py = demo_path / "main.py"
        if not main_py.exists():
            return StageResult(
                stage_name="test",
                success=False,
                output={"path": path},
                error_context="No test files and no main.py found in demo directory.",
            )
        try:
            smoke_code = (
                "import importlib.util; "
                f"spec = importlib.util.spec_from_file_location('main', '{main_py}'); "
                "mod = importlib.util.module_from_spec(spec); "
                "spec.loader.exec_module(mod)"
            )
            result = subprocess.run(
                ["python", "-c", smoke_code],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            passed = result.returncode == 0
            test_result = TestResult(
                passed=passed,
                total_tests=1,
                failed_tests=0 if passed else 1,
                error_output=result.stderr if not passed else None,
                failing_test_names=["smoke_test_import"] if not passed else [],
            )
            return StageResult(
                stage_name="test",
                success=passed,
                output={"path": path, "test_result": test_result},
                error_context=result.stderr + result.stdout if not passed else None,
            )
        except subprocess.TimeoutExpired:
            return StageResult(
                stage_name="test",
                success=False,
                output={"path": path},
                error_context=f"Smoke test timed out after {timeout} seconds.",
            )

    # Run pytest
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", str(demo_path), "--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return StageResult(
            stage_name="test",
            success=False,
            output={"path": path},
            error_context=f"Test execution timed out after {timeout} seconds.",
        )

    combined_output = result.stdout + result.stderr
    total, failed, failing_names = _parse_pytest_output(combined_output)
    passed = result.returncode == 0

    test_result = TestResult(
        passed=passed,
        total_tests=total,
        failed_tests=failed,
        error_output=combined_output if not passed else None,
        failing_test_names=failing_names,
    )

    return StageResult(
        stage_name="test",
        success=passed,
        output={"path": path, "test_result": test_result},
        error_context=combined_output if not passed else None,
    )
