"""검색 지표 훅 자리표시자 테스트."""
from modules.search.metrics import SearchMetricsEvent, SearchMetricsHook


class TestSearchMetricsHookRecordSearch:
    """SearchMetricsHook.record_search 테스트."""

    def test_starts_with_no_events(self):
        """생성 직후에는 기록된 이벤트가 없다."""
        hook = SearchMetricsHook()
        assert hook.events == []

    def test_records_a_search_event(self):
        """record_search를 호출하면 이벤트가 하나 기록된다."""
        hook = SearchMetricsHook()
        hook.record_search("wiki", 3)
        assert len(hook.events) == 1
        assert hook.events[0] == SearchMetricsEvent(term="wiki", result_count=3)

    def test_records_events_in_call_order(self):
        """여러 번 호출하면 호출한 순서대로 이벤트가 누적된다."""
        hook = SearchMetricsHook()
        hook.record_search("wiki", 3)
        hook.record_search("engine", 0)
        assert [event.term for event in hook.events] == ["wiki", "engine"]
        assert [event.result_count for event in hook.events] == [3, 0]

    def test_records_zero_result_count(self):
        """결과가 없는 검색도 result_count 0으로 기록된다."""
        hook = SearchMetricsHook()
        hook.record_search("존재하지않음", 0)
        assert hook.events[0].result_count == 0

    def test_each_hook_instance_has_independent_events(self):
        """서로 다른 훅 인스턴스는 이벤트 목록을 공유하지 않는다."""
        hook1 = SearchMetricsHook()
        hook2 = SearchMetricsHook()
        hook1.record_search("wiki", 1)
        assert hook1.events != []
        assert hook2.events == []
