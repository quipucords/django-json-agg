"""Testing setup."""

from __future__ import annotations

import django
import pytest
from django.conf import settings


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--db-vendor", action="store", default="sqlite")
    parser.addoption("--db-name", action="store", default="postgres")
    parser.addoption("--db-user", action="store", default="postgres")
    parser.addoption("--db-password", action="store", default="")
    parser.addoption("--db-host", action="store", default="127.0.0.1")
    parser.addoption("--db-port", action="store", default="5432")


@pytest.fixture(scope="session")
def db_vendor(pytestconfig):
    return pytestconfig.getoption("--db-vendor")


def pytest_configure(config: pytest.Config):
    db_settings = get_db_settings(config)
    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": db_settings,
        },
        SITE_ID=1,
        SECRET_KEY="not a secret in tests",  # noqa: S106
        USE_I18N=True,
        STATIC_URL="/static/",
        ROOT_URLCONF="tests.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {
                    "debug": True,
                },
            },
        ],
        MIDDLEWARE=(
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.staticfiles",
            "json_agg",
            "tests",
        ),
        PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
    )

    django.setup()


def get_db_settings(config: pytest.Config):
    valid_db_vendors = ["sqlite", "postgresql"]
    vendor_name = config.getoption("--db-vendor")
    if vendor_name not in valid_db_vendors:
        raise pytest.UsageError(
            f"Invalid db vendor ('{vendor_name}'). Valid values are {valid_db_vendors}."
        )
    settings_per_vendor = {
        "sqlite": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "postgresql": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config.getoption("--db-name"),
            "USER": config.getoption("--db-user"),
            "PASSWORD": config.getoption("--db-password"),
            "HOST": config.getoption("--db-host"),
            "PORT": config.getoption("--db-port"),
        },
    }

    db_settings = settings_per_vendor[vendor_name]
    return db_settings
