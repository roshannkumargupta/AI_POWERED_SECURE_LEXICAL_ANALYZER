import pytest
from apsla.server.workspace import (
    is_ignored_item,
    build_tree_node,
    create_workspace_folder,
    FolderCreateRequest,
)

def test_ignored_temporary_artifacts():
    # Temporary and internal directories must be filtered out
    assert is_ignored_item("__pycache__") is True
    assert is_ignored_item(".git") is True
    assert is_ignored_item(".pytest_cache") is True
    assert is_ignored_item("build") is True
    assert is_ignored_item("dist") is True

    # Temporary files must be filtered out
    assert is_ignored_item("temp.pyc") is True
    assert is_ignored_item("scratch.tmp") is True
    assert is_ignored_item("test.swp") is True

    # Genuine source and project files must NOT be ignored
    assert is_ignored_item("main.cpp") is False
    assert is_ignored_item("sample.py") is False
    assert is_ignored_item("App.java") is False
    assert is_ignored_item("src") is False

@pytest.mark.anyio
async def test_create_and_validate_folder(tmp_path, monkeypatch):
    monkeypatch.setattr("apsla.server.workspace.WORKSPACE_ROOT", tmp_path)
    # Create folder inside workspace
    res = await create_workspace_folder(FolderCreateRequest(path="components/test_dir"))
    assert res["success"] is True
    assert res["path"] == "components/test_dir"
    assert (tmp_path / "components" / "test_dir").is_dir()
