import json
from pathlib import Path

INFILE = Path("input/DT_jRPG_Enemies.uasset.json")
OUTFILE = Path("../../output/enemies/Modded-DT_jRPG_Enemies.uasset.json")

# ---- Config ----

ROUND_DECIMALS = 2

# When enabled, values below LOW_VALUE_THRESHOLD are replaced before scaling,
# but only for stats listed in LOW_VALUE_BASE_ENABLED_STATS.
USE_LOW_VALUE_BASE = True
LOW_VALUE_THRESHOLD = 0.75
LOW_VALUE_BASE_ENABLED_STATS = {
    "HP",
    "XP",
}
LOW_VALUE_BASE_BY_STAT = {
    "HP": 0.75,
    # "Speed": 1.0,
    # "ATK": 1.0,
    # "Chroma": 1.0,
    "XP": 0.75,
}

NAMES = {
    "HP": "HP_2_9B8F0EF14EBC6DBDE30E86A7FFE48646",
    "ATK": "PhysicalAttack_4_82A69E334B7A1E723084829AFCCEAA25",
    "Speed": "Speed_16_FC80E04941CF184AEFA369950419F557",
    "Chroma": "Chroma_21_6C260F8F48BCE6E6C43C568C38941012",
    "XP": "Experience_23_BEE8A0DD4ED59C6C6782B88443AB9AE8",
}

