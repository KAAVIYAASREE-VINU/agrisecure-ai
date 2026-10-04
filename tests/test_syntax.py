import pathlib
import py_compile

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = [
    p
    for d in ("ui", "voice", "assistant", "core", "data")
    for p in (ROOT / d).glob("*.py")
] + [ROOT / "app.py", ROOT / "config.py"]


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_file_compiles(path):
    py_compile.compile(str(path), doraise=True)