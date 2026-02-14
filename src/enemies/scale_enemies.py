import json
from pathlib import Path

INFILE = Path("input/DT_jRPG_Enemies.uasset.json")
OUTFILE = Path("output/Modded-DT_jRPG_Enemies.uasset.json")

# ---- Config ----

NAMES = {
    "HP": "HP_2_9B8F0EF14EBC6DBDE30E86A7FFE48646",
    "Speed": "Speed_16_FC80E04941CF184AEFA369950419F557",
    "Chroma": "Chroma_21_6C260F8F48BCE6E6C43C568C38941012",
    "XP": "Experience_23_BEE8A0DD4ED59C6C6782B88443AB9AE8",
}

# Multipliers by enemy type
MULTIPLIERS = {
    "normal": {"HP": 3.0, "Speed": 1.5, "Chroma": 1.25, "XP": 1},
    "boss":   {"HP": 1.5, "Speed": 1.333, "Chroma": 1.5, "XP": 1.5},
}

# Optional per-enemy overrides by EnemyHardcodedName
# Example:
# ENEMY_OVERRIDES = {
#     "Test_PlaceHolderBattleDude": {"HP": 2.5, "Speed": 1.2, "XP": 0.9},
#     "SM_FirstLancelier": {"HP": 4.0},
# }
ENEMY_OVERRIDES = {}

# ---- Constants ----

DOUBLE_TYPE = "UAssetAPI.PropertyTypes.Objects.DoublePropertyData, UAssetAPI"
SOFTOBJ_TYPE = "UAssetAPI.PropertyTypes.Objects.SoftObjectPropertyData, UAssetAPI"
BOOL_TYPE = "UAssetAPI.PropertyTypes.Objects.BoolPropertyData, UAssetAPI"
STRUCT_TYPE = "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI"

ENEMY_STRUCT = "S_jRPG_Enemy"
SCALING_STRUCT = "S_EnemyScalingMultipliers"

# ---- Helpers ----

def extract_enemy_asset_name(enemy_struct: dict) -> str:
    for item in enemy_struct.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type") == SOFTOBJ_TYPE
            and item.get("Name", "").startswith("EnemyActorClassSoft_")
        ):
            asset = item.get("Value", {}).get("AssetPath", {}).get("AssetName")
            if isinstance(asset, str) and asset:
                return asset
    return "<unknown_asset>"

def extract_enemy_hardcoded_name(enemy_struct: dict) -> str:
    for item in enemy_struct.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type") == "UAssetAPI.PropertyTypes.Objects.NamePropertyData, UAssetAPI"
            and item.get("Name") == "EnemyHardcodedName_4_0FAACC934CB2957BA37E888624E5835F"
        ):
            v = item.get("Value")
            if isinstance(v, str) and v:
                return v
    # fallback: the enemy struct's own "Name" field is usually the same
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

def find_scaling_struct(enemy_struct: dict):
    for item in enemy_struct.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type") == STRUCT_TYPE
            and item.get("StructType") == SCALING_STRUCT
            and isinstance(item.get("Value"), list)
        ):
            return item
    return None

def round1(x: float) -> float:
    return round(x, 1)

# Build a reverse map: property Name -> label ("HP"/"Speed"/"XP")
NAME_TO_LABEL = {v: k for k, v in NAMES.items()}

# ---- Main ----

with INFILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

stats = {
    "changed": {
        "normal": {"HP": 0, "Speed": 0, "Chroma": 0, "XP": 0},
        "boss": {"HP": 0, "Speed": 0, "Chroma": 0, "XP": 0},
    },
    "skipped_non_numeric": {
        "normal": {"HP": 0, "Speed": 0, "Chroma": 0, "XP": 0},
        "boss": {"HP": 0, "Speed": 0, "Chroma": 0, "XP": 0},
    },
    "missing_scaling": 0,
    "overrides_applied": 0,
}

# Handle full uasset.json structure
enemy_data = []
exports = data.get("Exports", [])
for export in exports:
    table = export.get("Table")
    if isinstance(table, dict):
        enemy_data = table.get("Data", [])
        break

# Fallback to root-level Data for simpler extracts
if not enemy_data:
    enemy_data = data.get("Data", [])

for entry in enemy_data:
    if not (
        isinstance(entry, dict)
        and entry.get("$type") == STRUCT_TYPE
        and entry.get("StructType") == ENEMY_STRUCT
    ):
        continue

    # asset_name = extract_enemy_asset_name(entry)
    enemy_name = extract_enemy_hardcoded_name(entry)
    is_boss = extract_is_boss(entry)

    is_mime = "MIME" in (enemy_name or "").upper()

    kind = "boss" if (is_boss or is_mime) else "normal"

    reason = (
    "boss"
    if is_boss
    else ("mime->boss" if is_mime else "normal")
    )

    scaling = find_scaling_struct(entry)
    if scaling is None:
        stats["missing_scaling"] += 1
        continue

    mults = MULTIPLIERS[kind]
    overrides = ENEMY_OVERRIDES.get(enemy_name, {})

    for prop in scaling["Value"]:
        if not (isinstance(prop, dict) and prop.get("$type") == DOUBLE_TYPE):
            continue

        pname = prop.get("Name")
        if pname not in NAME_TO_LABEL:
            continue  # ignore other scaling fields

        label = NAME_TO_LABEL[pname]
        val = prop.get("Value", None)

        if isinstance(val, (int, float)):
            old = float(val)
            if label in overrides:
                new = round1(float(overrides[label]))
                stats["overrides_applied"] += 1
                print(f"OVERRIDE [{enemy_name}] {label}: {old} -> {new}")
            else:
                mult = mults[label]
                new = round1(old * mult)
                print(f"CHANGED [{enemy_name}] ({reason}) {label}: {old} -> {new} (x{mult})")
            prop["Value"] = new
            if label not in overrides:
                stats["changed"][kind][label] += 1
        else:
            stats["skipped_non_numeric"][kind][label] += 1
            # print(f"SKIP   [{asset_name}] ({kind}) {label}: non-numeric Value {val!r}")
            print(f"SKIP   [{enemy_name}] ({reason}) {label}: non-numeric Value {val!r}")

print("\nSUMMARY")
print("-------")
print("Missing scaling struct:", stats["missing_scaling"])
print("Overrides applied:", stats["overrides_applied"])
for kind in ("normal", "boss"):
    print(f"\n{kind.upper()}")
    for label in ("HP", "Speed", "Chroma", "XP"):
        print(f"  {label} changed: {stats['changed'][kind][label]}")
        print(f"  {label} skipped (non-numeric): {stats['skipped_non_numeric'][kind][label]}")

OUTFILE.parent.mkdir(parents=True, exist_ok=True)
with OUTFILE.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
