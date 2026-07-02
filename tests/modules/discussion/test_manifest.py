"""discussion 모듈 계약 manifest(`src/modules/discussion/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지,
그리고 manifest 가 가리키는 서비스/저장소 계약(thread/comment/state)이 실제
구현과 어긋나지 않는지 확인한다. 태스크 0360 의 산출물이다.
"""
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

from modules.discussion.comment import DiscussionComment
from modules.discussion.repository import DiscussionRepository
from modules.discussion.service import DiscussionService
from modules.discussion.state import ThreadState
from modules.discussion.thread import DiscussionThread

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "discussion" / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestDiscussionManifest:
    """discussion manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

    def test_manifest_exists(self):
        """manifest 파일이 모듈 디렉터리 아래에 존재한다."""
        assert MANIFEST_PATH.is_file()

    def test_manifest_is_valid_json(self):
        """manifest 가 유효한 JSON 이다."""
        _load_manifest()

    def test_manifest_conforms_to_schema(self):
        """manifest 가 module_manifest.schema.json 을 만족한다."""
        manifest = _load_manifest()
        schema = _load_schema()
        jsonschema.validate(instance=manifest, schema=schema)

    def test_manifest_module_name_matches_directory(self):
        """module 필드가 src/modules/discussion 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "discussion"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/discussion"

    def test_manifest_port_status_not_ready_yet(self):
        """계약만 고정된 단계이므로 status 는 ready 가 아니다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] in {"not_started", "in_progress"}


class TestDiscussionManifestMatchesImplementation:
    """manifest 가 선언한 계약이 실제 구현과 어긋나지 않는지 확인한다."""

    def test_service_path_is_importable(self):
        """service.path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_public_methods_exist_on_service(self):
        """manifest 에 선언된 공개 메서드가 DiscussionService 에 실제로 존재한다."""
        manifest = _load_manifest()
        for method_name in manifest["service"]["public_methods"]:
            assert hasattr(DiscussionService, method_name), (
                f"DiscussionService 에 {method_name} 메서드가 없습니다"
            )

    def test_no_undeclared_public_methods(self):
        """DiscussionService 의 공개 메서드가 manifest 에 모두 선언되어 있다."""
        manifest = _load_manifest()
        declared = set(manifest["service"]["public_methods"])
        actual = {
            name
            for name, _ in inspect.getmembers(DiscussionService, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        assert actual == declared

    def test_repository_path_is_importable(self):
        """repository.port_path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_repository_interface_matches_abstract_base(self):
        """repository.interface 가 DiscussionRepository ABC 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["repository"]["interface"] == DiscussionRepository.__name__


class TestDiscussionManifestThreadStateContract:
    """thread 상태 계약(status 는 무조건 전이, ThreadState 는 미결선)이
    manifest 의 서술과 실제 동작에서 일치하는지 확인한다."""

    def test_contract_notes_describe_thread_state(self):
        """contract_notes 가 thread 상태 계약을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "ThreadState" in notes
        assert "is_open()" in notes

    def test_thread_state_enum_not_wired_into_status(self):
        """ThreadState 값과 DiscussionThread.status 문자열이 일치하지만
        검증에는 사용되지 않는다."""
        assert {state.value for state in ThreadState} == {"open", "closed", "paused"}
        thread = DiscussionThread(
            id="t1",
            document_id="d1",
            title="title",
            created_by="u1",
            created_at=datetime.now(timezone.utc),
            status="not-a-real-state",
        )
        assert thread.status == "not-a-real-state"

    def test_transitions_are_unconditional(self):
        """close/reopen/pause 는 현재 상태와 무관하게 항상 성공한다."""
        now = datetime.now(timezone.utc)
        thread = DiscussionThread(
            id="t1",
            document_id="d1",
            title="title",
            created_by="u1",
            created_at=now,
        )
        thread.close(now)
        thread.pause(now)
        assert thread.status == "paused"
        assert thread.closed_at is not None
        assert thread.paused_at is not None


class TestDiscussionManifestCommentContract:
    """댓글 숨김/뷰 계약이 manifest 의 서술과 실제 동작에서 일치하는지 확인한다."""

    def test_contract_notes_describe_comment_hide_and_views(self):
        """contract_notes 가 hide()/to_public_view()/to_moderator_view() 계약을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "hide(" in notes
        assert "to_public_view" in notes
        assert "to_moderator_view" in notes

    def test_hidden_comment_masks_body_only_in_public_view(self):
        """숨김 처리된 댓글은 public view 에서만 body 가 가려진다."""
        now = datetime.now(timezone.utc)
        comment = DiscussionComment(
            id="c1",
            thread_id="t1",
            body="hello",
            created_by="u1",
            created_at=now,
        )
        comment.hide(now)
        assert comment.to_public_view()["body"] is None
        assert comment.to_moderator_view()["body"] == "hello"
