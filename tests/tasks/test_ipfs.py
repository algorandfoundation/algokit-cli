import pytest
from algokit.core.tasks.ipfs import ALGOKIT_WEB3_STORAGE_TOKEN_KEY
from pytest_httpx import HTTPXMock

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke


class TestIpfsLogin:
    def test_ipfs_login_exists(self, mock_keyring: dict[str, str]) -> None:
        mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] = "test"

        result = invoke("task ipfs login", input="test\ntest")

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_ipfs_login_successful(self, mock_keyring: dict[str, str | None]) -> None:
        mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] = None
        result = invoke("task ipfs login", input="test\ntest")

        # Assert
        assert result.exit_code == 0
        verify(result.output)
        assert mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] == "test"


class TestIpfsLogout:
    def test_ipfs_logout(self, mock_keyring: dict[str, str | None]) -> None:
        mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] = "test"
        result = invoke("task ipfs logout")

        # Assert
        assert result.exit_code == 0
        verify(result.output)
        assert mock_keyring.get(ALGOKIT_WEB3_STORAGE_TOKEN_KEY) is None


class TestIpfsUpload:
    def test_ipfs_upload_successful(
        self, tmp_path_factory: pytest.TempPathFactory, httpx_mock: HTTPXMock, mock_keyring: dict[str, str | None]
    ) -> None:
        mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] = "test"
        cwd = tmp_path_factory.mktemp("cwd")
        (cwd / "dummy.txt").write_text("dummy text to upload")

        httpx_mock.add_response(status_code=200, json={"ok": True, "cid": "test"})
        result = invoke("task ipfs upload --file dummy.txt", cwd=cwd)

        # Assert
        assert result.exit_code == 0
        verify(result.output)

    def test_ipfs_not_logged_in(
        self, tmp_path_factory: pytest.TempPathFactory, mock_keyring: dict[str, str | None]
    ) -> None:
        mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] = None
        cwd = tmp_path_factory.mktemp("cwd")
        (cwd / "dummy.txt").write_text("dummy text to upload")

        result = invoke("task ipfs upload --file dummy.txt", cwd=cwd)

        # Assert
        assert result.exit_code == 1
        assert "You are not logged in" in result.output

    def test_ipfs_upload_http_error(
        self,
        tmp_path_factory: pytest.TempPathFactory,
        httpx_mock: HTTPXMock,
        mock_keyring: dict[str, str | None],
    ) -> None:
        mock_keyring[ALGOKIT_WEB3_STORAGE_TOKEN_KEY] = "test"
        cwd = tmp_path_factory.mktemp("cwd")
        (cwd / "dummy.txt").write_text("dummy text to upload")

        httpx_mock.add_response(status_code=500, json={"ok": False, "cid": "test"})
        result = invoke("task ipfs upload --file dummy.txt", cwd=cwd)

        # Assert
        assert result.exit_code == 1
        verify(result.output)
