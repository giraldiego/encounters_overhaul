import argparse
import json
from pathlib import Path
from typing import Iterable

FILE_PATTERN = "*.json"
DEFAULT_PROPERTY = "RespawnsOnRest"


def iter_json_files(path: Path, recursive: bool) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if recursive:
        yield from path.rglob(FILE_PATTERN)
    else:
        yield from path.glob(FILE_PATTERN)


def pick_default_export(exports: list[dict]) -> dict | None:
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


def file_has_property(file_path: Path, prop_name: str) -> bool:
    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    exports = payload.get("Exports", [])
    default_export = pick_default_export(exports)
    if not default_export:
        return False

    return export_has_property(default_export, prop_name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List JSON files where Default__* already has RespawnsOnRest property."
        )
    )
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories when path is a directory",
    )
    parser.add_argument(
        "--property",
        default=DEFAULT_PROPERTY,
        help="Property name to check (default: RespawnsOnRest)",
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

    matches = 0
    for file_path in sorted(files):
        try:
            if file_has_property(file_path, args.property):
                print(file_path)
                matches += 1
        except Exception as exc:
            print(f"{file_path}: error reading JSON ({exc})")

    if matches == 0:
        print("No files already have the property.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
