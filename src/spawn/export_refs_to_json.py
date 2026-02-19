import argparse
import os
import subprocess
from pathlib import Path

PREFIX = Path("Sandfall/Content/Characters")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export listed .uasset files to JSON, preserving path from Characters/."
    )
    parser.add_argument(
        "--list",
        required=True,
        help="Path to references.csv (one asset path per line).",
    )
    parser.add_argument(
        "--game-root",
        default=r"H:\Gaming\Modding\Exp33\Game",
        help="Root directory that contains the Sandfall/Content/Characters folder.",
    )
    parser.add_argument(
        "--json-root",
        required=True,
        help="Output directory to write JSONs into.",
    )
    parser.add_argument(
        "--uassetgui",
        default=r"H:\Gaming\Modding\Exp33\UassetGUIexp33\UAssetGUIexp33.exe",
        help="Path to UAssetGUI.exe.",
    )
    parser.add_argument(
        "--engine",
        default="VER_UE5_4",
        help="Engine version (e.g. VER_UE5_4 or 29).",
    )
    parser.add_argument(
        "--mappings",
        default="ClairObscur5",
        help="Mappings name (no extension). Defaults to ClairObscur5.4.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    list_path = Path(args.list)
    game_root = Path(args.game_root)
    json_root = Path(args.json_root)
    uassetgui = Path(args.uassetgui)

    if not uassetgui.exists():
        raise FileNotFoundError(f"UAssetGUI.exe not found: {uassetgui}")

    with list_path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            rel = Path(line.replace("\\", "/"))
            if not rel.as_posix().startswith(PREFIX.as_posix() + "/"):
                raise ValueError(f"Path does not start with {PREFIX.as_posix()}: {line}")

            asset_rel = rel.relative_to(PREFIX)
            src_asset = game_root / rel

            out_json = json_root / asset_rel
            out_json = out_json.with_suffix(".json")
            out_json.parent.mkdir(parents=True, exist_ok=True)

            cmd = [str(uassetgui), "tojson", str(src_asset), str(out_json), args.engine]
            if args.mappings:
                cmd.append(args.mappings)

            subprocess.run(cmd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
