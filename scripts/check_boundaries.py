#!/usr/bin/env python3
"""도메인 이식성 경계 검사기.

향후 백엔드를 Python 에서 PHP 로 모듈별 전환할 수 있도록, 도메인 계층에
웹 프레임워크·ORM·검증 라이브러리가 새어 들어오지 못하게 막는다.

규칙 (src/modules/ 하위에만 적용):
- ``router.py``      → fastapi 계열만 허용 (HTTP 어댑터)
- ``repository.py``  → sqlalchemy 계열만 허용 (영속성 어댑터)
- ``schema.py``      → pydantic 만 허용 (엣지 DTO)
- 그 외 모든 파일   → 위 프레임워크를 하나도 import 할 수 없음 (순수 도메인)

``src/app`` (부트스트랩) 와 ``src/persistence`` (ORM 어댑터) 는 프레임워크
전용 계층이므로 검사 대상에서 제외한다.

위반이 하나라도 있으면 위반 목록을 출력하고 종료 코드 1 로 끝낸다.
"""
import ast
import sys
from pathlib import Path

# 도메인에 침투하면 안 되는 프레임워크의 최상위 패키지명
FORBIDDEN_ROOTS = {
    "fastapi",
    "starlette",
    "sqlalchemy",
    "pydantic",
    "asyncpg",
    "uvicorn",
    "alembic",
}

# 파일명 → 그 파일에서 예외적으로 허용되는 프레임워크 최상위 패키지 집합
FILENAME_ALLOWANCES = {
    "router.py": {"fastapi", "starlette"},
    "repository.py": {"sqlalchemy"},
    "schema.py": {"pydantic"},
}

# 검사 루트 (도메인 계층). 이 디렉토리 하위만 순수성을 강제한다.
DOMAIN_ROOT = Path("src/modules")


def imported_roots(tree: ast.AST) -> set[str]:
    """AST 에서 import 된 모든 최상위 패키지명을 수집한다.

    ``import a.b.c`` 와 ``from a.b import c`` 모두 최상위 ``a`` 로 환원한다.

    Args:
        tree: 파싱된 모듈 AST

    Returns:
        import 된 최상위 패키지명 집합
    """
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # 상대 import (from . import x) 는 level>0 이며 module 이 없을 수 있다.
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return roots


def check_file(path: Path) -> list[str]:
    """단일 파일의 경계 위반을 검사한다.

    Args:
        path: 검사할 파이썬 파일 경로

    Returns:
        위반 메시지 목록 (위반이 없으면 빈 리스트)
    """
    allowed = FILENAME_ALLOWANCES.get(path.name, set())
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    violations: list[str] = []
    for root in sorted(imported_roots(tree)):
        if root in FORBIDDEN_ROOTS and root not in allowed:
            violations.append(f"{path}: 도메인 계층이 '{root}' 를 import 함")
    return violations


def main() -> int:
    """도메인 계층 전체를 검사하고 위반 여부에 따라 종료 코드를 반환한다.

    Returns:
        위반이 없으면 0, 있으면 1
    """
    if not DOMAIN_ROOT.exists():
        print(f"경계 검사 대상 디렉토리가 없습니다: {DOMAIN_ROOT}", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    for path in sorted(DOMAIN_ROOT.rglob("*.py")):
        all_violations.extend(check_file(path))

    if all_violations:
        print("❌ 도메인 이식성 경계 위반 발견:", file=sys.stderr)
        for message in all_violations:
            print(f"  - {message}", file=sys.stderr)
        print(
            "\n도메인 계층(service/model/순수 로직)은 프레임워크에 의존하면 안 됩니다.\n"
            "프레임워크 코드는 router.py / repository.py / schema.py 에만 두세요.\n"
            "자세한 규칙은 AGENTS.md 의 '이식성 계층 규칙' 을 참고하세요.",
            file=sys.stderr,
        )
        return 1

    print("✅ 도메인 이식성 경계 검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
