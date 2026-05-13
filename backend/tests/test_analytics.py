import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_root_endpoint_exists():
    response = client.get("/")
    assert response.status_code == 200
    assert b"Аналитика врачей" in response.content


def test_analytics_endpoint_structure():
    """Проверяет, что API возвращает ожидаемую структуру JSON"""
    # Мокаем ответ от базы данных, чтобы тест не зависел от реальных данных
    mock_data = {
        "period": {"start": "2023-01-01", "end": "2023-12-31"},
        "revenue": [{"doctor_id": 1, "doctor_name": "Test Doc", "total_revenue": 1000}],
        "referrals": [{"doctor_id": 1, "doctor_name": "Test Doc", "total_patients": 10, "referred_patients": 2,
                       "referral_rate_pct": 20.0}]
    }

    with patch("app.api.db.SessionLocal") as mock_session_factory:
        mock_db = MagicMock()
        mock_db.execute.return_value.mappings.return_value.all.return_value = []

        # Настраиваем мок так, чтобы он возвращал наши данные
        # В реальном проекте лучше использовать dependency_overrides
        mock_session_instance = MagicMock()
        mock_session_instance.execute.return_value.mappings.return_value.all.return_value = [
            MagicMock(**{"doctor_id": 1, "doctor_name": "Test Doc", "total_revenue": 1000})
        ]
        mock_session_factory.return_value = mock_session_instance

        # Простой тест на доступность эндпоинта
        # Для полноценного теста нужно мокать зависимости FastAPI
        response = client.get("/api/analytics?start_date=2023-01-01&end_date=2023-12-31")
        assert response.status_code == 200
        json_response = response.json()
        assert "revenue" in json_response
        assert "referrals" in json_response