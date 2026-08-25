import pytest
import httpx


BASE_URL = "http://localhost:8000"
VALID_TOKEN = "Taman-ei-p1t1a1s-0lla-na1n-123"

@pytest.fixture
def client():
    return httpx.Client(base_url = BASE_URL)

@pytest.fixture
def auth_headers():
    return {
        "Authorization": VALID_TOKEN,
        "Content-Type": "application/json"
    }