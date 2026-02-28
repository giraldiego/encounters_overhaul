import argparse
import copy
import json
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HARD_DIR = SCRIPT_DIR / "reference" / "Hard_Difficulty"
EASY_DIR = SCRIPT_DIR / "reference" / "Easy_Difficulty"
NORMAL_DIR = SCRIPT_DIR / "reference" / "Normal_Difficulty"
OUTPUT_ROOT_DIR = SCRIPT_DIR.parent.parent / "output" / "difficulty" / "scaled_from_hard"

# Easy-to-edit scaling multipliers applied to Hard values before copying Exports.
# Keys must be: HP, ATK, Speed, Chroma, EXP
MULTIPLIERS = {
    "normal": {"HP": 1, "ATK": 1, "Speed": 1, "Chroma": 1, "EXP": 1},
    "easy": {"HP": 1, "ATK": 1, "Speed": 1, "Chroma": 1, "EXP": 1},
}

REQUIRED_MULTIPLIER_KEYS = {"HP", "ATK", "Speed", "Chroma", "EXP"}


def hard_to_easy_name(hard_name: str) -> str:
    if hard_name.endswith("_Hard.json"):
        return hard_name.replace("_Hard.json", "_Easy.json")
    return hard_name.replace("Hard", "Easy")


def hard_to_normal_name(hard_name: str) -> str:
    if hard_name.endswith("_Hard.json"):
        return hard_name.replace("_Hard.json", ".json")
    return hard_name.replace("_Hard", "")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scale Hard Exports values, then copy into Easy/Normal base files while preserving target metadata."
    )
    parser.add_argument(
        "--target",
        choices=["easy", "normal", "both"],
        default="easy",
        help="Which output target to generate. Default: easy",
    )
    return parser.parse_args()


def validate_multipliers() -> None:
    for mode, values in MULTIPLIERS.items():
        missing = REQUIRED_MULTIPLIER_KEYS - set(values.keys())
        if missing:
            raise ValueError(f"MULTIPLIERS['{mode}'] is missing keys: {sorted(missing)}")


def identify_stat(property_name: str) -> str | None:
    if property_name.startswith("HP_"):
        return "HP"
    if property_name.startswith("PhysicalAttack_"):
        return "ATK"
    if property_name.startswith("Speed_"):
        return "Speed"
    if property_name.startswith("Chroma_"):
        return "Chroma"
    if property_name.startswith("Experience_"):
        return "EXP"
    return None


def scaled_number(value: int | float, multiplier: float) -> int:
    new_value = value * multiplier
    return int(math.ceil(new_value))


def scale_exports(exports: list[dict], multipliers: dict[str, float]) -> tuple[list[dict], dict[str, int]]:
    scaled_exports = copy.deepcopy(exports)
    scaled_counts = {key: 0 for key in REQUIRED_MULTIPLIER_KEYS}

    for export in scaled_exports:
        table = export.get("Table")
        if not isinstance(table, dict):
            continue

        rows = table.get("Data")
        if not isinstance(rows, list):
            continue

        for row in rows:
            values = row.get("Value") if isinstance(row, dict) else None
            if not isinstance(values, list):
                continue

            for prop in values:
                if not isinstance(prop, dict):
                    continue

                prop_name = prop.get("Name")
                if not isinstance(prop_name, str):
                    continue

                stat = identify_stat(prop_name)
                if stat is None:
                    continue

                value = prop.get("Value")
                if not isinstance(value, (int, float)):
                    continue

                prop["Value"] = scaled_number(value, multipliers[stat])
                scaled_counts[stat] += 1

    return scaled_exports, scaled_counts


def process_target(target: str, hard_files: list[Path]) -> tuple[int, int]:
    if target == "easy":
        source_dir = EASY_DIR
        output_dir = OUTPUT_ROOT_DIR / "Easy_Difficulty"
        name_mapper = hard_to_easy_name
    elif target == "normal":
        source_dir = NORMAL_DIR
        output_dir = OUTPUT_ROOT_DIR / "Normal_Difficulty"
        name_mapper = hard_to_normal_name
    else:
        raise ValueError(f"Unsupported target: {target}")

    multipliers = MULTIPLIERS[target]

    processed = 0
    skipped = 0

    print(f"\n=== Processing target: {target} ===")
    print(f"Multipliers: {multipliers}")

    for hard_path in hard_files:
        target_name = name_mapper(hard_path.name)
        target_base_path = source_dir / target_name

        if not target_base_path.exists():
            print(f"SKIP: {target} counterpart not found for {hard_path.name} -> {target_name}")
            skipped += 1
            continue

        hard_data = load_json(hard_path)
        target_data = load_json(target_base_path)

        hard_exports = hard_data.get("Exports")
        if not isinstance(hard_exports, list):
            print(f"SKIP: Missing or invalid 'Exports' in hard file: {hard_path.name}")
            skipped += 1
            continue

        scaled_exports, counts = scale_exports(hard_exports, multipliers)
        target_data["Exports"] = scaled_exports

        output_path = output_dir / target_name
        save_json(output_path, target_data)

        print(
            f"OK: {hard_path.name} -> {output_path.name} | "
            f"scaled HP={counts['HP']} ATK={counts['ATK']} Speed={counts['Speed']} "
            f"Chroma={counts['Chroma']} EXP={counts['EXP']}"
        )
        processed += 1

    print(f"Target '{target}' summary: processed={processed}, skipped={skipped}")
    print(f"Output: {output_dir}")
    return processed, skipped


def main() -> None:
    validate_multipliers()
    args = parse_args()

    hard_files = sorted(HARD_DIR.glob("*.json"))
    if not hard_files:
        raise FileNotFoundError(f"No JSON files found in: {HARD_DIR}")

    targets = ["easy", "normal"] if args.target == "both" else [args.target]

    processed = 0
    skipped = 0

    for target in targets:
        p, s = process_target(target, hard_files)
        processed += p
        skipped += s

    print("\nDone")
    print(f"Processed:   {processed}")
    print(f"Skipped:     {skipped}")
    print(f"Output root: {OUTPUT_ROOT_DIR}")


if __name__ == "__main__":
    main()
