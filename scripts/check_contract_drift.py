#!/usr/bin/env python3
"""Python/PHP 계약 drift 리포트 (placeholder).

``docs/contract-drift-report.md`` 가 고정한 형식대로, 모듈별 manifest
상태와 ``php/`` 트리 존재 여부를 표로 출력한다. ``php/`` 트리가 아직
없는 동안(Phase A/B, 0351-0440)은 실제 drift(계약 불일치) 비교 로직을
구현하지 않고, 모든 모듈을 "not_measurable" 로 보고한다.

이 스크립트는 판정(pass/fail) 게이트가 아니라 정보성 리포트이므로,
``php/`` 트리가 없어도 실패하지 않고 항상 종료 코드 0 을 반환한다.
"""
import json
import sys
from pathlib import Path

# 모듈 계약이 위치하는 루트 디렉토리
MODULES_ROOT = Path("src/modules")
# 이후 태스크(0394 이후)가 채울 PHP 구현 루트. 이 스크립트 작성 시점에는
# 존재하지 않는 것이 Phase A/B 의 정상 상태다.
PHP_ROOT = Path("php")

NOT_MEASURABLE = "not_measurable"


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


def build_report(php_root: Path = PHP_ROOT) -> list[dict]:
    """모듈별 drift 리포트 행을 만든다.

    ``php_root`` 가 없으면 모든 모듈의 drift 판정을 ``not_measurable``
    로 고정한다 — 비교할 PHP 구현 자체가 없기 때문이다.

    Args:
        php_root: PHP 구현 트리 루트. 테스트에서 임시 경로로 대체할 수
            있도록 인자로 받는다.

    Returns:
        ``module``/``manifest_status``/``php_tree_present``/``drift``
        키를 가진 딕셔너리 목록 (모듈 이름순).
    """
    php_tree_present = php_root.is_dir()
    rows = []
    for module_dir in module_dirs():
        manifest_path = module_dir / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_status = manifest.get("port", {}).get("status", "unknown")
        else:
            manifest_status = "unknown"
        rows.append(
            {
                "module": module_dir.name,
                "manifest_status": manifest_status,
                "php_tree_present": php_tree_present,
                # php/ 트리가 없는 동안은 비교 근거가 없으므로 항상
                # not_measurable 이다. php/ 트리가 생긴 뒤의 실제 비교
                # 로직은 이 태스크의 범위 밖이다.
                "drift": NOT_MEASURABLE,
            }
        )
    return rows


def format_report(rows: list[dict]) -> str:
    """리포트 행을 사람이 읽을 수 있는 표 문자열로 만든다."""
    header = f"{'module':<12} {'manifest_status':<15} {'php_tree_present':<18} drift"
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['module']:<12} {row['manifest_status']:<15} "
            f"{str(row['php_tree_present']):<18} {row['drift']}"
        )
    return "\n".join(lines)


def main() -> int:
    rows = build_report()
    print(format_report(rows))
    if not PHP_ROOT.is_dir():
        print(
            f"\nnote: '{PHP_ROOT}' 트리가 없어 drift 를 측정할 수 없습니다 "
            "(Phase A/B 의 정상 상태). docs/contract-drift-report.md 참고.",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
