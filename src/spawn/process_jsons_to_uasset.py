import argparse
import subprocess
from pathlib import Path

from check_respawns_on_rest import process_json_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process JSONs to add RespawnsOnRest and convert to .uasset."
    )
    parser.add_argument(
        "--json-root",
        required=True,
        help="Root directory containing source JSON files.",
    )
    parser.add_argument(
        "--out-root",
        required=True,
        help="Output directory for generated .uasset files.",
    )
    parser.add_argument(
        "--uassetgui",
        default=r"H:\Gaming\Modding\Exp33\UassetGUIexp33\UAssetGUIexp33.exe",
        help="Path to UAssetGUI.exe.",
    )
    parser.add_argument(
        "--mappings",
        default="ClairObscur5",
        help="Mappings name (no extension). Defaults to ClairObscur5.4.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories.",
    )
    return parser.parse_args()


def iter_json_files(root: Path, recursive: bool) -> list[Path]:
    if recursive:
        return sorted(root.rglob("*.json"))
    return sorted(root.glob("*.json"))


def build_uasset_output(json_root: Path, out_root: Path, json_path: Path) -> Path:
    relative = json_path.relative_to(json_root)
    return out_root / relative.with_suffix(".uasset")


def main() -> int:
    args = parse_args()
    json_root = Path(args.json_root)
    out_root = Path(args.out_root)
    uassetgui = Path(args.uassetgui)

    if not json_root.exists():
        print(f"JSON root not found: {json_root}")
        return 2
    if not uassetgui.exists():
        print(f"UAssetGUI.exe not found: {uassetgui}")
        return 2

    files = iter_json_files(json_root, args.recursive)
    if not files:
        print("No JSON files found.")
        return 0

    for json_path in files:
        result = process_json_report(json_path)
        if result["status"] == "error":
            print(f"{json_path}: skipped (error: {result['error']})")
            continue
        if result["status"] == "missing-default":
            print(f"{json_path}: skipped (Default__ export not found)")
            continue
        if not result["added"]:
            print(f"{json_path}: skipped (property already present)")
            continue

        processed_path = result["output_path"]
        if processed_path is None:
            print(f"{json_path}: skipped (no output JSON written)")
            continue
        if not Path(processed_path).exists():
            print(f"{json_path}: skipped (processed JSON not found: {processed_path})")
            continue

        out_asset_path = build_uasset_output(json_root, out_root, json_path)
        out_asset_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [str(uassetgui), "fromjson", str(processed_path), str(out_asset_path)]
        if args.mappings:
            cmd.append(args.mappings)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            print(f"{json_path}: fromjson failed ({exc.returncode})")
            if exc.stdout:
                print(f"stdout: {exc.stdout.strip()}")
            if exc.stderr:
                print(f"stderr: {exc.stderr.strip()}")
            continue

        print(f"{json_path} -> {processed_path} -> {out_asset_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
