"""검색 지표 훅 자리표시자."""
from dataclasses import dataclass
from typing import List


@dataclass
class SearchMetricsEvent:
    """검색 지표 훅에 기록되는 단일 검색 이벤트."""

    term: str
    result_count: int


class SearchMetricsHook:
    """
    검색 작업에 대한 지표를 기록하는 훅 자리표시자.

    현재는 실제 관측(observability) 백엔드(Prometheus, StatsD 등)로 지표를
    전송하지 않고, `record_search` 호출을 메모리 리스트에 순서대로 누적하기만
    하는 자리표시자다. `SearchService`나 router로의 실제 연결과 실질적인
    지표 백엔드 연동은 이후 태스크에서 채워진다.
    """

    def __init__(self):
        self.events: List[SearchMetricsEvent] = []

    def record_search(self, term: str, result_count: int) -> None:
        """
        검색 작업 완료 시 호출되는 지표 기록 훅.

        Args:
            term: 검색에 사용된 질의어
            result_count: 검색 결과 개수
        """
        self.events.append(SearchMetricsEvent(term=term, result_count=result_count))
