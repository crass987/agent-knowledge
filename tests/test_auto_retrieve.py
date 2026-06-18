import importlib.util
from pathlib import Path


def _load():
    script = Path(__file__).resolve().parents[1] / "scripts" / "auto-retrieve.py"
    spec = importlib.util.spec_from_file_location("auto_retrieve", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_blocks_skip_html_commented_examples():
    """The seed example lives inside <!-- --> and must NOT be treated as real."""
    mod = _load()
    text = (
        "# Patterns\n\n"
        "<!--\n---\nkey: example\ninsight: do not match me\n---\n-->\n\n"
        "---\nkey: real-one\ninsight: jira via mcp capability\n---\n"
    )
    joined = "\n".join("\n".join(b) for b in mod.blocks(text))
    assert "example" not in joined
    assert "real-one" in joined


def test_blocks_yield_each_frontmatter_block():
    mod = _load()
    text = "---\nkey: a\n---\n\n---\nkey: b\n---\n"
    keys = []
    for blk in mod.blocks(text):
        body = "\n".join(blk)
        if "key: a" in body:
            keys.append("a")
        if "key: b" in body:
            keys.append("b")
    assert keys == ["a", "b"]
