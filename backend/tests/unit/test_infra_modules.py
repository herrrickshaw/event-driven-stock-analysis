"""utils/logging.py, utils/errors.py, models/base.py and the placeholder
db clients."""

import json
import logging
import sys

import pytest

from config.settings import settings


def record(msg="hello %s", args=("w",), exc_info=None, **extra):
    r = logging.LogRecord("lg", logging.WARNING, __file__, 42, msg, args, exc_info, func="fn")
    for k, v in extra.items():
        setattr(r, k, v)
    return r


@pytest.mark.unit
class TestJSONFormatter:
    def fmt(self, rec):
        from utils.logging import JSONFormatter

        return json.loads(JSONFormatter().format(rec))

    def test_core_fields(self):
        out = self.fmt(record())
        assert out["level"] == "WARNING" and out["logger"] == "lg"
        assert out["message"] == "hello w" and out["function"] == "fn" and out["line"] == 42
        assert out["module"] == record().module
        assert "T" in out["timestamp"]
        assert set(out) == {"timestamp", "level", "logger", "message", "module", "function", "line"}

    def test_optional_ids_only_when_present(self):
        out = self.fmt(record(user_id="u1", portfolio_id=9))
        assert out["user_id"] == "u1" and out["portfolio_id"] == 9
        assert "user_id" not in self.fmt(record(portfolio_id=1))
        assert "portfolio_id" not in self.fmt(record(user_id="x"))

    def test_exception_text_included(self):
        try:
            raise ValueError("kaboom")
        except ValueError:
            out = self.fmt(record(exc_info=sys.exc_info()))
        assert "ValueError: kaboom" in out["exception"]


@pytest.mark.unit
class TestSetupLogging:
    @pytest.fixture(autouse=True)
    def restore_root(self):
        root = logging.getLogger()
        handlers, level = list(root.handlers), root.level
        names = ("sqlalchemy", "httpx", "uvicorn")
        levels = {n: logging.getLogger(n).level for n in names}
        yield
        root.handlers = handlers
        root.setLevel(level)
        for n, lv in levels.items():
            logging.getLogger(n).setLevel(lv)

    def test_json_format_and_levels(self, monkeypatch):
        from utils.logging import JSONFormatter, setup_logging

        monkeypatch.setattr(settings, "log_format", "json")
        monkeypatch.setattr(settings, "log_level", "ERROR")
        logging.getLogger().addHandler(logging.NullHandler())
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.ERROR
        assert len(root.handlers) == 1 and isinstance(root.handlers[0].formatter, JSONFormatter)
        assert logging.getLogger("sqlalchemy").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("uvicorn").level == logging.INFO

    def test_text_format(self, monkeypatch):
        from utils.logging import JSONFormatter, setup_logging

        monkeypatch.setattr(settings, "log_format", "text")
        monkeypatch.setattr(settings, "log_level", "DEBUG")
        setup_logging()
        h = logging.getLogger().handlers[0]
        assert not isinstance(h.formatter, JSONFormatter)
        assert logging.getLogger().level == logging.DEBUG
        assert h.formatter.format(record("m", ())).endswith("lg - WARNING - m")

    def test_get_logger(self):
        from utils.logging import get_logger

        assert get_logger("abc") is logging.getLogger("abc")


@pytest.mark.unit
class TestErrors:
    def test_api_error_defaults(self):
        from utils.errors import APIError

        e = APIError()
        assert (e.status_code, e.detail) == (400, "An error occurred")
        e = APIError(418, "teapot")
        assert (e.status_code, e.detail) == (418, "teapot")

    def test_validation_and_database_errors(self):
        from utils.errors import DatabaseError, ValidationError

        v = ValidationError("bad input")
        assert (v.status_code, v.detail) == (422, "bad input")
        d = DatabaseError()
        assert (d.status_code, d.detail) == (500, "Database operation failed")
        assert DatabaseError("conn lost").detail == "conn lost"

    def test_external_service_and_calculation_message_formats(self):
        from utils.errors import CalculationError, ExternalServiceError

        assert ExternalServiceError("yfinance").detail == "Error fetching data from yfinance"
        e = ExternalServiceError("yfinance", "timeout")
        assert (e.status_code, e.detail) == (503, "Error fetching data from yfinance: timeout")
        assert CalculationError("beta").detail == "Error calculating beta"
        c = CalculationError("beta", "singular")
        assert (c.status_code, c.detail) == (500, "Error calculating beta: singular")

    def test_insufficient_data_custom_detail(self):
        from utils.errors import InsufficientDataError

        assert InsufficientDataError("need 30 days").detail == "need 30 days"

    def test_hierarchy(self):
        from fastapi import HTTPException

        from utils.errors import InvalidWeightsError, PortfolioNotFoundError, ValidationError

        assert issubclass(InvalidWeightsError, ValidationError) and issubclass(PortfolioNotFoundError, HTTPException)


@pytest.mark.unit
class TestModelsBase:
    def test_get_db_yields_session_then_closes_it(self, monkeypatch):
        import models.base as base

        class S:
            closed = False

            def close(self):
                self.closed = True

        s = S()
        monkeypatch.setattr(base, "SessionLocal", lambda: s)
        gen = base.get_db()
        assert next(gen) is s and not s.closed
        with pytest.raises(StopIteration):
            next(gen)
        assert s.closed

    def test_get_db_closes_on_error(self, monkeypatch):
        import models.base as base

        class S:
            closed = False

            def close(self):
                self.closed = True

        s = S()
        monkeypatch.setattr(base, "SessionLocal", lambda: s)
        gen = base.get_db()
        next(gen)
        with pytest.raises(RuntimeError):
            gen.throw(RuntimeError("x"))
        assert s.closed

    def test_init_db_creates_all_tables_on_engine(self, monkeypatch):
        import models.base as base

        calls = []
        monkeypatch.setattr(base.Base.metadata, "create_all", lambda bind: calls.append(bind))
        base.init_db()
        assert calls == [base.engine]

    def test_session_factory_flags(self):
        import models.base as base

        s = base.SessionLocal()
        try:
            assert s.autoflush is False and s.bind is base.engine
        finally:
            s.close()


@pytest.mark.unit
@pytest.mark.parametrize("modname", ["db.cassandra_client", "db.postgres_client"])
def test_placeholder_clients_report_unavailable(modname):
    import importlib

    m = importlib.import_module(modname)
    assert m.is_available() is False
    assert m.connect() is False
    assert m.close() is None