# Multipliers by enemy type
MULTIPLIERS = {
    # "volester": {"HP": 6.0, "ATK": 1.2, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
    # "cultistflying": {"HP": 6.0, "ATK": 1.2, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
    # "ballet": {"HP": 6.0, "ATK": 1.2, "Speed": 1.5, "Chroma": 1.5, "XP": 1},

    "mime":   {"HP": 1.0, "ATK": 1.5, "Speed": 1.333, "Chroma": 1, "XP": 1},

    "default": {"HP": 3.0, "ATK": 1.2, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
    "alpha":  {"HP": 2.0, "ATK": 1.0, "Speed": 1.1, "Chroma": 1.5, "XP": 0.4},
    "boss":   {"HP": 1.5, "ATK": 1.1, "Speed": 1.333, "Chroma": 2, "XP": 1.5},

    # "weak":   {"HP": 3.0, "ATK": 1.333, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
    # "regular": {"HP": 3.0, "ATK": 1.333, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
    # "strong": {"HP": 3.0, "ATK": 1.333, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
    # "elite":  {"HP": 3.0, "ATK": 1.333, "Speed": 1.5, "Chroma": 1.5, "XP": 1},
}

# Optional per-enemy overrides by EnemyHardcodedName (values replace category multipliers)

ENEMY_OVERRIDES = {
    "MO_Boss_Paintress": {"HP": 1.2, "ATK": 1.1, "Speed": 1.333, "Chroma": 2, "XP": 1.5},
    "SM_Lancelier_Alpha": {"HP": 3.0, "ATK": 1.0, "Speed": 1.1, "Chroma": 1.5, "XP": 0.4},
    "SM_Abbest_Alpha": {"HP": 3.0, "ATK": 1.0, "Speed": 1.1, "Chroma": 1.5, "XP": 0.4},
    "GO_Demineur": {"HP": 3.0, "ATK": 1.2, "Speed": 1.333, "Chroma": 1.5, "XP": 1.0},
}

# EnemyHardcodedName patterns that should be treated as bosses (case-insensitive substring match)
BOSS_NAME_PATTERNS = [
    # "MIME",
]

# EnemyHardcodedName patterns for alpha/elite enemies (case-insensitive substring match)
ALPHA_NAME_PATTERNS = [
    "ALPHA",
    "_Alpha",
]

# Custom per-name categories; if a name matches one of these patterns and the
# category exists in MULTIPLIERS, it takes priority over archetype/boss/alpha.
CUSTOM_NAME_PATTERNS = {
    "mime": [
        "MIME",
    ],
    # "volester":[
    #     "Volester",
    # ],
    # "cultistflying":[
    #     "CultistFlying",
    # ],
    # "ballet":[
    #     "Ballet",
    # ]
}

# ---- Constants ----

DOUBLE_TYPE = "UAssetAPI.PropertyTypes.Objects.DoublePropertyData, UAssetAPI"
SOFTOBJ_TYPE = "UAssetAPI.PropertyTypes.Objects.SoftObjectPropertyData, UAssetAPI"
BOOL_TYPE = "UAssetAPI.PropertyTypes.Objects.BoolPropertyData, UAssetAPI"
STRUCT_TYPE = "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI"
OBJECT_TYPE = "UAssetAPI.PropertyTypes.Objects.ObjectPropertyData, UAssetAPI"

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

def build_enemy_archetype_value_map(data: dict) -> dict[int, str]:
    value_to_kind: dict[int, str] = {}

    for idx, imp in enumerate(data.get("Imports", []), start=1):
        if not isinstance(imp, dict):
            continue

        obj_name = imp.get("ObjectName")
        if not (isinstance(obj_name, str) and obj_name.startswith("BP_DataAsset_Archetype_")):
            continue

        raw_kind = obj_name.removeprefix("BP_DataAsset_Archetype_").lower()
        kind = {
            "boss_noachievement": "boss",
            "hardonly_boss": "boss",
            "hardonly_opboss": "boss",
        }.get(raw_kind, raw_kind)

        value_to_kind[-idx] = kind

    return value_to_kind

def extract_enemy_archetype_kind(enemy_struct: dict, value_to_kind: dict[int, str]) -> str | None:
    for item in enemy_struct.get("Value", []):
        if (
            isinstance(item, dict)
            and item.get("$type") == OBJECT_TYPE
            and item.get("Name", "").startswith("EnemyArchetype_")
        ):
            val = item.get("Value")
            if isinstance(val, int):
                return value_to_kind.get(val)
            return None
    return None

def apply_rounding(x: float) -> float:
    return round(x, ROUND_DECIMALS)

def get_value_to_scale(label: str, value: float) -> tuple[float, bool]:
    if (
        not USE_LOW_VALUE_BASE
        or label not in LOW_VALUE_BASE_ENABLED_STATS
        or value >= LOW_VALUE_THRESHOLD
    ):
        return value, False

    replacement = LOW_VALUE_BASE_BY_STAT.get(label)
    if replacement is None:
        return value, False

    return float(replacement), True

def matches_boss_pattern(enemy_name: str) -> bool:
    if not enemy_name:
        return False
    name_upper = enemy_name.upper()
    return any(pattern.upper() in name_upper for pattern in BOSS_NAME_PATTERNS if pattern)

def matches_alpha_pattern(enemy_name: str) -> bool:
    if not enemy_name:
        return False
    name_upper = enemy_name.upper()
    return any(pattern.upper() in name_upper for pattern in ALPHA_NAME_PATTERNS if pattern)

def detect_custom_kind(enemy_name: str) -> str | None:
    if not enemy_name:
        return None

    name_upper = enemy_name.upper()
    for kind, patterns in CUSTOM_NAME_PATTERNS.items():
        if any(pattern.upper() in name_upper for pattern in patterns if pattern):
            return kind
    return None

# Build a reverse map: property Name -> label ("HP"/"Speed"/"XP")
NAME_TO_LABEL = {v: k for k, v in NAMES.items()}

# ---- Main ----

with INFILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

enemy_archetype_value_map = build_enemy_archetype_value_map(data)

stats = {
    "changed": {kind: {"HP": 0, "ATK": 0, "Speed": 0, "Chroma": 0, "XP": 0} for kind in MULTIPLIERS},
    "skipped_non_numeric": {kind: {"HP": 0, "ATK": 0, "Speed": 0, "Chroma": 0, "XP": 0} for kind in MULTIPLIERS},
    "low_value_base_applied": {kind: {"HP": 0, "ATK": 0, "Speed": 0, "Chroma": 0, "XP": 0} for kind in MULTIPLIERS},
    "missing_scaling": 0,
    "overrides_applied": 0,
    "alpha_boss_conflicts": [],
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
    archetype_kind = extract_enemy_archetype_kind(entry, enemy_archetype_value_map)
    custom_kind = detect_custom_kind(enemy_name)

    matches_boss_pat = matches_boss_pattern(enemy_name)
    matches_alpha_pat = matches_alpha_pattern(enemy_name)

    if matches_alpha_pat and (is_boss or matches_boss_pat):
        stats["alpha_boss_conflicts"].append(enemy_name)

    # Determine category:
    # 1) explicit archetype in data if configured in MULTIPLIERS
    # 2) alpha pattern
    # 3) custom name pattern if configured in MULTIPLIERS
    # 4) boss flag/pattern
    # 5) default fallback
    if archetype_kind in MULTIPLIERS:
        kind = archetype_kind
        reason = f"archetype:{archetype_kind}"
    elif matches_alpha_pat and "alpha" in MULTIPLIERS:
        kind = "alpha"
        reason = "alpha"
    elif custom_kind in MULTIPLIERS:
        kind = custom_kind
        reason = f"pattern->{custom_kind}"
    elif is_boss or matches_boss_pat:
        kind = "boss"
        reason = "boss" if is_boss else "pattern->boss"
    else:
        kind = "default"
        reason = "default"

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
            value_to_scale, used_low_value_base = get_value_to_scale(label, old)

            if used_low_value_base:
                stats["low_value_base_applied"][kind][label] += 1

            if label in overrides:
                override_mult = float(overrides[label])
                new = apply_rounding(value_to_scale * override_mult)
                stats["overrides_applied"] += 1
                if used_low_value_base:
                    print(
                        f"OVERRIDE [{enemy_name}] {label}: {old} -> {value_to_scale} -> {new} "
                        f"(base<{LOW_VALUE_THRESHOLD}, x{override_mult})"
                    )
                else:
                    print(f"OVERRIDE [{enemy_name}] {label}: {old} -> {new} (x{override_mult})")
            else:
                mult = mults[label]
                new = apply_rounding(value_to_scale * mult)
                if used_low_value_base:
                    print(
                        f"CHANGED [{enemy_name}] ({reason}) {label}: {old} -> {value_to_scale} -> {new} "
                        f"(base<{LOW_VALUE_THRESHOLD}, x{mult})"
                    )
                else:
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
if stats["alpha_boss_conflicts"]:
    print("\nALPHA+BOSS CONFLICTS (alpha multipliers applied)")
    for name in sorted(set(stats["alpha_boss_conflicts"])):
        print(f"  {name}")
for kind in MULTIPLIERS.keys():
    print(f"\n{kind.upper()}")
    for label in ("HP", "ATK", "Speed", "Chroma", "XP"):
        print(f"  {label} changed: {stats['changed'][kind][label]}")
        print(f"  {label} low-value base applied: {stats['low_value_base_applied'][kind][label]}")
        print(f"  {label} skipped (non-numeric): {stats['skipped_non_numeric'][kind][label]}")

OUTFILE.parent.mkdir(parents=True, exist_ok=True)
with OUTFILE.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
