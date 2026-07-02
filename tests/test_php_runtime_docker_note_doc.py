"""`docs/php-runtime-docker-note.md` 가 태스크 0432 의 목표("PHP 런타임
로컬 테스트 note를 추가한다")와 Notes 요구사항("shared hosting과
Docker를 구분한다")을 실제로 고정하고 있으며, 저장소 루트의 기존
Docker 설정(Python 앱 전용)을 건드리지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-runtime-docker-note.md"
PHP_README_PATH = REPO_ROOT / "php" / "README.md"
ROOT_DOCKERFILE_PATH = REPO_ROOT / "Dockerfile"
ROOT_COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"

REQUIRED_DOC_HEADINGS = [
    "## 목적: 로컬 테스트 편의, 배포 방식이 아니다",
    "## 로컬 테스트용 Docker 실행 예시",
    "## shared hosting과 Docker의 구분",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]


def test_php_runtime_docker_note_doc_exists():
    """PHP 런타임 Docker note 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_runtime_docker_note_doc_has_required_sections():
    """목적, 실행 예시, shared hosting 구분, 범위 제외, 관련 문서 절이
    모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_runtime_docker_note_doc_distinguishes_shared_hosting_and_docker():
    """태스크 Notes 요구사항: shared hosting과 Docker를 구분해서
    설명한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "shared hosting" in content
    assert "Docker" in content
    assert "배포 목표" in content or "배포 대상" in content


def test_php_runtime_docker_note_doc_gives_docker_run_example():
    """php CLI가 없는 로컬 환경에서 쓸 수 있는 `docker run` 예시를
    포함한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docker run" in content
    assert "php:8.1-cli" in content


def test_php_runtime_docker_note_doc_does_not_claim_new_docker_assets():
    """이 문서가 새 Dockerfile이나 docker-compose 서비스를 추가하지
    않는다는 범위 제외를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "추가하지 않는다" in content


def test_php_runtime_docker_note_doc_references_related_docs():
    """전략 문서, portability 용어집, 테스트 bootstrap 문서, 아키텍처
    문서, php/ 트리 README와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-replacement-strategy.md",
        "docs/portability-glossary.md",
        "docs/php-test-bootstrap.md",
        "docs/architecture.md",
        "php/README.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_readme_links_to_docker_note_doc():
    """`php/README.md`가 새 Docker note 문서를 가리켜, php/ 트리를 보는
    사람이 로컬 테스트용 Docker 사용법을 바로 찾을 수 있다."""
    content = PHP_README_PATH.read_text(encoding="utf-8")
    assert "docs/php-runtime-docker-note.md" in content


def test_root_docker_assets_remain_python_only():
    """저장소 루트의 기존 Docker 설정은 여전히 Python 앱 전용이고, 이
    태스크가 PHP 런타임을 그 안에 끼워 넣지 않았다."""
    dockerfile_content = ROOT_DOCKERFILE_PATH.read_text(encoding="utf-8")
    compose_content = ROOT_COMPOSE_PATH.read_text(encoding="utf-8")
    assert "php" not in dockerfile_content.lower()
    assert "php" not in compose_content.lower()
