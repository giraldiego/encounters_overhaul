import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable, List, Optional

FILE_PATTERN = "*.json"
DEFAULT_PROPERTY = "RespawnsOnRest"
INPUT_ROOT_NAME = "JSONs"
OUTPUT_ROOT_NAME = "processed"
NEEDFIX_ROOT_NAME = "needfix"


def iter_json_files(path: Path, recursive: bool) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if recursive:
        yield from path.rglob(FILE_PATTERN)
    else:
        yield from path.glob(FILE_PATTERN)


def pick_default_export(exports: List[dict], prefixes: List[str]) -> Optional[dict]:
    if not exports:
        return None

    if prefixes:
        for prefix in prefixes:
            for export in exports:
                name = export.get("ObjectName", "")
                if name.startswith(prefix):
                    return export

    for export in exports:
        name = export.get("ObjectName", "")
        if name.startswith("Default__"):
            return export

    return None


def export_has_property(export: dict, prop_name: str) -> bool:
    data = export.get("Data", [])
    for item in data:
        if item.get("Name") == prop_name:
            return True
    return False


def add_missing_property(export: dict, prop_name: str) -> bool:
    if export_has_property(export, prop_name):
        return False

    data = export.setdefault("Data", [])
    new_prop = {
        "$type": "UAssetAPI.PropertyTypes.Objects.BoolPropertyData, UAssetAPI",
        "Name": prop_name,
        "ArrayIndex": 0,
        "IsZero": False,
        "PropertyTagFlags": "None",
        "PropertyTagExtensions": "NoExtension",
        "Value": False,
    }

    preferred_markers = ["VO Idle Delay Max", "PossibleEncounters"]
    for marker in preferred_markers:
        for idx, item in enumerate(data):
            if item.get("Name") == marker:
                data.insert(idx + 1, new_prop)
                return True

    data.append(new_prop)
    return True


def build_output_path(file_path: Path, output_root_name: str) -> Path:
    parts = file_path.parts
    if INPUT_ROOT_NAME in parts:
        idx = parts.index(INPUT_ROOT_NAME)
        relative = Path(*parts[idx + 1 :])
        base = Path(*parts[:idx]) / output_root_name
        return base / relative
    return file_path.parent / output_root_name / file_path.name


def process_json_report(json_path: Path | str, apply_changes: bool = False) -> dict:
    file_path = Path(json_path)
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        return {
            "path": file_path,
            "status": "error",
            "error": str(exc),
        }

    exports = payload.get("Exports", [])
    default_export = pick_default_export(exports, [])
    if not default_export:
        return {
            "path": file_path,
            "status": "missing-default",
        }

    has_prop = export_has_property(default_export, DEFAULT_PROPERTY)
    needfix_path = None
    output_path = None
    added = False

    if not has_prop:
        needfix_path = build_output_path(file_path, NEEDFIX_ROOT_NAME)
        needfix_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, needfix_path)

        if apply_changes:
            added = add_missing_property(default_export, DEFAULT_PROPERTY)
            output_path = build_output_path(file_path, OUTPUT_ROOT_NAME)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=True, indent=2)
    return {
        "path": file_path,
        "needfix_path": needfix_path,
        "output_path": output_path,
        "status": "ok",
        "object_name": default_export.get("ObjectName", "<unknown>"),
        "has_property": has_prop,
        "added": added,
    }


def process_json(json_path: Path | str, apply_changes: bool = False) -> Path | None:
    result = process_json_report(json_path, apply_changes=apply_changes)
    if result["status"] != "ok":
        return None
    return result["output_path"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a given property exists on the Default__* export in UAssetAPI JSON files."
        )
    )
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories when path is a directory",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Add RespawnsOnRest and write to processed/ when missing.",
    )

    args = parser.parse_args()
    root = Path(args.path)

    if not root.exists():
        print(f"Path not found: {root}")
        return 2

    files = list(iter_json_files(root, args.recursive))
    if not files:
        print("No files matched.")
        return 0

    for file_path in sorted(files):
        result = process_json_report(file_path, apply_changes=args.apply)
        if result["status"] == "error":
            print(f"{file_path}: error reading JSON ({result['error']})")
            continue
        if result["status"] == "missing-default":
            print(f"{file_path}: Default__ export not found")
            continue

        status = "present" if result["has_property"] else "absent"
        changed = "added" if result["added"] else "already present"
        print(
            f"{file_path}: {status} ({result['object_name']}) [{changed}]"
        )
        if result["needfix_path"] is not None:
            print(f"Needfix: {result['needfix_path']}")
        if result["output_path"] is not None:
            print(f"Processed: {result['output_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
