"""Tests for structured logging module."""

import logging
from pathlib import Path

from harness.logging import setup_logging, get_logger, HAS_STRUCTLOG


def test_get_logger_returns_logger():
    """get_logger should return a logger-like object."""
    log = get_logger(experiment="test", covenant="mock")
    assert log is not None


def test_setup_logging_no_dir():
    """setup_logging without log_dir should not raise."""
    setup_logging(level="WARNING")


def test_setup_logging_with_dir(tmp_path):
    """setup_logging with log_dir should create the directory."""
    log_dir = tmp_path / "logs"
    setup_logging(log_dir=log_dir, level="DEBUG")
    assert log_dir.exists()


def test_logger_can_log():
    """Logger should accept standard log calls without error."""
    log = get_logger(experiment="test", covenant="mock")
    # Both structlog and stdlib LoggerAdapter support .info()
    log.info("test message")


def test_has_structlog_flag():
    """HAS_STRUCTLOG should be a boolean."""
    assert isinstance(HAS_STRUCTLOG, bool)
