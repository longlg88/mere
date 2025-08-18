"""
pytest configuration file for MERE AI Agent tests
"""
import pytest
import asyncio
import os
import tempfile
from pathlib import Path

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Create a minimal WAV file header (silence)
        f.write(b'RIFF')
        f.write((36).to_bytes(4, 'little'))  # File size - 8
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))  # Subchunk1 size
        f.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
        f.write((1).to_bytes(2, 'little'))   # Number of channels
        f.write((16000).to_bytes(4, 'little'))  # Sample rate
        f.write((32000).to_bytes(4, 'little'))  # Byte rate
        f.write((2).to_bytes(2, 'little'))   # Block align
        f.write((16).to_bytes(2, 'little'))  # Bits per sample
        f.write(b'data')
        f.write((0).to_bytes(4, 'little'))   # Data size
        
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)

@pytest.fixture
def sample_texts():
    """Sample Korean texts for testing"""
    return [
        "내일 우유 사는 거 기억해줘",
        "오늘 오후 3시에 회의 있어",
        "할일 목록 보여줘",
        "방금 말한 할일 취소해",
        "이번 주 일정 확인해줘"
    ]

@pytest.fixture
def test_user_id():
    """Test user ID for session management"""
    return "test-user-12345"