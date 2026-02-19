from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

UASSET_SOURCE_ROOT = Path(
    r"H:\Gaming\Modding\Exp33\Game\Sandfall\Content\Characters"
)
DEST_DIR = Path(
    r"H:\Gaming\Modding\Exp33\Retoc\Building\Z_NoRespawn_P\Sandfall\Content\Characters"
)
JSON_ROOT_NAME = "processed"


def compact_path(value: str) -> str:
    return (
        value.replace("/", "")
        .replace("\\", "")
        .replace(":", "")
        .replace(".", "")
        .casefold()
    )


def iter_dirs(base: Path) -> Iterable[Path]:
    for path in base.rglob("*"):
        if path.is_dir():
            yield path


def recover_mangled_dir(raw: str, base: Path) -> Path | None:
    compact_raw = compact_path(raw)
    if not compact_raw:
        return None

    matches: list[Path] = []
    for candidate in iter_dirs(base):
        rel = candidate.relative_to(base)
        if compact_path(str(rel)) == compact_raw:
            matches.append(candidate)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        print("Multiple matching directories found:")
        for match in matches:
            print(f"  {match}")
    return None


def build_uasset_source_dir(json_dir: Path) -> Path:
    parts = json_dir.parts
    if JSON_ROOT_NAME in parts:
        idx = parts.index(JSON_ROOT_NAME)
        relative = Path(*parts[idx + 1 :])
        return UASSET_SOURCE_ROOT / relative
    return UASSET_SOURCE_ROOT / json_dir.name


def build_dest_base_dir(json_dir: Path) -> Path:
    parts = json_dir.parts
    if JSON_ROOT_NAME in parts:
        idx = parts.index(JSON_ROOT_NAME)
        relative = Path(*parts[idx + 1 :])
        return DEST_DIR / relative
    return DEST_DIR / json_dir.name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy matching .uasset files based on JSON file names."
    )
    parser.add_argument("json_dir", help="Directory containing JSON files")
    args = parser.parse_args()

    json_dir = Path(args.json_dir)
    if not json_dir.is_dir():
        recovered = None
        if "/" not in args.json_dir and "\\" not in args.json_dir:
            recovered = recover_mangled_dir(args.json_dir, Path.cwd())
        if recovered is None:
            print(f"JSON dir not found: {json_dir}")
            print(
                "Hint: In bash, wrap Windows paths in single quotes to keep backslashes."
            )
            return 2
        json_dir = recovered

    uasset_source_dir = build_uasset_source_dir(json_dir)
    if not uasset_source_dir.is_dir():
        print(f"Uasset source dir not found: {uasset_source_dir}")
        return 2

    dest_base_dir = build_dest_base_dir(json_dir)

    json_files = sorted(json_dir.rglob("*.json"))
    if not json_files:
        print("No JSON files found.")
        return 0

    dest_base_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    missing = 0

    for json_path in json_files:
        uasset_name = f"{json_path.stem}.uasset"
        rel_dir = json_path.parent.relative_to(json_dir)
        source_path = uasset_source_dir / rel_dir / uasset_name
        if not source_path.is_file():
            print(f"Missing uasset: {source_path}")
            missing += 1
            continue

        dest_path = dest_base_dir / rel_dir / uasset_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        copied += 1
        print(f"Copied: {source_path} -> {dest_path}")

    print(f"Done. Copied: {copied}, Missing: {missing}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
