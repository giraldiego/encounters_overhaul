import argparse
import csv
import json
from pathlib import Path


def parse_ranges_file(ranges_path: Path) -> list[tuple[int, int | None, float]]:
    with ranges_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError("Ranges file must be a JSON array of objects")

    explicit_ranges: list[tuple[int, int, float]] = []
    starts: list[tuple[int, float]] = []
    for idx, entry in enumerate(payload, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Range entry {idx} must be an object")

        multiplier = entry.get("multiplier")
        if not isinstance(multiplier, (int, float)):
            raise ValueError(f"Range entry {idx} must include numeric multiplier")

        if "min" in entry or "max" in entry:
            start = entry.get("min")
            end = entry.get("max")
            if not isinstance(start, int) or not isinstance(end, int):
                raise ValueError(f"Range entry {idx} must include integer min/max")
            if start > end:
                raise ValueError(f"Range entry {idx} has min greater than max")
            explicit_ranges.append((start, end, float(multiplier)))
            continue

        start = entry.get("start", entry.get("level"))
        if not isinstance(start, int):
            raise ValueError(f"Range entry {idx} must include integer start (or level)")
        starts.append((start, float(multiplier)))

    if explicit_ranges and starts:
        raise ValueError("Do not mix min/max ranges with start-only entries")

    if explicit_ranges:
        return explicit_ranges

    if not starts:
        raise ValueError("Ranges file must include at least one entry")

    starts.sort(key=lambda item: item[0])
    ranges: list[tuple[int, int | None, float]] = []
    for idx, (start, multiplier) in enumerate(starts):
        end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else None
        ranges.append((start, end, multiplier))

    return ranges


def load_level_adjustments(csv_path: Path) -> list[tuple[int, float]]:
    rows: list[tuple[int, float]] = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            level_raw = (row.get("Level") or "").strip()
            multiplier_raw = (row.get("multiplier") or "").strip()
            if not level_raw or not multiplier_raw:
                continue
            rows.append((int(level_raw), float(multiplier_raw)))
    rows.sort(key=lambda item: item[0])
    return rows


def build_ranges(levels: list[tuple[int, float]]) -> list[dict[str, float]]:
    ranges: list[dict[str, float]] = []
    last_multiplier: float | None = None
    for level, multiplier in levels:
        if last_multiplier is None or multiplier != last_multiplier:
            ranges.append({"level": level, "multiplier": multiplier})
            last_multiplier = multiplier
    return ranges


def write_ranges_file(levels_csv: Path, ranges_path: Path) -> None:
    levels = load_level_adjustments(levels_csv)
    ranges = build_ranges(levels)

    lines = ["["]
    for index, item in enumerate(ranges):
        encoded = json.dumps(item, separators=(", ", ": "))
        suffix = "," if index < len(ranges) - 1 else ""
        lines.append(f"  {encoded}{suffix}")
    lines.append("]")
    ranges_path.parent.mkdir(parents=True, exist_ok=True)
    ranges_path.write_text("\n".join(lines), encoding="utf-8")


def find_multiplier(level: int, ranges: list[tuple[int, int | None, float]]) -> float | None:
    for start, end, multiplier in ranges:
        if end is None and level >= start:
            return multiplier
        if end is not None and start <= level <= end:
            return multiplier
    return None


def scale_xp_values(
    data: dict,
    multiplier: float | None,
    ranges: list[tuple[int, int | None, float]] | None,
    default_multiplier: float | None,
) -> int:
    count = 0
    exports = data.get("Exports", [])
    for export in exports:
        table = export.get("Table")
        if not isinstance(table, dict):
            continue
        for row in table.get("Data", []):
            if not isinstance(row, dict):
                continue
            if row.get("StructType") != "S_jRPG_Level":
                continue

            level_name = row.get("Name")
            try:
                level = int(level_name)
            except (TypeError, ValueError):
                continue

            if ranges is not None:
                row_multiplier = find_multiplier(level, ranges)
                if row_multiplier is None:
                    if default_multiplier is None:
                        continue
                    row_multiplier = default_multiplier
            else:
                if multiplier is None:
                    continue
                row_multiplier = multiplier

            for prop in row.get("Value", []):
                if not isinstance(prop, dict):
                    continue
                if prop.get("Name") != "ExperienceNeededToReachThisLevel_2_34A827D0478AC7DA58357FA2F3884115":
                    continue
                value = prop.get("Value")
                if isinstance(value, int):
                    prop["Value"] = int(round(value * row_multiplier))
                    count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Scale XP values in DT_jRPG_Levels.uasset.json")
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("input/DT_jRPG_Levels.uasset.json"),
        help="Path to DT_jRPG_Levels.uasset.json",
    )
    parser.add_argument("multiplier", type=float, nargs="?", default=None, help="Scaling multiplier (e.g., 1.6)")
    parser.add_argument(
        "--levels-csv",
        type=Path,
        default=Path("config/level_multipliers.csv"),
        help="CSV file with level multipliers (tab-delimited)",
    )
    parser.add_argument(
        "--ranges-file",
        type=Path,
        default=Path("input/ranges.json"),
        help="JSON file with level multipliers (start or min/max ranges)",
    )
    parser.add_argument(
        "--skip-ranges-generation",
        action="store_true",
        help="Skip generating ranges.json and use the existing file instead",
    )
    parser.add_argument(
        "--default-multiplier",
        type=float,
        default=None,
        help="Multiplier for levels not covered by any range (default: keep original)",
    )
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output file path")
    args = parser.parse_args()

    input_path = args.input
    base_dir = input_path.parent
    if base_dir.name == "input":
        base_dir = base_dir.parent
    output_path = args.output or (base_dir / "output" / "Modded-DT_jRPG_Levels.uasset.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated_ranges = False
    if not args.skip_ranges_generation:
        response = input("Generate ranges.json from config/level_multipliers.csv? [Y/n] ").strip().lower()
        if response not in {"n", "no"}:
            write_ranges_file(args.levels_csv, args.ranges_file)
            generated_ranges = True

    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    ranges = parse_ranges_file(args.ranges_file)
    count = scale_xp_values(data, args.multiplier, ranges, args.default_multiplier)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")

    ranges_source = str(args.ranges_file)
    if generated_ranges:
        ranges_source = f"{ranges_source} (generated from {args.levels_csv})"
    elif args.skip_ranges_generation:
        ranges_source = f"{ranges_source} (generation skipped)"
    else:
        ranges_source = f"{ranges_source} (kept existing)"

    print("Level multipliers report")
    print(f"- Source: {ranges_source}")
    for start, end, multiplier in ranges:
        if end is None:
            label = f"{start}+"
        else:
            label = f"{start}-{end}"
        print(f"- Levels {label}: x{multiplier}")
    print(f"Updated {count} XP values -> {output_path}")


if __name__ == "__main__":
    main()
