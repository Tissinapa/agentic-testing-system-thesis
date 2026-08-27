import pytest
import httpx


BASE_URL = "http://localhost:8000"
VALID_TOKEN = "Bearer Taman-ei-p1t1a1s-0lla-na1n-123"

AUTH_HEADERS = {
    "Authorization": VALID_TOKEN,
    "Content-Type": "application/json"
}

# ----------------Authentication tests-------------------

def test_login_valid_creditentials():
    response = httpx.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert response.json()["access_token"] != ""

def test_login_invalid_creditentials_returns_401():
    response = httpx.post(f"{BASE_URL}/auth/login", json={
        "username": "wrong",
        "password": "wrong123"
    })
    assert response.status_code == 401
    
def test_login_empty_creditentials_returns_401():
    response = httpx.post(f"{BASE_URL}/auth/login", json={
        "username": "",
        "password": ""
    })
    assert response.status_code == 401
    
#---------------------- Test tasks----------------------------

def test_get_tasks_without_auth_returns_401():
    response = httpx.get(f"{BASE_URL}/tasks")
    assert response.status_code == 401

def test_get_tasks_with_auth_returns_200():
    response = httpx.get(f"{BASE_URL}/tasks", headers=AUTH_HEADERS)
    assert response.status_code == 200

def test_create_task_returns_201():
    response = httpx.post(f"{BASE_URL}/tasks",
                         json= {"title": "TESTing", "priority":1 }, 
                         headers=AUTH_HEADERS)
    assert response.status_code == 201
        
def test_create_task_null_title_returns_400():
    response = httpx.post(f"{BASE_URL}/tasks",
                         json= {"title": "", "priority":1 }, 
                         headers=AUTH_HEADERS)
    assert response.status_code == 400

def test_get_nonexistent_task_returns_404():
    response = httpx.get(f"{BASE_URL}/tasks/99999", headers=AUTH_HEADERS)
    assert response.status_code == 404
    
def test_delete_taks_returns_204():
    create = httpx.post(
        f"{BASE_URL}/tasks",
        json= {"title": "TESTing delete", "priority":1 },
        headers=AUTH_HEADERS
    )
    task_id = create.json()["id"]
    response = httpx.delete(
        f"{BASE_URL}/tasks/{task_id}",
        headers=AUTH_HEADERS
    )
    assert response.status_code == 204