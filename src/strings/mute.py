import json
from pathlib import Path

INFILE = Path("input/ST_Enemies_Skills.uasset.json")
OUTFILE = Path("output/Modded-ST_Enemies_Skills.uasset.json")

REPLACEMENT_TEXT = "..."

# Verbs indicating attack actions - mute these
ATTACK_VERBS = [
    "attacks", "attack", "perform", "combo", "jumps", "jump",
    "casts a spell", "cast", "summons", "unleashes", 
    "smashes", "smash", "spits", "spit", "eats", "chains",
    "dashes", "slams", "slam", "crashes", "crash", "fires", "fire",
    "spins", "spin", "crushes", "crush", "sweeps", "sweep",
    "launches", "launch", "throws", "throw", "strikes", "strike",
    "uses", "use", "shoot", "swings", "swing", 
    "catapults", "lands", "tears", "wreaks", "freezes", "freeze",
    "triggers", "explodes", "explode"
]

# Patterns for non-attacks - keep these (don't mute)
NON_ATTACK_PATTERNS = [
    "charges", "prepares", "is about to", "preparing",
    "enraged", "threatened", "shields", "heals", 
    "revives", "applies", "gains", "feels", 
    "skips", "turn", "turns", "weak point", "shot at",
    "shakes", "calls for help", "becomes", "grows", "absorbs",
    "regenerates", "consumes", "sends a wave", "strengthened", "weakened",
    "ends", "spawns", "buffs", "interrupted", "exhausts", "marks",
    "creates", "pounds", "darkens", "binds",
    "damaged", "destroyed", "broken", "weakens", "rebuilds",
    "raises", "takes the fight", "covers", "powers up", "power up",
    "draws strength", "emanates", "disrupt",
    "flies off", "switches", "heating up", "yells",
    "arrives", "thaws", "lights up", "grabs", "makes a sacrifice", "plunges",
    "is about to explode"
]

with INFILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Navigate to the string table data
string_table = None
for export in data.get("Exports", []):
    if export.get("$type") == "UAssetAPI.ExportTypes.StringTableExport, UAssetAPI":
        string_table = export.get("Table", {}).get("Value")
        break

if string_table is None:
    raise ValueError("Could not find StringTableExport in the file")

changed = 0

def should_replace(text: str) -> bool:
    """Return True if text describes an attack action and should be muted."""
    if not text or "{name}" not in text:
        return False
    
    t = text.lower()
    
    # Don't mute if it contains non-attack patterns
    if any(pattern.lower() in t for pattern in NON_ATTACK_PATTERNS):
        return False
    
    # Mute if it contains attack verbs
    return any(verb.lower() in t for verb in ATTACK_VERBS)

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

process(string_table)

print(f"Replaced text in {changed} entries.")
print("Unchanged strings:")
for s in unchanged:
    print(s)

OUTFILE.parent.mkdir(parents=True, exist_ok=True)
with OUTFILE.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
