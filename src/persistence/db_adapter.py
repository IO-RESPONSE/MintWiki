"""DB adapter 최소 계약의 skeleton.

docs/db-adapter-contract.md §2(최소 동작 집합)를 실제 Python 클래스로
옮긴다. 이 클래스는 계약을 고정할 뿐 ORM 동작을 확장하지 않는다 — 구체
구현체(SQLAlchemy AsyncSession을 감싸는 어댑터)는 이후 태스크에서 채운다.
"""

from abc import ABC, abstractmethod
from typing import Optional


class DbAdapter(ABC):
    """모든 모듈의 Database* 저장소 구현체가 감싸는 최소 연결/세션 포트.

    Python 쪽 구체 구현은 SQLAlchemy AsyncSession을 감싸고, PHP 쪽 구체
    구현은 PDO 연결을 감싼다. 이 인터페이스 자체는 SQLAlchemy도 PDO도
    아니다 — 두 언어가 공통으로 만족해야 하는 최소 동작만 규정한다.
    statement의 구체 타입은 이 클래스의 범위 밖이다(0451 query builder
    정책이 다룬다).
    """

    @abstractmethod
    async def add(self, row: object) -> None:
        """새 행에 해당하는 객체를 이번 트랜잭션에 추가한다(아직 커밋 전)."""

    @abstractmethod
    async def fetch_one(self, statement: object) -> Optional[object]:
        """조회문을 실행해 첫 결과를 반환한다. 없으면 예외가 아니라 None."""

    @abstractmethod
    async def fetch_all(self, statement: object) -> list[object]:
        """조회문을 실행해 모든 결과를 반환한다. 없으면 빈 리스트."""

    @abstractmethod
    async def execute(self, statement: object) -> None:
        """조회 결과가 필요 없는 INSERT/UPDATE/DELETE 문을 실행한다."""

    @abstractmethod
    async def commit(self) -> None:
        """지금까지의 변경을 확정한다. 실패하면 통합 위반 신호를 던진다."""

    @abstractmethod
    async def rollback(self) -> None:
        """지금까지의 변경을 취소한다."""
