from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch


def test_passing_tests_return_success(tmp_path):
    # Create a demo directory with a test file
    (tmp_path / "main.py").write_text("x = 1\n")
    (tmp_path / "test_demo.py").write_text("def test_x(): assert True\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "1 passed"
    mock_result.stderr = ""

    with patch("agents.demo.test_runner.subprocess") as mock_sub, \
         patch("agents.demo.test_runner.get_config") as mock_cfg:
        mock_sub.run.return_value = mock_result
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_cfg.return_value = MagicMock(demo_test_timeout=120)

        from agents.demo.test_runner import run
        result = run(path=str(tmp_path))

    assert result.success is True
    test_result = result.output.get("test_result")
    assert test_result is not None
    assert test_result.passed is True


def test_failing_tests_return_failure(tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")
    (tmp_path / "test_demo.py").write_text("def test_x(): assert False\n")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "1 failed\nFAILED test_demo.py::test_x"
    mock_result.stderr = ""

    with patch("agents.demo.test_runner.subprocess") as mock_sub, \
         patch("agents.demo.test_runner.get_config") as mock_cfg:
        mock_sub.run.return_value = mock_result
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_cfg.return_value = MagicMock(demo_test_timeout=120)

        from agents.demo.test_runner import run
        result = run(path=str(tmp_path))

    assert result.success is False
    assert result.error_context is not None
    test_result = result.output.get("test_result")
    assert test_result.failed_tests == 1


def test_missing_path_returns_failure():
    with patch("agents.demo.test_runner.get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(demo_test_timeout=120)

        from agents.demo.test_runner import run
        result = run(path="/nonexistent/path")

    assert result.success is False
    assert "does not exist" in result.error_context


def test_timeout_returns_failure(tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")
    (tmp_path / "test_demo.py").write_text("def test_x(): assert True\n")

    with patch("agents.demo.test_runner.subprocess") as mock_sub, \
         patch("agents.demo.test_runner.get_config") as mock_cfg:
        mock_sub.run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=10)
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_cfg.return_value = MagicMock(demo_test_timeout=10)

        from agents.demo.test_runner import run
        result = run(path=str(tmp_path))

    assert result.success is False
    assert "timed out" in result.error_context


def test_smoke_test_when_no_test_files(tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("agents.demo.test_runner.subprocess") as mock_sub, \
         patch("agents.demo.test_runner.get_config") as mock_cfg:
        mock_sub.run.return_value = mock_result
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_cfg.return_value = MagicMock(demo_test_timeout=120)

        from agents.demo.test_runner import run
        result = run(path=str(tmp_path))

    assert result.success is True
    test_result = result.output.get("test_result")
    assert test_result.total_tests == 1


def test_pytest_output_parsing():
    from agents.demo.test_runner import _parse_pytest_output

    total, failed, names = _parse_pytest_output(
        "3 passed, 1 failed\nFAILED test_demo.py::test_a\nFAILED test_demo.py::test_b"
    )
    assert total == 4
    assert failed == 1
    assert len(names) == 2
