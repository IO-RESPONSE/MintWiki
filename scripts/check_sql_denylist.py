#!/usr/bin/env python3
"""PostgreSQL 전용 SQL feature 금지 목록 검사기.

docs/ansi-sql-persistence-policy.md 의 "PostgreSQL 전용 기능 금지 목록"에
정의된 키워드/함수가 저장소·영속성·마이그레이션 코드에 등장하는지 검사한다.
위반이 하나라도 있으면 위반 목록을 출력하고 종료 코드 1 로 끝낸다.

검사 대상은 정책 문서의 "적용 범위" 절과 동일하다.
"""
import re
import sys
from pathlib import Path

# 검사 대상 경로 (docs/ansi-sql-persistence-policy.md 의 "적용 범위" 절 참고)
TARGET_GLOBS = [
    "src/modules/*/repository.py",
    "src/persistence/**/*.py",
    "migrations/versions/*.py",
]

# 금지 기능 이름 -> 탐지 정규식.
# docs/ansi-sql-persistence-policy.md 의 "PostgreSQL 전용 기능 금지 목록" 표와 대응한다.
DENYLIST: dict[str, re.Pattern] = {
    "RETURNING": re.compile(r"\bRETURNING\b|\.returning\(", re.IGNORECASE),
    "ILIKE": re.compile(r"\bILIKE\b|\.ilike\(", re.IGNORECASE),
    "JSONB": re.compile(r"\bJSONB\b", re.IGNORECASE),
    "JSON 연산자(->, ->>, @>)": re.compile(r"""['"][^'"]*(->>?|@>)[^'"]*['"]"""),
    "ARRAY 타입": re.compile(r"\bARRAY\b"),
    "SERIAL/BIGSERIAL": re.compile(r"\b(BIG)?SERIAL\b", re.IGNORECASE),
    "gen_random_uuid()": re.compile(r"gen_random_uuid\s*\(", re.IGNORECASE),
    "uuid_generate_v4()": re.compile(r"uuid_generate_v4\s*\(", re.IGNORECASE),
    "ON CONFLICT (upsert)": re.compile(
        r"\bON\s+CONFLICT\b|on_conflict_do_(update|nothing)", re.IGNORECASE
    ),
    "SKIP LOCKED": re.compile(r"\bSKIP\s+LOCKED\b|skip_locked", re.IGNORECASE),
    "tsvector/tsquery": re.compile(r"\btsvector\b|\btsquery\b", re.IGNORECASE),
    "DISTINCT ON": re.compile(r"\bDISTINCT\s+ON\b|distinct_on", re.IGNORECASE),
    "generate_series()": re.compile(r"generate_series\s*\(", re.IGNORECASE),
    "LISTEN/NOTIFY": re.compile(r"\bLISTEN\b|\bNOTIFY\b", re.IGNORECASE),
    "테이블 상속(INHERITS)": re.compile(r"\bINHERITS\b", re.IGNORECASE),
    "부분 인덱스/EXCLUDE 제약": re.compile(
        r"CREATE\s+INDEX[^;]*\bWHERE\b|\bEXCLUDE\s+USING\b|ExcludeConstraint"
        r"|postgresql_where",
        re.IGNORECASE,
    ),
    "네이티브 ENUM 타입": re.compile(
        r"CREATE\s+TYPE\s+\w+\s+AS\s+ENUM|postgresql\.ENUM", re.IGNORECASE
    ),
    "age()/date_trunc()": re.compile(r"\bage\s*\(|\bdate_trunc\s*\(", re.IGNORECASE),
}


def iter_target_files(root: Path) -> list[Path]:
    """검사 대상 파일 목록을 수집한다.

    Args:
        root: 저장소 루트 디렉토리

    Returns:
        존재하는 검사 대상 파일 경로 목록 (정렬됨)
    """
    files: list[Path] = []
    for pattern in TARGET_GLOBS:
        files.extend(sorted(root.glob(pattern)))
    return files


def check_file(path: Path) -> list[str]:
    """단일 파일에서 금지된 SQL feature 사용을 검사한다.

    Args:
        path: 검사할 파일 경로

    Returns:
        위반 메시지 목록 (위반이 없으면 빈 리스트)
    """
    violations: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for lineno, line in enumerate(lines, start=1):
        for feature, pattern in DENYLIST.items():
            if pattern.search(line):
                violations.append(f"{path}:{lineno}: 금지된 SQL feature '{feature}' 사용")
    return violations


def main() -> int:
    """검사 대상 전체를 검사하고 위반 여부에 따라 종료 코드를 반환한다.

    Returns:
        위반이 없으면 0, 있으면 1
    """
    root = Path(__file__).resolve().parent.parent

    all_violations: list[str] = []
    for path in iter_target_files(root):
        all_violations.extend(check_file(path))

    if all_violations:
        print("❌ PostgreSQL 전용 SQL feature 금지 목록 위반 발견:", file=sys.stderr)
        for message in all_violations:
            print(f"  - {message}", file=sys.stderr)
        print(
            "\n금지 목록과 대체 방법은 docs/ansi-sql-persistence-policy.md 의"
            " 'PostgreSQL 전용 기능 금지 목록' 을 참고하세요.",
            file=sys.stderr,
        )
        return 1

    print("✅ SQL feature 금지 목록 검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
