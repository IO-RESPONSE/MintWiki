"""공유 SQLAlchemy 메타데이터 및 기본 모델 테스트."""

import pytest
from sqlalchemy import Column, Integer, String, MetaData as SQLAlchemyMetaData
from sqlalchemy.orm import DeclarativeBase

from persistence.base import Base, metadata


def test_metadata_is_shared():
    """공유 메타데이터가 정의되었는지 확인한다."""
    assert metadata is not None
    assert isinstance(metadata, SQLAlchemyMetaData)


def test_base_has_metadata():
    """Base 클래스가 메타데이터를 가지고 있는지 확인한다."""
    assert hasattr(Base, 'metadata')
    assert Base.metadata is metadata


def test_base_is_declarative():
    """Base 클래스가 DeclarativeBase를 상속하는지 확인한다."""
    assert issubclass(Base, DeclarativeBase)


def test_base_can_create_models():
    """Base를 상속하여 모델을 정의할 수 있는지 확인한다."""

    class TestModel(Base):
        """테스트 모델."""

        __tablename__ = "test_model"
        id = Column(Integer, primary_key=True)
        name = Column(String(100))

    assert TestModel.__tablename__ == "test_model"
    assert hasattr(TestModel, 'id')
    assert hasattr(TestModel, 'name')
    # 메타데이터에 테이블이 등록되었는지 확인
    assert "test_model" in metadata.tables


def test_metadata_shared_across_models():
    """여러 모델이 같은 메타데이터를 공유하는지 확인한다."""

    class Model1(Base):
        """첫 번째 테스트 모델."""

        __tablename__ = "model1"
        id = Column(Integer, primary_key=True)

    class Model2(Base):
        """두 번째 테스트 모델."""

        __tablename__ = "model2"
        id = Column(Integer, primary_key=True)

    # 둘 다 같은 메타데이터에 등록되어야 함
    assert Model1.metadata is Model2.metadata
    assert Model1.metadata is metadata
    assert "model1" in metadata.tables
    assert "model2" in metadata.tables
