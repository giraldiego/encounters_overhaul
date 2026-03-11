import argparse
import copy
import json
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HARD_DIR = SCRIPT_DIR / "input" / "Hard_Difficulty"
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "output" / "difficulty" / "scaled_hard_from_level" / "Hard_Difficulty"

# Easy-to-edit settings.
# Only listed stats are scaled, and only for rows whose level is >= MIN_LEVEL.
MIN_LEVEL = 55
STAT_MULTIPLIERS = {
    "HP": 1.0,
}

SUPPORTED_STATS = {"HP", "ATK", "Speed", "Chroma", "EXP"}


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
        description="Scale selected stats in Hard difficulty files from a minimum level onward."
    )
    parser.add_argument(
        "--min-level",
        type=int,
        default=MIN_LEVEL,
        help=f"Minimum row level to scale. Default: {MIN_LEVEL}",
    )
    return parser.parse_args()


def validate_stat_multipliers() -> None:
    unknown_stats = set(STAT_MULTIPLIERS) - SUPPORTED_STATS
    if unknown_stats:
        raise ValueError(f"Unsupported stats in STAT_MULTIPLIERS: {sorted(unknown_stats)}")

    if not STAT_MULTIPLIERS:
        raise ValueError("STAT_MULTIPLIERS must contain at least one stat to scale")


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


def extract_row_level(row: dict) -> int | None:
    values = row.get("Value") if isinstance(row, dict) else None
    if not isinstance(values, list):
        return None

    for prop in values:
        if not isinstance(prop, dict):
            continue

        prop_name = prop.get("Name")
        if not isinstance(prop_name, str) or not prop_name.startswith("Level_"):
            continue

        value = prop.get("Value")
        if isinstance(value, (int, float)):
            return int(value)

    return None


def scaled_number(value: int | float, multiplier: float) -> int:
    return int(math.ceil(value * multiplier))


def scale_exports(
    exports: list[dict],
    stat_multipliers: dict[str, float],
    min_level: int,
) -> tuple[list[dict], dict[str, int], int]:
    scaled_exports = copy.deepcopy(exports)
    scaled_counts = {stat: 0 for stat in stat_multipliers}
    eligible_rows = 0

    for export in scaled_exports:
        table = export.get("Table")
        if not isinstance(table, dict):
            continue

        rows = table.get("Data")
        if not isinstance(rows, list):
            continue

        for row in rows:
            row_level = extract_row_level(row)
            if row_level is None or row_level < min_level:
                continue

            values = row.get("Value") if isinstance(row, dict) else None
            if not isinstance(values, list):
                continue

            eligible_rows += 1

            for prop in values:
                if not isinstance(prop, dict):
                    continue

                prop_name = prop.get("Name")
                if not isinstance(prop_name, str):
                    continue

                stat = identify_stat(prop_name)
                if stat not in stat_multipliers:
                    continue

                value = prop.get("Value")
                if not isinstance(value, (int, float)):
                    continue

                prop["Value"] = scaled_number(value, stat_multipliers[stat])
                scaled_counts[stat] += 1

    return scaled_exports, scaled_counts, eligible_rows


def process_files(min_level: int) -> tuple[int, int]:
    hard_files = sorted(HARD_DIR.glob("*.json"))
    if not hard_files:
        raise FileNotFoundError(f"No JSON files found in: {HARD_DIR}")

    processed = 0
    skipped = 0

    print("=== Processing Hard difficulty files ===")
    print(f"Minimum level: {min_level}")
    print(f"Stat multipliers: {STAT_MULTIPLIERS}")

    for source_path in hard_files:
        source_data = load_json(source_path)
        source_exports = source_data.get("Exports")

        if not isinstance(source_exports, list):
            print(f"SKIP: Missing or invalid 'Exports' in base file: {source_path.name}")
            skipped += 1
            continue

        scaled_exports, counts, eligible_rows = scale_exports(source_exports, STAT_MULTIPLIERS, min_level)
        output_data = copy.deepcopy(source_data)
        output_data["Exports"] = scaled_exports

        output_path = OUTPUT_DIR / source_path.name
        save_json(output_path, output_data)

        scaled_stats_summary = " ".join(f"{stat}={count}" for stat, count in counts.items())
        print(
            f"OK: {source_path.name} -> {output_path.name} | "
            f"eligible rows={eligible_rows} scaled {scaled_stats_summary}"
        )
        processed += 1

    return processed, skipped


def main() -> None:
    validate_stat_multipliers()
    args = parse_args()

    processed, skipped = process_files(args.min_level)

    print("\nDone")
    print(f"Processed:   {processed}")
    print(f"Skipped:     {skipped}")
    print(f"Output dir:  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()