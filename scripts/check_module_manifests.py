#!/usr/bin/env python3
"""모듈 계약 manifest 검증기.

``src/modules/<module>/manifest.json`` 이 ``src/modules/module_manifest.schema.json``
이 요구하는 필수 필드(schema_version, module, summary, port, service,
repository, fixtures)를 모두 채우고 있는지 검사한다. manifest 파일 자체가
없는 모듈(예: 아직 계약을 작성하지 않은 모듈)도 위반으로 잡는다.

이 스크립트는 태스크 0365 의 산출물이며, QA 파이프라인(scripts/qa.sh) 에는
태스크 0366 에서 연결되었다.

위반이 하나라도 있으면 위반 목록을 출력하고 종료 코드 1 로 끝낸다.
"""
import json
import sys
from pathlib import Path

import jsonschema

# 모듈 계약이 위치하는 루트 디렉토리
MODULES_ROOT = Path("src/modules")
# 모든 모듈 manifest 가 따라야 하는 JSON Schema 파일 위치
SCHEMA_PATH = MODULES_ROOT / "module_manifest.schema.json"


def module_dirs() -> list[Path]:
    """검사 대상 모듈 디렉토리 목록을 반환한다.

    ``__pycache__`` 같은 비모듈 디렉토리는 제외한다.

    Returns:
        모듈 디렉토리 경로 목록 (이름순 정렬)
    """
    return sorted(
        path
        for path in MODULES_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    )


def check_module(module_dir: Path, schema: dict) -> list[str]:
    """단일 모듈의 manifest 를 검사한다.

    Args:
        module_dir: 검사할 모듈 디렉토리
        schema: manifest 가 만족해야 하는 JSON Schema

    Returns:
        위반 메시지 목록 (위반이 없으면 빈 리스트)
    """
    manifest_path = module_dir / "manifest.json"
    if not manifest_path.is_file():
        return [f"{module_dir.name}: manifest.json 파일이 없습니다 ({manifest_path})"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"{module_dir.name}: manifest.json 이 유효한 JSON 이 아닙니다 ({error})"]

    try:
        jsonschema.validate(instance=manifest, schema=schema)
    except jsonschema.ValidationError as error:
        return [f"{module_dir.name}: manifest.json 이 스키마를 만족하지 않습니다 ({error.message})"]

    return []


def main() -> int:
    """모든 모듈의 manifest 를 검사하고 위반 여부에 따라 종료 코드를 반환한다.

    Returns:
        위반이 없으면 0, 있으면 1
    """
    if not SCHEMA_PATH.is_file():
        print(f"manifest 스키마 파일이 없습니다: {SCHEMA_PATH}", file=sys.stderr)
        return 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    all_violations: list[str] = []
    for module_dir in module_dirs():
        all_violations.extend(check_module(module_dir, schema))

    if all_violations:
        print("❌ 모듈 계약 manifest 검증 실패:", file=sys.stderr)
        for message in all_violations:
            print(f"  - {message}", file=sys.stderr)
        print(
            "\n각 모듈은 src/modules/<module>/manifest.json 에 "
            "schema_version, module, summary, port, service, repository, "
            "fixtures 를 채운 계약 manifest 를 두어야 합니다.\n"
            "자세한 규칙은 docs/module-contract-manifest-schema.md 를 참고하세요.",
            file=sys.stderr,
        )
        return 1

    print("✅ 모듈 계약 manifest 검증 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
