import argparse
import json
import re
from pathlib import Path

DEFAULT_INPUT = Path("input/Tower-DT_jRPG_Enemies.json")
ENEMY_STRUCT = "S_jRPG_Enemy"
SUFFIX_RE = re.compile(r"^(.*?)(\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find duplicate enemy names represented as numeric-suffix variants "
            "(for example: SM_Lancelier + SM_Lancelier2)."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to DT_jRPG_Enemies JSON file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--include-orphans",
        action="store_true",
        help=(
            "Also include groups where only suffixed names exist "
            "(for example: Name2 + Name3 without Name)."
        ),
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_enemy_names(data: dict) -> list[str]:
    names: list[str] = []

    exports = data.get("Exports", [])
    for export in exports:
        table = export.get("Table")
        if not isinstance(table, dict):
            continue

        rows = table.get("Data", [])
        for row in rows:
            if not (
                isinstance(row, dict)
                and row.get("$type") == "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI"
                and row.get("StructType") == ENEMY_STRUCT
            ):
                continue

            row_name = row.get("Name")
            if isinstance(row_name, str) and row_name:
                names.append(row_name)

    # Fallback for simpler extracts with root-level Data.
    if not names:
        rows = data.get("Data", [])
        for row in rows:
            if not (
                isinstance(row, dict)
                and row.get("$type") == "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI"
                and row.get("StructType") == ENEMY_STRUCT
            ):
                continue
            row_name = row.get("Name")
            if isinstance(row_name, str) and row_name:
                names.append(row_name)

    return names


def split_numeric_suffix(name: str) -> tuple[str, str | None]:
    match = SUFFIX_RE.match(name)
    if not match:
        return name, None
    return match.group(1), match.group(2)


def find_duplicate_groups(names: list[str], include_orphans: bool) -> dict[str, list[str]]:
    unique_names = sorted(set(names))
    all_names = set(unique_names)

    groups: dict[str, list[str]] = {}

    for name in unique_names:
        base, suffix = split_numeric_suffix(name)
        if suffix is None:
            continue

        if not include_orphans and base not in all_names:
            continue

        groups.setdefault(base, [])
        groups[base].append(name)

    for base in list(groups.keys()):
        variants = [base] + groups[base] if base in all_names else groups[base]
        groups[base] = sorted(set(variants), key=natural_sort_key)

    # Keep only true groups with at least 2 variants.
    groups = {base: variants for base, variants in groups.items() if len(variants) >= 2}
    return dict(sorted(groups.items(), key=lambda kv: natural_sort_key(kv[0])))


def natural_sort_key(text: str) -> list[object]:
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"(\d+)", text)]


def main() -> int:
    args = parse_args()

    if not args.file.exists():
        print(f"ERROR: File not found: {args.file}")
        return 1

    data = load_json(args.file)
    enemy_names = extract_enemy_names(data)

    if not enemy_names:
        print("No enemy rows found (StructType S_jRPG_Enemy).")
        return 1

    groups = find_duplicate_groups(enemy_names, include_orphans=args.include_orphans)

    print(f"Enemy rows scanned: {len(enemy_names)}")
    print(f"Unique enemy names: {len(set(enemy_names))}")
    print(f"Duplicate groups found: {len(groups)}")

    if not groups:
        return 0

    print("\nDuplicate groups:")
    for base, variants in groups.items():
        print(f"- {base}: {', '.join(variants)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
