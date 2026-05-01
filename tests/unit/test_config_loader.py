"""Tests for ConfigLoader (YAML seed parser)."""
import textwrap
import pytest

pytestmark = pytest.mark.unit


def test_load_returns_empty_when_path_is_none():
    from src.config_loader import ConfigLoader
    assert ConfigLoader(seed_path=None).load() == []


def test_load_returns_empty_when_file_missing(tmp_path):
    from src.config_loader import ConfigLoader
    assert ConfigLoader(seed_path=tmp_path / "missing.yaml").load() == []


def test_load_parses_seeded_entries(tmp_path):
    from src.config_loader import ConfigLoader
    p = tmp_path / "registry.yaml"
    p.write_text(textwrap.dedent("""
    services:
      - name: ai-mcp-data
        type: mcp
        expected_url: http://data-mcp:8080
        metadata:
          owner: data-team
      - name: ai-agent-analytics
        type: agent
        expected_url: http://analytics-agent:8000
    """))
    entries = ConfigLoader(seed_path=p).load()
    assert {e.name for e in entries} == {"ai-mcp-data", "ai-agent-analytics"}


def test_load_raises_on_invalid_yaml(tmp_path):
    from src.config_loader import ConfigLoader
    p = tmp_path / "registry.yaml"
    p.write_text("[broken yaml")
    with pytest.raises(ValueError, match="(?i)parse"):
        ConfigLoader(seed_path=p).load()


def test_load_validates_entry_shape(tmp_path):
    from src.config_loader import ConfigLoader
    p = tmp_path / "registry.yaml"
    p.write_text("services:\n  - name: x\n")
    with pytest.raises(ValueError, match="(type|expected_url)"):
        ConfigLoader(seed_path=p).load()


def test_load_aggregates_errors_across_multiple_bad_entries(tmp_path):
    """Multiple bad entries should ALL surface in the error message."""
    from src.config_loader import ConfigLoader
    p = tmp_path / "registry.yaml"
    p.write_text(
        "services:\n"
        "  - name: x\n"           # missing type AND expected_url
        "  - name: y\n"           # also missing type AND expected_url
        "    type: mcp\n"
    )
    with pytest.raises(ValueError) as exc:
        ConfigLoader(seed_path=p).load()
    msg = str(exc.value)
    assert "[0]" in msg
    assert "[1]" in msg
