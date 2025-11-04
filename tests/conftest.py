"""
PyTest configuration and fixtures
"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ASTERISK_PASSWORD"] = "test-pass"
os.environ["VONAGE_API_KEY"] = "test-vonage-key"
os.environ["VONAGE_API_SECRET"] = "test-vonage-secret"
os.environ["VONAGE_NUMBER"] = "+1234567890"
os.environ["PUBLIC_IP"] = "1.2.3.4"


@pytest.fixture
def mock_config():
    """Fixture to provide mock configuration"""
    from unittest.mock import MagicMock

    config = MagicMock()
    config.openai.api_key = "test-key"
    config.openai.model = "test-model"
    config.openai.voice = "alloy"
    config.asterisk.host = "localhost"
    config.asterisk.port = 8088
    config.audio.sample_rate = 24000
    config.audio.chunk_size = 960
    return config
