from pathlib import Path
import pytest
from app.config import settings
from app.tools.db import init_db


@pytest.fixture(autouse=True)
def isolate_test_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Aisla la base de datos de pruebas para garantizar tests 100% deterministas."""
    test_db = tmp_path / "test_reservas.db"
    monkeypatch.setattr(settings, "database_path", test_db)
    init_db(test_db)
