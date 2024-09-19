import os

import pytest

from app.factories.application import setup_app


@pytest.fixture(scope="session")
def app():
    os.putenv("QUDO_ENV", "testing")
    app = setup_app()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
