"""`php/public/index.php` 가 태스크 0394 의 목표
("`public/index.php` 골격을 추가한다")와 Notes 요구사항("요청 정보를
읽고 placeholder 응답만 반환한다"), 그리고 태스크 0419의 목표
("PHP `/health` endpoint를 추가한다")와 Notes 요구사항("앱 이름과 status를
반환한다")을 지키는지 확인한다.

`/health` 외의 라우팅/애플리케이션 로직은 아직 연결되어 있지 않다 — PHP
내장 웹서버(`php -S`)로 실제 HTTP 요청을 보내 `REQUEST_METHOD`/
`REQUEST_URI`가 응답 본문에 반영되는지, `/health`가 JSON으로 app 이름과
status를 반환하는지, 그리고 CLI로 직접 실행해도 크래시 없이 placeholder
응답을 내는지만 검증한다.
"""
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHP_ROOT = REPO_ROOT / "php"
PUBLIC_ROOT = PHP_ROOT / "public"
FRONT_CONTROLLER_PATH = PUBLIC_ROOT / "index.php"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TestPhpPublicFrontController:
    def test_front_controller_file_exists(self):
        assert FRONT_CONTROLLER_PATH.is_file()

    def test_front_controller_has_valid_php_syntax(self):
        result = subprocess.run(
            ["php", "-l", str(FRONT_CONTROLLER_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_front_controller_runs_under_cli_without_crashing(self):
        """웹서버 없이 CLI로 직접 실행해도 크래시하지 않고 placeholder
        응답을 표준 출력에 낸다."""
        result = subprocess.run(
            ["php", str(FRONT_CONTROLLER_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "placeholder" in result.stdout

    def test_front_controller_reflects_request_info_over_http(self):
        port = _free_port()
        server = subprocess.Popen(
            ["php", "-S", f"127.0.0.1:{port}", "-t", str(PUBLIC_ROOT)],
            cwd=PUBLIC_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_for_server(port)

            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/some/path?x=1", timeout=5
            ) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                body = response.read().decode("utf-8")
        finally:
            server.terminate()
            server.wait(timeout=5)

        assert status == 200
        assert "text/plain" in content_type
        assert "method=GET" in body
        assert "uri=/some/path?x=1" in body

    def test_health_route_returns_app_name_and_status(self):
        port = _free_port()
        server = subprocess.Popen(
            ["php", "-S", f"127.0.0.1:{port}", "-t", str(PUBLIC_ROOT)],
            cwd=PUBLIC_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_for_server(port)

            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5
            ) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                body = response.read().decode("utf-8")
        finally:
            server.terminate()
            server.wait(timeout=5)

        assert status == 200
        assert "application/json" in content_type
        payload = json.loads(body)
        assert payload["status"] == "ok"
        assert payload["app"] == "wiki-engine"


def _wait_for_server(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.5)
            return
        except urllib.error.HTTPError:
            return
        except (urllib.error.URLError, ConnectionError) as error:
            last_error = error
            time.sleep(0.05)
    raise TimeoutError(f"php -S server on port {port} never became ready") from last_error
