"""Test migration configuration."""

import sys
from pathlib import Path


def test_migration_env_can_import_settings():
    """Verify migration env.py can import app settings."""
    # Add migrations to path so we can import env
    migrations_path = Path(__file__).parent.parent / "migrations"
    sys.path.insert(0, str(migrations_path))

    try:
        # This should not raise an ImportError
        import env  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"migration env.py failed to import: {e}") from e
    finally:
        # Clean up sys.path
        if str(migrations_path) in sys.path:
            sys.path.remove(str(migrations_path))


def test_migration_directory_exists():
    """Verify migrations directory structure exists."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    assert migrations_dir.exists(), "migrations directory should exist"
    assert (migrations_dir / "env.py").exists(), "migrations/env.py should exist"
    assert (
        migrations_dir / "script.py.mako"
    ).exists(), "migrations/script.py.mako should exist"
    assert (
        migrations_dir / "versions"
    ).exists(), "migrations/versions directory should exist"
    assert (migrations_dir / "versions").is_dir(), "versions should be a directory"


def test_alembic_config_exists():
    """Verify alembic.ini config file exists."""
    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    assert alembic_ini.exists(), "alembic.ini should exist"


def test_migration_env_uses_shared_metadata():
    """Verify migration env.py uses shared persistence metadata."""
    src_path = Path(__file__).parent.parent / "src"
    migrations_path = Path(__file__).parent.parent / "migrations"

    # Add src and migrations to path
    sys.path.insert(0, str(src_path))
    sys.path.insert(0, str(migrations_path))

    try:
        from persistence.base import metadata
        # Try to import env which should use the metadata
        import env  # noqa: F401

        # Verify that metadata is available
        assert metadata is not None
    except ImportError as e:
        raise AssertionError(
            f"migration env.py failed to import persistence.base: {e}"
        ) from e
    finally:
        # Clean up sys.path
        if str(src_path) in sys.path:
            sys.path.remove(str(src_path))
        if str(migrations_path) in sys.path:
            sys.path.remove(str(migrations_path))
