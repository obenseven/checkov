import json
import os
from pathlib import Path

import pytest
from mock import AsyncMock
from pytest_mock import MockerFixture

from checkov.sca_package.scanner import Scanner, CHECKOV_SEC_IN_WEEK


def test_should_download_new_twistcli(tmp_path: Path):
    # given
    scanner = Scanner()
    twistcli_path = tmp_path / "twistcli"
    scanner.twistcli_path = twistcli_path

    # then
    assert scanner.should_download()


def test_not_should_download_twistcli(tmp_path: Path):
    # given
    scanner = Scanner()
    os.environ["CHECKOV_EXPIRATION_TIME_IN_SEC"] = str(CHECKOV_SEC_IN_WEEK)
    twistcli_path = tmp_path / "twistcli"
    twistcli_path.touch()
    scanner.twistcli_path = twistcli_path

    # then
    assert not scanner.should_download()
   

def test_should_download_twistcli_again(tmp_path: Path):
    # given
    scanner = Scanner()
    os.environ["CHECKOV_EXPIRATION_TIME_IN_SEC"] = "0"
    twistcli_path = tmp_path / "twistcli"
    twistcli_path.touch()
    scanner.twistcli_path = twistcli_path

    # then
    assert scanner.should_download()
   

def test_cleanup_twistcli_exists(tmp_path: Path):
    # given
    scanner = Scanner()

    # prepare local paths
    twistcli_path = tmp_path / "twistcli"
    twistcli_path.touch()
    scanner.twistcli_path = twistcli_path

    # when
    scanner.cleanup_twictcli()

    # then
    assert not twistcli_path.exists()


def test_cleanup_twistcli_not_exists(tmp_path: Path):
    # given
    scanner = Scanner()

    # prepare local paths
    twistcli_path = tmp_path / "twistcli"
    scanner.twistcli_path = twistcli_path

    # when
    scanner.cleanup_twictcli()

    # then
    assert not twistcli_path.exists()


@pytest.mark.asyncio
async def test_run_scan(mocker: MockerFixture, tmp_path: Path, mock_bc_integration, scan_result):
    # given
    subprocess_async_mock = AsyncMock()
    subprocess_async_mock.return_value.communicate = AsyncMock(return_value=("test".encode(encoding="utf-8"),
                                                                             "test".encode(encoding="utf-8")))
    subprocess_async_mock.return_value.wait = AsyncMock(return_value=0)
    mocker.patch("asyncio.create_subprocess_shell", side_effect=subprocess_async_mock)

    # prepare local paths
    app_temp_dir = tmp_path / "app"
    app_temp_dir.mkdir()
    output_path = app_temp_dir / "requirements_result.json"
    output_path.write_text(json.dumps(scan_result))

    # when
    result = await Scanner().run_scan(
        command="./twistcli coderepo scan",
        input_path=app_temp_dir / "requirements.txt",
        output_path=output_path,
    )

    # then
    assert result == scan_result
    assert not output_path.exists()
    subprocess_async_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_scan_fail_on_scan(mocker: MockerFixture, mock_bc_integration):
    # given
    subprocess_async_mock = AsyncMock()
    subprocess_async_mock.return_value.communicate = AsyncMock(return_value=("test".encode(encoding="utf-8"),
                                                                             "test".encode(encoding="utf-8")))
    subprocess_async_mock.return_value.wait = AsyncMock(return_value=1)
    mocker.patch("asyncio.create_subprocess_shell", side_effect=subprocess_async_mock)

    # when
    result = await Scanner().run_scan(
        command="./twistcli coderepo scan",
        input_path=Path("app/requirements.txt"),
        output_path=Path("app/requirements_result.json"),
    )

    # then
    assert result == {}
    subprocess_async_mock.assert_awaited_once()
