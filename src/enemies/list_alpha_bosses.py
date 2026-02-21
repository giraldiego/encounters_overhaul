import argparse
import json
from pathlib import Path

INFILE = Path("input/DT_jRPG_Enemies.uasset.json")

BOOL_TYPE = "UAssetAPI.PropertyTypes.Objects.BoolPropertyData, UAssetAPI"
STRUCT_TYPE = "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI"
ENEMY_STRUCT = "S_jRPG_Enemy"

BOSS_NAME_PATTERNS = [
    "MIME",
]

ALPHA_NAME_PATTERNS = [
    "ALPHA",
    "_Alpha",
]


def extract_enemy_hardcoded_name(enemy_struct: dict) -> str:
    for item in enemy_struct.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type")
            == "UAssetAPI.PropertyTypes.Objects.NamePropertyData, UAssetAPI"
            and item.get("Name") == "EnemyHardcodedName_4_0FAACC934CB2957BA37E888624E5835F"
        ):
            v = item.get("Value")
            if isinstance(v, str) and v:
                return v
    v = enemy_struct.get("Name")
    return v if isinstance(v, str) and v else "<unknown_enemy>"


def extract_is_boss(enemy_struct: dict) -> bool:
    for item in enemy_struct.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type") == BOOL_TYPE
            and item.get("Name", "").startswith("IsBoss_")
        ):
            v = item.get("Value", False)
            return bool(v) if isinstance(v, bool) else False
    return False


def matches_pattern(name: str, patterns: list[str]) -> bool:
    if not name:
        return False
    name_upper = name.upper()
    return any(pattern.upper() in name_upper for pattern in patterns if pattern)


def extract_enemy_entries(data: dict) -> list[dict]:
    exports = data.get("Exports", [])
    for export in exports:
        table = export.get("Table")
        if isinstance(table, dict):
            data_list = table.get("Data", [])
            if isinstance(data_list, list) and data_list:
                return data_list

    fallback = data.get("Data", [])
    return fallback if isinstance(fallback, list) else []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List alpha enemies and classify which are bosses vs non-bosses."
    )
    parser.add_argument(
        "--input",
        default=str(INFILE),
        help="Path to DT_jRPG_Enemies.uasset.json",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    alpha_bosses: list[str] = []
    alpha_non_bosses: list[str] = []

    for entry in extract_enemy_entries(data):
        if not (
            isinstance(entry, dict)
            and entry.get("$type") == STRUCT_TYPE
            and entry.get("StructType") == ENEMY_STRUCT
        ):
            continue

        enemy_name = extract_enemy_hardcoded_name(entry)
        if not matches_pattern(enemy_name, ALPHA_NAME_PATTERNS):
            continue

        is_boss = extract_is_boss(entry) or matches_pattern(enemy_name, BOSS_NAME_PATTERNS)
        if is_boss:
            alpha_bosses.append(enemy_name)
        else:
            alpha_non_bosses.append(enemy_name)

    alpha_bosses = sorted(set(alpha_bosses))
    alpha_non_bosses = sorted(set(alpha_non_bosses))

    print("ALPHA BOSSES")
    print("------------")
    for name in alpha_bosses:
        print(name)

    print("\nALPHA NON-BOSSES")
    print("----------------")
    for name in alpha_non_bosses:
        print(name)

    print("\nSUMMARY")
    print("-------")
    print(f"Alpha bosses: {len(alpha_bosses)}")
    print(f"Alpha non-bosses: {len(alpha_non_bosses)}")
    print(f"Alpha total: {len(alpha_bosses) + len(alpha_non_bosses)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
