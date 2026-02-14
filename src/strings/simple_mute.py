import json
from pathlib import Path

INFILE = Path("input/ST_Enemies_Skills.uasset.json")
OUTFILE = Path("output/Modded-ST_Enemies_Skills.uasset.json")

REPLACEMENT_TEXT = "..."

TRIGGER_SUBSTRINGS = ["{name}", "at the Expedition"]  # replace only if any of these is present
EXEMPT_SUBSTRINGS = ["turn"]  # but skip if any of these is present

with open(INFILE, "r", encoding="utf-8") as f:
    data = json.load(f)

changed = 0

def should_replace(text: str) -> bool:
    t = text.lower()
    return any(s.lower() in t for s in TRIGGER_SUBSTRINGS) and not any(
        s.lower() in t for s in EXEMPT_SUBSTRINGS
    )

unchanged = []

def process(obj):
    global changed

    if isinstance(obj, list):
        if len(obj) == 2 and isinstance(obj[0], str) and isinstance(obj[1], str):
            if obj[1] != REPLACEMENT_TEXT:
                if should_replace(obj[1]):
                    obj[1] = REPLACEMENT_TEXT
                    changed += 1
                else:
                    unchanged.append(obj[1])

        for item in obj:
            process(item)

    elif isinstance(obj, dict):
        for value in obj.values():
            process(value)

process(data)

print(f"Replaced text in {changed} entries.")
print("Unchanged strings:")
for s in unchanged:
    print(s)

with open(OUTFILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
