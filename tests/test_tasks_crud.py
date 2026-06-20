from fastapi.testclient import TestClient


def _create_task(client: TestClient, title: str = "Testar API") -> dict:
    response = client.post("/tasks", json={"title": title, "priority": "high"})
    assert response.status_code == 201
    return response.json()


def test_crud_create_task(client: TestClient) -> None:
    task = _create_task(client)

    assert task["id"] == 1
    assert task["title"] == "Testar API"
    assert task["status"] == "pending"
    assert task["priority"] == "high"


def test_crud_list_tasks(client: TestClient) -> None:
    _create_task(client, "Primeira")
    _create_task(client, "Segunda")

    response = client.get("/tasks")

    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == ["Segunda", "Primeira"]


def test_crud_get_task(client: TestClient) -> None:
    task = _create_task(client)

    response = client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == task["title"]


def test_crud_update_task(client: TestClient) -> None:
    task = _create_task(client)

    response = client.put(
        f"/tasks/{task['id']}",
        json={"status": "done", "title": "API validada"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"
    assert response.json()["title"] == "API validada"


def test_crud_delete_task(client: TestClient) -> None:
    task = _create_task(client)

    response = client.delete(f"/tasks/{task['id']}")

    assert response.status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_crud_missing_task_returns_404(client: TestClient) -> None:
    response = client.get("/tasks/999999")

    assert response.status_code == 404


def test_crud_rejects_blank_title(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "   "})

    assert response.status_code == 422


def test_crud_validates_pagination(client: TestClient) -> None:
    assert client.get("/tasks?skip=-1").status_code == 422
    assert client.get("/tasks?limit=101").status_code == 422
