import json
import argparse
import copy
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HARD_DIR = SCRIPT_DIR / "reference" / "Hard_Difficulty"
EASY_DIR = SCRIPT_DIR / "reference" / "Easy_Difficulty"
NORMAL_DIR = SCRIPT_DIR / "reference" / "Normal_Difficulty"
OUTPUT_ROOT_DIR = SCRIPT_DIR.parent.parent / "output" / "difficulty"

TARGET_PREFIX_TO_STAT = {
    "HP_": "HP",
    "PhysicalAttack_": "ATK",
    "Speed_": "Speed",
    "Chroma_": "Chroma",
    "Experience_": "EXP",
}


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


def identify_target_stat(property_name: str) -> str | None:
    for prefix, stat in TARGET_PREFIX_TO_STAT.items():
        if property_name.startswith(prefix):
            return stat
    return None


def normalize_exports_round_up(exports: list[dict]) -> list[dict]:
    rounded_exports = copy.deepcopy(exports)

    for export in rounded_exports:
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

                if identify_target_stat(prop_name) is None:
                    continue

                value = prop.get("Value")
                if not isinstance(value, (int, float)):
                    continue

                prop["Value"] = int(math.ceil(value))

    return rounded_exports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy Hard difficulty Exports into Easy/Normal base files while preserving target metadata."
    )
    parser.add_argument(
        "--target",
        choices=["easy", "normal", "both"],
        default="easy",
        help="Which output target to generate. Default: easy",
    )
    return parser.parse_args()


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

    processed = 0
    skipped = 0

    print(f"\n=== Processing target: {target} ===")

    for hard_path in hard_files:
        target_name = name_mapper(hard_path.name)
        target_base_path = source_dir / target_name

        if not target_base_path.exists():
            print(f"SKIP: {target} counterpart not found for {hard_path.name} -> {target_name}")
            skipped += 1
            continue

        hard_data = load_json(hard_path)
        target_data = load_json(target_base_path)

        if "Exports" not in hard_data:
            print(f"SKIP: Missing 'Exports' in hard file: {hard_path.name}")
            skipped += 1
            continue

        target_data["Exports"] = normalize_exports_round_up(hard_data["Exports"])

        output_path = output_dir / target_name
        save_json(output_path, target_data)

        print(f"OK: {hard_path.name} -> {output_path.name}")
        processed += 1

    print(f"Target '{target}' summary: processed={processed}, skipped={skipped}")
    print(f"Output: {output_dir}")
    return processed, skipped


def main() -> None:
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
    print(f"Processed: {processed}")
    print(f"Skipped:   {skipped}")
    print(f"Output root: {OUTPUT_ROOT_DIR}")


if __name__ == "__main__":
    main()
