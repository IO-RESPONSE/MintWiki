#!/usr/bin/env python3
"""모듈 → app 역참조 금지 검사기.

``src/app`` 는 FastAPI 부트스트랩(엔트리포인트·설정·DB 엔진 초기화)을 담당하는
UI/API 어댑터 계층이다. 의존 방향은 항상 ``app -> modules`` 여야 하며, 반대로
``src/modules/<모듈>/`` 안의 코드가 ``app`` 패키지를 import 하면 도메인 모듈이
특정 어댑터 조립 방식에 묶여 PHP 등 다른 백엔드로 모듈별 전환할 때 걸림돌이
된다.

이 스크립트는 ``src/modules`` 하위 모든 파일에서 ``app`` (혹은 ``app.*``)
import 를 금지한다. 예외 없이 전체 모듈 트리에 적용된다.

위반이 하나라도 있으면 위반 목록을 출력하고 종료 코드 1 로 끝낸다.
"""
import ast
import sys
from pathlib import Path

# 역참조가 금지되는 UI/API 어댑터 계층의 최상위 패키지명
FORBIDDEN_ROOT = "app"

# 검사 루트 (도메인 계층). 이 디렉토리 하위만 검사한다.
MODULES_ROOT = Path("src/modules")


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
    """단일 파일의 app 역참조 위반을 검사한다.

    Args:
        path: 검사할 파이썬 파일 경로

    Returns:
        위반 메시지 목록 (위반이 없으면 빈 리스트)
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    if FORBIDDEN_ROOT in imported_roots(tree):
        return [f"{path}: 모듈 도메인이 UI/API 어댑터 계층 'app' 을 import 함"]
    return []


def main() -> int:
    """모듈 도메인 전체를 검사하고 위반 여부에 따라 종료 코드를 반환한다.

    Returns:
        위반이 없으면 0, 있으면 1
    """
    if not MODULES_ROOT.exists():
        print(f"검사 대상 디렉토리가 없습니다: {MODULES_ROOT}", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    for path in sorted(MODULES_ROOT.rglob("*.py")):
        all_violations.extend(check_file(path))

    if all_violations:
        print("❌ 모듈 → app 역참조 위반 발견:", file=sys.stderr)
        for message in all_violations:
            print(f"  - {message}", file=sys.stderr)
        print(
            "\nsrc/modules 의 도메인 코드는 src/app (UI/API 부트스트랩 계층)을 "
            "import 할 수 없습니다. 의존 방향은 항상 app -> modules 여야 합니다.",
            file=sys.stderr,
        )
        return 1

    print("✅ 모듈 → app 역참조 검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
