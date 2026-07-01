"""공유 SQLAlchemy 메타데이터 및 기본 모델."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# 모든 ORM 모델이 공유하는 메타데이터
metadata = MetaData()


class Base(DeclarativeBase):
    """모든 ORM 모델이 상속하는 기본 클래스."""

    metadata = metadata
