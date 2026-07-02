"""
Portable seed fixture 로더.

ANSI SQL 기반의 INSERT 문을 파싱하여 데이터베이스에 로드한다.
PostgreSQL과 MariaDB 양쪽에서 동일하게 동작한다.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text


class SeedLoader:
    """Portable seed fixture를 로드하는 클래스."""

    def __init__(self, fixtures_dir: Optional[Path] = None):
        """
        초기화.

        Args:
            fixtures_dir: seed 파일들이 있는 디렉토리. 지정하지 않으면 tests/fixtures/seed를 사용.
        """
        if fixtures_dir is None:
            # 기본값: tests/fixtures/seed
            # 이 모듈이 src/persistence에 있으므로, 상대 경로로 접근
            project_root = Path(__file__).parent.parent.parent
            fixtures_dir = project_root / "tests" / "fixtures" / "seed"

        self.fixtures_dir = fixtures_dir

    async def load_seed(self, session: AsyncSession, table_name: str) -> None:
        """
        특정 테이블의 seed 데이터를 로드한다.

        Args:
            session: SQLAlchemy AsyncSession
            table_name: 로드할 테이블명 (파일명으로도 사용: {table_name}.sql)
        """
        sql_file = self.fixtures_dir / f"{table_name}.sql"

        if not sql_file.exists():
            raise FileNotFoundError(f"Seed file not found: {sql_file}")

        # SQL 파일 읽기
        sql_content = sql_file.read_text(encoding="utf-8")

        # INSERT 문 파싱 및 실행
        insert_statements = self._parse_insert_statements(sql_content)

        for insert_sql in insert_statements:
            await session.execute(text(insert_sql))

        await session.commit()

    async def load_all_seeds(self, session: AsyncSession) -> None:
        """
        모든 seed 파일을 로드한다.

        파일 순서대로 로드되므로, FK 종속성을 고려하여 파일명을 정렬할 것.
        """
        seed_files = sorted(self.fixtures_dir.glob("*.sql"))

        for seed_file in seed_files:
            if seed_file.name.startswith("."):
                continue  # 숨김 파일 무시

            table_name = seed_file.stem
            await self.load_seed(session, table_name)

    def _parse_insert_statements(self, sql_content: str) -> List[str]:
        """
        SQL 콘텐츠에서 INSERT 문들을 추출한다.

        Args:
            sql_content: SQL 파일의 전체 내용

        Returns:
            INSERT 문 리스트 (주석 제거, 완전한 문)
        """
        # 주석 제거
        lines = sql_content.split("\n")
        cleaned_lines = []

        for line in lines:
            # SQL 라인 주석 제거 (-- 이후의 모든 내용)
            line = re.sub(r"--.*$", "", line)
            cleaned_lines.append(line)

        sql_content = "\n".join(cleaned_lines)

        # 블록 주석 제거 (/* ... */)
        sql_content = re.sub(r"/\*.*?\*/", "", sql_content, flags=re.DOTALL)

        # INSERT 문 추출
        # INSERT INTO ... VALUES (...); 패턴
        pattern = r"INSERT\s+INTO\s+\w+\s*\([^)]*\)\s*VALUES\s*\([^)]*\)\s*;"

        insert_statements = re.findall(pattern, sql_content, re.IGNORECASE | re.DOTALL)

        return insert_statements
