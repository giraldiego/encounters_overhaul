import argparse
import copy
import json
from pathlib import Path

TARGET_DEFAULT = Path("input/Tower-DT_jRPG_Enemies.json")
SOURCE_DEFAULT = Path("../../output/enemies/Modded-DT_jRPG_Enemies.uasset.json")
OUTPUT_DEFAULT = Path("../../output/tower/Patched-Tower-DT_jRPG_Enemies.json")

STRUCT_TYPE = "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI"
ENEMY_STRUCT = "S_jRPG_Enemy"
SCALING_STRUCT = "S_EnemyScalingMultipliers"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy S_jRPG_Enemy Value arrays from a source enemy table into a target table "
            "using exact-name matches only."
        )
    )
    parser.add_argument("--target", type=Path, default=TARGET_DEFAULT, help=f"Target JSON file (default: {TARGET_DEFAULT})")
    parser.add_argument("--source", type=Path, default=SOURCE_DEFAULT, help=f"Source JSON file (default: {SOURCE_DEFAULT})")
    parser.add_argument("--out", type=Path, default=OUTPUT_DEFAULT, help=f"Output JSON file (default: {OUTPUT_DEFAULT})")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write changes directly into --target (ignores --out).",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_enemy_rows(data: dict):
    exports = data.get("Exports", [])
    for export in exports:
        table = export.get("Table")
        if not isinstance(table, dict):
            continue
        rows = table.get("Data", [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if (
                isinstance(row, dict)
                and row.get("$type") == STRUCT_TYPE
                and row.get("StructType") == ENEMY_STRUCT
            ):
                yield row

    # Fallback for simpler extracts with root-level Data.
    rows = data.get("Data", [])
    if isinstance(rows, list):
        for row in rows:
            if (
                isinstance(row, dict)
                and row.get("$type") == STRUCT_TYPE
                and row.get("StructType") == ENEMY_STRUCT
            ):
                yield row


def find_scaling_struct(enemy_row: dict) -> dict | None:
    for item in enemy_row.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type") == STRUCT_TYPE
            and item.get("StructType") == SCALING_STRUCT
            and isinstance(item.get("Value"), list)
        ):
            return item
    return None


def build_source_scaling_map(source_data: dict) -> dict[str, list]:
    value_map: dict[str, list] = {}
    for row in iter_enemy_rows(source_data):
        name = row.get("Name")
        scaling = find_scaling_struct(row)
        if isinstance(name, str) and scaling is not None:
            value_map[name] = scaling["Value"]
    return value_map


def main() -> int:
    args = parse_args()

    if not args.target.exists():
        print(f"ERROR: Target file not found: {args.target}")
        return 1
    if not args.source.exists():
        print(f"ERROR: Source file not found: {args.source}")
        return 1

    target_data = load_json(args.target)
    source_data = load_json(args.source)

    source_values = build_source_scaling_map(source_data)
    if not source_values:
        print("ERROR: No source enemy scaling rows found.")
        return 1

    stats = {
        "target_rows": 0,
        "replaced_exact": 0,
        "target_without_name": 0,
        "missing_scaling_in_target": 0,
        "missing_in_source": 0,
    }
    missing: list[str] = []
    missing_scaling_target: list[str] = []

    for row in iter_enemy_rows(target_data):
        stats["target_rows"] += 1

        target_name = row.get("Name")
        if not isinstance(target_name, str):
            stats["target_without_name"] += 1
            continue

        if target_name not in source_values:
            stats["missing_in_source"] += 1
            missing.append(target_name)
            continue

        target_scaling = find_scaling_struct(row)
        if target_scaling is None:
            stats["missing_scaling_in_target"] += 1
            missing_scaling_target.append(target_name)
            continue

        # Copy only the nested scaling payload modified by scale_enemies.py.
        target_scaling["Value"] = copy.deepcopy(source_values[target_name])
        stats["replaced_exact"] += 1

    output_path = args.target if args.in_place else args.out
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(target_data, f, indent=2)

    print("Done.")
    print(f"Target rows scanned: {stats['target_rows']}")
    print(f"Replaced nested scaling by exact name: {stats['replaced_exact']}")
    print(f"Target rows without a valid name: {stats['target_without_name']}")
    print(f"Target rows missing scaling struct: {stats['missing_scaling_in_target']}")
    print(f"Missing in source: {stats['missing_in_source']}")
    print(f"Written to: {output_path}")

    if missing:
        print("\nMissing names (first 50):")
        for name in sorted(set(missing))[:50]:
            print(f"- {name}")

    if missing_scaling_target:
        print("\nTarget rows missing scaling struct (first 50):")
        for name in sorted(set(missing_scaling_target))[:50]:
            print(f"- {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
