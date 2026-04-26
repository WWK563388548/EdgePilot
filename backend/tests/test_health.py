from backend.app.api.routes.health import health


def test_health() -> None:
    data = health()
    assert data["status"] == "ok"
