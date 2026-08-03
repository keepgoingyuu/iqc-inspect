from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_openapi_has_named_operations():
    """hey-api 依賴 route 名稱產生 client 方法名。"""
    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()
        operation_ids = {
            op["operationId"]
            for path in spec["paths"].values()
            for op in path.values()
        }
        assert "login" in operation_ids
        assert "judge_sheet" in operation_ids
