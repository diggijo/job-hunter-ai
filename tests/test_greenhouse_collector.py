import pytest

from app.collectors.greenhouse import get_greenhouse_jobs


def test_greenhouse_rejects_incomplete_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "jobs": [
                    {"id": i}
                    for i in range(95)
                ],
                "meta": {
                    "total": 100
                }
            }

    def fake_get(url, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        "app.collectors.greenhouse.httpx.get",
        fake_get
    )

    with pytest.raises(
        ValueError,
        match="Invalid or incomplete Greenhouse response"
    ):
        get_greenhouse_jobs("testboard")