import json
from pathlib import Path

INFILE = Path("input/ST_Enemies_Skills.uasset.json")
OUTFILE = Path("output/Modded-ST_Enemies_Skills.uasset.json")

REPLACEMENT_TEXT = "."

# Always replace when any of these matches (highest priority)
ALWAYS_REPLACE_KEY_SUBSTRINGS = [
    "shieldpunch",
    "shieldhit",
    "shieldsmash",
    "shieldslam",
    "shieldstrike",
    "counterattack",
    "counterstrike",
    #"explosion",
    #"explode",
    "aoe"
] + [
    "ST_GO_Demineur_LongRange",
    "ST_SC_Lampmaster_TurnOffLevelLamps",
    "ST_L_Boss_Curator_BlackHole",
    "ST_L_Boss_Curator_Skill4",
    "ST_L_Boss_Curator_Skill5",
    "ST_L_Boss_Curator_BlackLake",
    "ST_L_Boss_Curator_ConvasTransition"

]
ALWAYS_REPLACE_TEXT_SUBSTRINGS = [
    "slams its shield",
    "slams his shield",
    "counterattacks",
]

# Replace when at least one trigger matches (key OR text)
TRIGGER_KEY_SUBSTRINGS = [
    "attack",
    "combo",
    "slash",
    "smash",
    "shoot",
]
TRIGGER_TEXT_SUBSTRINGS = [
    "{name}",
    "at the expedition",
    "attacks",
    "strikes",
    "explodes"
]

# Do NOT replace when any exempt matches (key OR text)
EXEMPT_KEY_SUBSTRINGS = [
    "summon",
    "phase",
    "turn",
    "shield",
    "heal",
]
EXEMPT_TEXT_SUBSTRINGS = [
    "summons",
    "feels threatened",
    "turn starts",
    "turn ends",
    "shields",
    "heals",
    "weak point",
    "is about",
    "re-enter"
]


def contains_any(source: str, patterns: list[str]) -> bool:
    source_lower = source.lower()
    return any(pattern.lower() in source_lower for pattern in patterns)


def should_replace(key: str, text: str) -> bool:
    if not text or text == REPLACEMENT_TEXT:
        return False

    if contains_any(key, ALWAYS_REPLACE_KEY_SUBSTRINGS) or contains_any(text, ALWAYS_REPLACE_TEXT_SUBSTRINGS):
        return True

    if contains_any(key, EXEMPT_KEY_SUBSTRINGS) or contains_any(text, EXEMPT_TEXT_SUBSTRINGS):
        return False

    return contains_any(key, TRIGGER_KEY_SUBSTRINGS) or contains_any(text, TRIGGER_TEXT_SUBSTRINGS)


def process_pairs(pairs: list[list[str]]) -> tuple[int, list[str]]:
    changed = 0
    unchanged: list[str] = []

    for pair in pairs:
        if not (
            isinstance(pair, list)
            and len(pair) == 2
            and isinstance(pair[0], str)
            and isinstance(pair[1], str)
        ):
            continue

        key, text = pair
        if should_replace(key, text):
            pair[1] = REPLACEMENT_TEXT
            changed += 1
        else:
            unchanged.append(f"{key}: {text}")

    return changed, unchanged


def find_value_lists(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("Value"), list):
            yield obj["Value"]
        for value in obj.values():
            yield from find_value_lists(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_value_lists(item)


def main() -> None:
    with INFILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    value_lists = list(find_value_lists(data))
    if not value_lists and isinstance(data, dict) and isinstance(data.get("Value"), list):
        value_lists = [data["Value"]]

    if not value_lists:
        raise ValueError("No 'Value' list found with [key, text] pairs.")

    total_changed = 0
    unchanged: list[str] = []
    for pairs in value_lists:
        changed, not_changed = process_pairs(pairs)
        total_changed += changed
        unchanged.extend(not_changed)

    print(f"Replaced text in {total_changed} entries.")
    print("Unchanged strings:")
    for item in unchanged:
        print(item)

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
