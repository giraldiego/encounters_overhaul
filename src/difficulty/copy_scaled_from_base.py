import argparse
import copy
import json
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EASY_DIR = SCRIPT_DIR / "input" / "Easy_Difficulty"
NORMAL_DIR = SCRIPT_DIR / "input" / "Normal_Difficulty"
OUTPUT_ROOT_DIR = SCRIPT_DIR.parent.parent / "output" / "difficulty" / "scaled_from_base"

# Easy-to-edit scaling multipliers applied to each target's own base values.
# Keys must be: HP, ATK, Speed, Chroma, EXP
MULTIPLIERS = {
    "normal": {"HP": 1, "ATK": 1, "Speed": 1, "Chroma": 0.25, "EXP": 0.25},
    "easy": {"HP": 1, "ATK": 1, "Speed": 1, "Chroma": 0.1, "EXP": 0.1},
}

REQUIRED_MULTIPLIER_KEYS = {"HP", "ATK", "Speed", "Chroma", "EXP"}


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
        description="Scale each difficulty file from its own base values and write to scaled_from_base output."
    )
    parser.add_argument(
        "--target",
        choices=["easy", "normal", "both"],
        default="both",
        help="Which target difficulty to process. Default: both",
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


def process_target(target: str) -> tuple[int, int]:
    if target == "easy":
        source_dir = EASY_DIR
        output_dir = OUTPUT_ROOT_DIR / "Easy_Difficulty"
    elif target == "normal":
        source_dir = NORMAL_DIR
        output_dir = OUTPUT_ROOT_DIR / "Normal_Difficulty"
    else:
        raise ValueError(f"Unsupported target: {target}")

    multipliers = MULTIPLIERS[target]
    target_files = sorted(source_dir.glob("*.json"))

    if not target_files:
        raise FileNotFoundError(f"No JSON files found for target '{target}' in: {source_dir}")

    processed = 0
    skipped = 0

    print(f"\n=== Processing target: {target} ===")
    print(f"Multipliers: {multipliers}")

    for source_path in target_files:
        source_data = load_json(source_path)
        source_exports = source_data.get("Exports")

        if not isinstance(source_exports, list):
            print(f"SKIP: Missing or invalid 'Exports' in base file: {source_path.name}")
            skipped += 1
            continue

        scaled_exports, counts = scale_exports(source_exports, multipliers)
        output_data = copy.deepcopy(source_data)
        output_data["Exports"] = scaled_exports

        output_path = output_dir / source_path.name
        save_json(output_path, output_data)

        print(
            f"OK: {source_path.name} -> {output_path.name} | "
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

    targets = ["easy", "normal"] if args.target == "both" else [args.target]

    processed = 0
    skipped = 0

    for target in targets:
        p, s = process_target(target)
        processed += p
        skipped += s

    print("\nDone")
    print(f"Processed:   {processed}")
    print(f"Skipped:     {skipped}")
    print(f"Output root: {OUTPUT_ROOT_DIR}")


if __name__ == "__main__":
    main()
