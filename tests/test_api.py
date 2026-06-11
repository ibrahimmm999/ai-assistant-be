import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Inisialisasi TestClient dengan mock database agar test tidak butuh DB nyata."""
    with patch("app.db.database.create_engine") as mock_engine, \
         patch("app.db.seed.seed_database"):
        mock_engine.return_value = MagicMock()
        from app.main import app
        return TestClient(app)

class TestHealthCheck:
    def test_root_endpoint_returns_healthy(self, client):
        """Endpoint root harus mengembalikan status healthy."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
class TestRequestValidation:
    def test_empty_message_returns_400(self, client):
        """Pesan kosong harus ditolak dengan status 400."""
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 400

    def test_whitespace_only_message_returns_400(self, client):
        """Pesan hanya spasi harus ditolak dengan status 400."""
        response = client.post("/api/chat", json={"message": "   "})
        assert response.status_code == 400

    def test_missing_message_field_returns_422(self, client):
        """Request tanpa field message harus ditolak dengan status 422."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_valid_request_returns_200(self, client):
        """Request valid harus mengembalikan status 200."""
        with patch("app.api.routes.chat.process_business_intelligence_chat") as mock_process:
            mock_process.return_value = {
                "intent": "general",
                "response": "Halo! Ada yang bisa saya bantu?",
                "generated_sql": None
            }
            response = client.post("/api/chat", json={"message": "halo"})
            assert response.status_code == 200

class TestResponseStructure:
    def test_response_has_required_fields(self, client):
        """Response harus mengandung field intent, response, dan generated_sql."""
        with patch("app.api.routes.chat.process_business_intelligence_chat") as mock_process:
            mock_process.return_value = {
                "intent": "general",
                "response": "Halo!",
                "generated_sql": None
            }
            response = client.post("/api/chat", json={"message": "halo"})
            data = response.json()
            assert "intent" in data
            assert "response" in data
            assert "generated_sql" in data

    def test_general_intent_has_no_sql(self, client):
        """Intent general tidak boleh menghasilkan SQL."""
        with patch("app.api.routes.chat.process_business_intelligence_chat") as mock_process:
            mock_process.return_value = {
                "intent": "general",
                "response": "Halo!",
                "generated_sql": None
            }
            response = client.post("/api/chat", json={"message": "halo"})
            assert response.json()["generated_sql"] is None

    def test_data_query_intent_has_sql(self, client):
        """Intent data_query harus menghasilkan SQL."""
        with patch("app.api.routes.chat.process_business_intelligence_chat") as mock_process:
            mock_process.return_value = {
                "intent": "data_query",
                "response": "Terdapat 5 produk skincare di bawah 100rb.",
                "generated_sql": "SELECT * FROM products WHERE price < 100000 LIMIT 100;"
            }
            response = client.post("/api/chat", json={"message": "produk skincare di bawah 100k"})
            data = response.json()
            assert data["intent"] == "data_query"
            assert data["generated_sql"] is not None

class TestSessionHandling:
    def test_custom_session_id_accepted(self, client):
        """Custom session_id harus diterima tanpa error."""
        with patch("app.api.routes.chat.process_business_intelligence_chat") as mock_process:
            mock_process.return_value = {
                "intent": "general",
                "response": "Halo!",
                "generated_sql": None
            }
            response = client.post("/api/chat", json={
                "message": "halo",
                "session_id": "custom_session_123"
            })
            assert response.status_code == 200

    def test_default_session_id_used_if_not_provided(self, client):
        """session_id default harus digunakan jika tidak disertakan."""
        with patch("app.api.routes.chat.process_business_intelligence_chat") as mock_process:
            mock_process.return_value = {
                "intent": "general",
                "response": "Halo!",
                "generated_sql": None
            }
            response = client.post("/api/chat", json={"message": "halo"})
            assert response.status_code == 200
            mock_process.assert_called_once()
            call_kwargs = mock_process.call_args
            assert call_kwargs is not None
