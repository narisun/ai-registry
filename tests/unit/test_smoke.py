import os
import pathlib

# Point the loader at the repo's config/ dir and supply the required secret
# before src.app is first imported (module-level RegistryApp() calls load()).
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("INTERNAL_API_KEY", "smoke-test-key")
os.environ.setdefault("CONFIG_DIR", str(_REPO_ROOT / "config"))


def test_app_imports():
    from src.app import app
    assert app is not None
