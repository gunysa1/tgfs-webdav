from unittest.mock import Mock

from fastapi.testclient import TestClient

from asgidav.app import create_app, extract_path_from_destination, split_path
from asgidav.folder import Folder


class TestGetHandler:
    """The GET route on a collection must not 500 (regression)."""

    def _client(self, member) -> TestClient:
        async def get_member(path: str):
            return member

        return TestClient(create_app(get_member))

    def test_get_on_folder_returns_405_not_500(self):
        client = self._client(Mock(spec=Folder))
        resp = client.get("/somefolder")
        assert resp.status_code == 405
        assert "PROPFIND" in resp.headers.get("Allow", "")

    def test_get_on_missing_returns_404(self):
        client = self._client(None)
        resp = client.get("/does-not-exist")
        assert resp.status_code == 404


class TestAppHelpers:
    def test_split_path_root(self):
        parent, name = split_path("/")
        assert parent == "/"
        assert name == ""

    def test_split_path_single_level(self):
        parent, name = split_path("/test")
        assert parent == "/"
        assert name == "test"

    def test_split_path_multiple_levels(self):
        parent, name = split_path("/path/to/file.txt")
        assert parent == "path/to"
        assert name == "file.txt"

    def test_split_path_trailing_slash(self):
        parent, name = split_path("/path/to/folder/")
        assert parent == "path/to"
        assert name == "folder"

    def test_extract_path_from_destination_http(self):
        url = "http://example.com/webdav/path/to/file.txt"
        result = extract_path_from_destination(url)
        assert result == "/webdav/path/to/file.txt"

    def test_extract_path_from_destination_https(self):
        url = "https://example.com/webdav/path/to/file.txt"
        result = extract_path_from_destination(url)
        assert result == "/webdav/path/to/file.txt"

    def test_extract_path_from_destination_path_only(self):
        path = "/webdav/path/to/file.txt"
        result = extract_path_from_destination(path)
        assert result == "/webdav/path/to/file.txt"

    def test_extract_path_from_destination_encoded(self):
        path = "/webdav/path%20with%20spaces/file.txt"
        result = extract_path_from_destination(path)
        assert result == "/webdav/path with spaces/file.txt"
