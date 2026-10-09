"""Packaging checks: every tool is registered, valid, and backed by source."""

from pathlib import Path

import pytest
import yaml
from dify_plugin.entities.tool import ToolConfiguration

ROOT = Path(__file__).resolve().parent.parent
PROVIDER = yaml.safe_load((ROOT / "provider/anakin.yaml").read_text())
REGISTERED = PROVIDER["tools"]
LANGS = {"en_US", "zh_Hans", "pt_BR", "ja_JP"}


def test_every_tool_yaml_is_registered():
    on_disk = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "tools").glob("*.yaml"))
    assert sorted(REGISTERED) == on_disk


def test_no_duplicate_registrations():
    assert len(REGISTERED) == len(set(REGISTERED))


@pytest.mark.parametrize("path", REGISTERED)
def test_tool_yaml_validates(path):
    raw = yaml.safe_load((ROOT / path).read_text())
    config = ToolConfiguration(**raw)
    assert (ROOT / config.extra.python.source).is_file()
    assert Path(path).stem == config.identity.name


@pytest.mark.parametrize("path", REGISTERED)
def test_tool_yaml_is_fully_translated(path):
    raw = yaml.safe_load((ROOT / path).read_text())
    assert set(raw["identity"]["label"]) == LANGS
    assert set(raw["description"]["human"]) == LANGS
    for param in raw.get("parameters") or []:
        assert set(param["label"]) == LANGS, param["name"]
        assert set(param["human_description"]) == LANGS, param["name"]


def test_tool_count():
    assert len(REGISTERED) == 24
