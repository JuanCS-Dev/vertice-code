from __future__ import annotations

from pathlib import Path

from vertice_tui.core.ui_bridge import AutocompleteBridge


def test_warmup_file_cache_scans_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    (tmp_path / "a.py").write_text("print('a')\n")
    (tmp_path / "b.txt").write_text("b\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("# c\n")

    bridge = AutocompleteBridge()
    files = bridge.warmup_file_cache(max_files=100)
    paths = {Path(item) for item in files}

    assert Path("a.py") in paths
    assert Path("b.txt") in paths
    assert Path("sub") / "c.md" in paths

    completions = bridge.get_completions("@a", max_results=10)
    assert "@a.py" in {completion["text"] for completion in completions}


def test_warmup_file_cache_rescans_when_root_changes(tmp_path: Path) -> None:
    root1 = tmp_path / "root1"
    root1.mkdir()
    (root1 / "one.py").write_text("x\n")

    root2 = tmp_path / "root2"
    root2.mkdir()
    (root2 / "two.py").write_text("y\n")

    bridge = AutocompleteBridge()
    files1 = bridge.warmup_file_cache(root=root1, max_files=100)
    assert Path("one.py") in {Path(item) for item in files1}

    files2 = bridge.warmup_file_cache(root=root2, max_files=100)
    paths2 = {Path(item) for item in files2}

    assert Path("two.py") in paths2
    assert Path("one.py") not in paths2
