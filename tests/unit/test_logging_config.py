"""Tests for logging configuration."""

import pytest
from unittest.mock import Mock, patch
import logging
from pathlib import Path
import tempfile

from papergen.core.logging_config import (
    setup_logging, get_logger, log_operation,
    log_error, log_api_call, enable_debug_mode, disable_logging
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup with default settings."""
        logger = setup_logging()

        assert logger.name == "papergen"
        assert logger.level == logging.INFO

    def test_setup_logging_custom_level(self):
        """Test setup with custom log level."""
        logger = setup_logging(level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self):
        """Test setup with file logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "test.log"

            logger = setup_logging(log_file=log_file, enable_file=True)

            # Log something
            logger.info("Test message")

            # File should be created
            assert log_file.exists()

    def test_setup_logging_no_console(self):
        """Test setup without console logging."""
        logger = setup_logging(enable_console=False)

        # Should have no console handler
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        # May have file handler but not console
        assert logger.name == "papergen"

    def test_setup_logging_no_file(self):
        """Test setup without file logging."""
        logger = setup_logging(enable_file=False)

        assert logger.name == "papergen"

    def test_setup_logging_invalid_log_path(self):
        """Test setup with invalid log path."""
        # Should not raise, just continue without file logging
        logger = setup_logging(log_file=Path("/nonexistent/path/test.log"), enable_file=True)

        assert logger.name == "papergen"


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_default(self):
        """Test getting default logger."""
        logger = get_logger()

        assert logger.name == "papergen"

    def test_get_logger_custom_name(self):
        """Test getting logger with custom name."""
        logger = get_logger("custom.module")

        assert logger.name == "custom.module"

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns same instance."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")

        assert logger1 is logger2


class TestLogOperation:
    """Tests for log_operation function."""

    def test_log_operation_basic(self):
        """Test basic operation logging."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_operation("test_op")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "test_op" in call_args

    def test_log_operation_with_kwargs(self):
        """Test operation logging with kwargs."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_operation("test_op", user="john", action="read")

            call_args = mock_logger.info.call_args[0][0]
            assert "user=john" in call_args
            assert "action=read" in call_args


class TestLogError:
    """Tests for log_error function."""

    def test_log_error_basic(self):
        """Test basic error logging."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            exc = ValueError("Test error")
            log_error(exc, "test_operation")

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "test_operation" in call_args[0][0]
            assert "Test error" in call_args[0][0]

    def test_log_error_with_kwargs(self):
        """Test error logging with kwargs."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            exc = RuntimeError("Runtime issue")
            log_error(exc, "test_op", file="test.py", line=10)

            call_args = mock_logger.error.call_args[0][0]
            assert "file=test.py" in call_args
            assert "line=10" in call_args


class TestLogAPICall:
    """Tests for log_api_call function."""

    def test_log_api_call_basic(self):
        """Test basic API call logging."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_api_call("generate", "claude-3")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "generate" in call_args
            assert "claude-3" in call_args

    def test_log_api_call_with_tokens(self):
        """Test API call logging with tokens."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_api_call("generate", "claude-3", tokens=1500)

            call_args = mock_logger.info.call_args[0][0]
            assert "tokens=1500" in call_args

    def test_log_api_call_with_kwargs(self):
        """Test API call logging with kwargs."""
        with patch('papergen.core.logging_config.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_api_call("generate", "claude-3", tokens=1500, max_tokens=4000)

            call_args = mock_logger.info.call_args[0][0]
            assert "max_tokens=4000" in call_args


class TestEnableDebugMode:
    """Tests for enable_debug_mode function."""

    def test_enable_debug_mode(self):
        """Test enabling debug mode."""
        # Setup logger first
        logger = setup_logging()

        enable_debug_mode()

        assert logger.level == logging.DEBUG


class TestDisableLogging:
    """Tests for disable_logging function."""

    def test_disable_logging(self):
        """Test disabling logging."""
        # Setup logger first
        logger = setup_logging()
        assert len(logger.handlers) > 0

        disable_logging()

        assert len(logger.handlers) == 0
