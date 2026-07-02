"""`scripts/qa.sh` 가 모듈 계약 manifest 검증을 실행하는지 확인한다.

태스크 0366 의 산출물이다. manifest 검증 스크립트(`check_module_manifests.py`)
자체의 동작은 `tests/test_check_module_manifests.py` 가 검증하므로, 여기서는
QA 파이프라인에 해당 검증이 연결되어 있는지만 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"
BOUNDARY_SCRIPT_PATH = REPO_ROOT / "scripts" / "check_boundaries.py"
MANIFEST_SCRIPT_PATH = REPO_ROOT / "scripts" / "check_module_manifests.py"


def test_qa_runs_manifest_validation():
    """qa.sh 는 check_module_manifests.py 를 호출해야 한다."""
    qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "scripts/check_module_manifests.py" in qa_contents


def test_qa_runs_manifest_validation_alongside_boundary_check():
    """manifest 검증은 기존 boundary 검사와 함께(같은 스크립트 안에서) 실행되어야 한다."""
    qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    boundary_index = qa_contents.index("scripts/check_boundaries.py")
    manifest_index = qa_contents.index("scripts/check_module_manifests.py")
    test_index = qa_contents.index("scripts/test.sh")
    assert boundary_index < manifest_index < test_index
