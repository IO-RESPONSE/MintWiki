#!/usr/bin/env python3
"""DB 모듈 경계 검사기.

DB 모듈(src/persistence/)이 ORM 구현 세부사항(SQLAlchemy/asyncpg)을
적절히 숨기고, 도메인이 이들을 직접 보지 않게 한다.

규칙:
1. src/persistence/ 안에서 SQLAlchemy를 import할 수 있는 파일 목록:
   - models.py (ORM 모델 정의)
   - base.py (기본 클래스/설정)
   - transaction.py (트랜잭션 관리)
   - seed_loader.py (시드 로더)
   - migration_state_service.py (마이그레이션 상태 관리)
   - db_adapter.py는 SQLAlchemy를 import하지 않음 (순수 인터페이스)

2. src/modules/ 안의 도메인 파일은 SQLAlchemy를 직접 import하지 않음
   (이미 check_boundaries.py가 검사하지만, DB 경계 관점에서도 확인)

위반이 하나라도 있으면 위반 목록을 출력하고 종료 코드 1로 끝낸다.
"""
import ast
import sys
from pathlib import Path

# DB 모듈 내에서 SQLAlchemy를 import할 수 있는 파일들
PERSISTENCE_ALLOWED_FILES = {
    "models.py",
    "base.py",
    "transaction.py",
    "seed_loader.py",
    "migration_state_service.py",
}

# 도메인 모듈 내에서 SQLAlchemy를 import할 수 있는 파일들 (어댑터)
DOMAIN_ADAPTER_FILES = {
    "repository.py",  # 영속성 어댑터
}

# DB 모듈에 침투하면 안 되는 것들
DB_IMPL_ROOTS = {
    "sqlalchemy",
    "asyncpg",
}

# DB 모듈 경로
DB_MODULE_ROOT = Path("src/persistence")
DOMAIN_ROOT = Path("src/modules")


def imported_roots(tree: ast.AST) -> set[str]:
    """AST에서 import된 모든 최상위 패키지명을 수집한다.

    ``import a.b.c``와 ``from a.b import c`` 모두 최상위 ``a``로 환원한다.

    Args:
        tree: 파싱된 모듈 AST

    Returns:
        import된 최상위 패키지명 집합
    """
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return roots


def check_db_module_file(path: Path) -> list[str]:
    """DB 모듈 내 단일 파일의 경계 위반을 검사한다.

    Args:
        path: 검사할 파이썬 파일 경로

    Returns:
        위반 메시지 목록 (위반이 없으면 빈 리스트)
    """
    violations: list[str] = []
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    imported = imported_roots(tree)
    disallowed_imports = imported & DB_IMPL_ROOTS

    # db_adapter.py는 SQLAlchemy를 import하면 안 됨 (순수 인터페이스)
    if path.name == "db_adapter.py" and disallowed_imports:
        violations.append(
            f"{path}: DB 어댑터 인터페이스가 '{disallowed_imports}' 를 import 함"
        )

    # 허용된 파일 목록에 없는 파일이 SQLAlchemy를 import하면 안 됨
    if path.name not in PERSISTENCE_ALLOWED_FILES and disallowed_imports:
        violations.append(
            f"{path}: DB 모듈의 비허용 파일이 '{disallowed_imports}' 를 import 함"
        )

    return violations


def check_domain_file(path: Path) -> list[str]:
    """도메인 파일이 DB 구현을 직접 import하지 않는지 검사한다.

    Args:
        path: 검사할 파이썬 파일 경로

    Returns:
        위반 메시지 목록 (위반이 없으면 빈 리스트)
    """
    violations: list[str] = []
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    imported = imported_roots(tree)
    disallowed_imports = imported & DB_IMPL_ROOTS

    # 어댑터 파일(repository.py 등)은 SQLAlchemy 사용 허용
    if path.name in DOMAIN_ADAPTER_FILES:
        return violations

    if disallowed_imports:
        violations.append(
            f"{path}: 도메인 계층이 DB 구현 '{disallowed_imports}' 를 직접 import 함"
        )

    return violations


def main() -> int:
    """DB 모듈 경계를 검사하고 위반 여부에 따라 종료 코드를 반환한다.

    Returns:
        위반이 없으면 0, 있으면 1
    """
    all_violations: list[str] = []

    # DB 모듈 파일 검사
    if DB_MODULE_ROOT.exists():
        for path in sorted(DB_MODULE_ROOT.rglob("*.py")):
            all_violations.extend(check_db_module_file(path))

    # 도메인 파일 검사
    if DOMAIN_ROOT.exists():
        for path in sorted(DOMAIN_ROOT.rglob("*.py")):
            all_violations.extend(check_domain_file(path))

    if all_violations:
        print("❌ DB 모듈 경계 위반 발견:", file=sys.stderr)
        for message in all_violations:
            print(f"  - {message}", file=sys.stderr)
        print(
            "\nDB 모듈(src/persistence/)의 SQLAlchemy/asyncpg 사용은 제한되어 있습니다.\n"
            "도메인은 DbAdapter 인터페이스를 통해서만 DB에 접근해야 합니다.\n"
            "자세한 규칙은 tasks 파일의 '0498 Add DB module boundary check'를 참고하세요.",
            file=sys.stderr,
        )
        return 1

    print("✅ DB 모듈 경계 검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
