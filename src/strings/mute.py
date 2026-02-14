import json
from pathlib import Path

INFILE = Path("input/ST_Enemies_Skills.uasset.json")
OUTFILE = Path("output/Modded-ST_Enemies_Skills.uasset.json")

REPLACEMENT_TEXT = "..."

# Key patterns that strongly indicate attacks - mute these
ATTACK_KEY_PATTERNS = [
    "attack", "combo", "hit", "slash", "smash", "strike", "shot", "shoot",
    "punch", "kick", "melee", "aoe", "range", "ranged", "estoc", "spear",
    "sword", "hammer", "blade", "cut", "stab", "impale", "bash", "bonk",
    "crush", "slam", "smite", "cleave", "swing", "swipe", "sweep",
    "fire", "blast", "bolt", "missile", "projectile", "cannon",
    "throw", "launch", "hurl", "toss", "lob",
    "bite", "claw", "gore", "maul", "rend", "tear",
    "fury", "wrath", "rampage", "frenzy", "finisher",
    "barrage", "volley", "salvo", "burst",
    "skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7", "skill8", "skill9"
]

# Key patterns that indicate non-attacks - keep these
# BUT: Be specific - "Shield" alone isn't enough, need context
NON_ATTACK_KEY_PATTERNS = [
    "summon", "buff", "debuff", "heal", "revive",
    "phase", "enter", "charge", "warn", "prepare",
    "weakspot", "weak", "break", "tutorial", "end", "start",
    "enraged", "enrage", "threatened", "calm",
    "boost", "apply", "gain",
    "regenerate", "recover", "restore", "rebuild", "regen",
    "ritual", "incantation", "pray",
    "parry", "dodge", "block", "defense",
    "stance", "mode", "form", "transform", "switch",
    "spawn", "grow", "emerge", "appear",
    "call", "invoke",
    "effect", "feedback", "tooltip", "turn",
    "puzzle", "trial", "complete", "failed",
    "transition", "vanish",
    "absorb", "drain", "devourer",
    "shieldbuff", "shieldteam", "applyshield", "shieldallie",  # Specific shield non-attacks  
    "healally", "healpreparation", "healmask",  # Specific heal non-attacks
    "buffteam", "buffshield",  # Specific buff non-attacks
]

# Compound patterns that override non-attack detection (attack + defense word)
ATTACK_OVERRIDE_PATTERNS = [
    "shieldhit", "shieldpunch", "shieldsmash", "shieldslam", "shieldstrike",  # Attacking WITH shield
    "counterattack", "counterstrike", "counterfire",  # Counter attacks ARE attacks
    "attackdebuff", "attackexhaust", "attackmarked", "attackagain",  # Attacks with side effects
    "rangeattack",  # Range attacks
    "weakribbonattack",  # Weakened attacks are still attacks
    "buffattack", "attackbuff",  # Buffs that also attack- "closecombo",  # Close-range combos
]

# Text patterns for attacks (secondary check)
ATTACK_TEXT_PATTERNS = [
    "attacks", "attack", "performing", "perform", "combo",
    "jumps", "jump", "leaps", "leap",
    "casts a spell at", "casting", "casts an exploding",
    "dashes", "dash", "slams", "slam", "crashes", "crash",
    "fires", "fire", "spins", "spin", "crushes", "crush",
    "sweeps", "sweep", "launches", "launch", "throws", "throw",
    "strikes", "strike", "swings", "swing", "swipes", "swipe",
    "uses", "use", "shoots", "shoot",
    "lands a", "tears up", "tears apart", "wreaks",
    "slashes", "slash", "smashes", "smash",
    "bites", "bite", "claws", "claw", "mauls", "maul",
    "counterattacks", "counterattack"  # Counterattacks ARE attacks
]

# Text patterns for non-attacks (keep these)
# These should be STRONG indicators - specific phrases that clearly indicate non-attacks
NON_ATTACK_TEXT_PATTERNS = [
    "charges up", "charges a", "charging",
    "prepares a", "preparing a", " is preparing", "getting ready",
    "is about to unleash", "is about to explode", "is about to jump", "is about to launch", "is about to crush",
    "is enraged", "feels threatened", "becomes weak",
    "shields its allies", "shields his allies", "shields her allies",
    "heals", "healing", "revives", "reviving",
    "applies shields", "applies rush", "applies powerful", "applies exhaust", "applies inverted", "gains", "feels",
    "turn starts", "turn ends", "takes another turn", "take another turn", "play a second time",
    "weak point", "weakspot", "is weak", "vulnerable",
    "shot at", "you shot",
    "calls for help", "summons minions", "summons other", "summons a", "summons 2", "summons the", "summons strange",
    "becomes weak", "grows flowers", "emerges from", "appears",
    "absorbs the", "absorbs energy", "draws strength",
    "regenerates", "rebuilds", "recovers",
    "consumes burns", "drains",
    "sends a wave of fire", "inner fire is",
    "ends the", "spawns", "buffs its",  " interrupted",
    "creates earthquakes", "pounds the ground", "darkens the sky",
    "damaged", "destroyed", "is broken", "starting to crack",
    "raises its shield", "raises his shield", "takes the fight seriously",
    "covers her sword", "covers his sword",
    "powers up", "power emanates", "draws strength from",
    "emanates", "tries to disrupt", "tries to build", "tries to heal",
    "flies off", "flies away", "switches stance", "switching stance", "heating up", "yells",
    "arrives", "thaws", "lights up", "lights the",
    "grabs a spear", "makes a sacrifice", "plunges the battle", "gobbles up a dead",
    "strange ritual", "incantation",
    "no effect", "has no effect", "emits a", "glow",
    "trial", "completed the", "failed the", "cancelled",
   " doesn't seem", "seems to weaken", "seems to kill", "looks like",
    "vanishes", "falls", "doubles the blight",
    " get ready", "gets ready", "surrounded by",
    "gain shield", "becomes dangerously stronger",
    "enchants", "seduces", "curses the expedition",
    "weaves", "releases the bouquet", "dances with",
    " begins", "rescues", " supports", "defends", "enters phase",
    "is furious", "is coming", "is off-balance", "is stronger",
    "placid stance", "more resistant", "more vulnerable",
    "selects", "increases its allies", "protects an", "cascades from",
    "turns its lamps", "turns his sword"
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

def should_replace(key: str, text: str) -> bool:
    """Return True if the key-text pair describes an attack action and should be muted.
    
    Uses a multi-stage heuristic:
    1. Check key for compound attack patterns that override non-attack indicators
    2. Check key for strong non-attack indicators (keep these)
    3. Check key for attack indicators (mute these)
    4. Check text for non-attack patterns (keep if no strong attack key)
    5. Check text for attack patterns (mute if no non-attack indicators)
    """
    if not text:
        return False
    
    # Relax the {name} requirement - also accept "The " prefix for creature names
    if "{name}" not in text and not text.startswith("The "):
        return False
    
    key_lower = key.lower()
    text_lower = text.lower()
    
    # Stage 1: Check for compound attack patterns (highest priority - these ARE attacks)
    if any(pattern in key_lower for pattern in ATTACK_OVERRIDE_PATTERNS):
        return True
    
    # Stage 2: Check key for strong non-attack indicators
    for pattern in NON_ATTACK_KEY_PATTERNS:
        if pattern in key_lower:
            return False
    
    # Stage 3: Check key for attack indicators
    key_suggests_attack = any(pattern in key_lower for pattern in ATTACK_KEY_PATTERNS)
    
    # Check if this is a VERY strong attack indicator (combo with numbers, specific attacks)
    strong_attack_key = any(p in key_lower for p in ["combo", "hit", "slash", "strike", "melee"])
    
    # Stage 4: Check text for non-attack patterns
    text_suggests_non_attack = any(pattern in text_lower for pattern in NON_ATTACK_TEXT_PATTERNS)
    
    # Stage 5: Check text for attack patterns
    text_suggests_attack = any(pattern in text_lower for pattern in ATTACK_TEXT_PATTERNS)
    
    # Decision logic:
    # - If key STRONGLY suggests attack, mute (don't let text override)
    # - If key suggests attack, mute unless text STRONGLY suggests non-attack
    # - If key is neutral but text suggests attack, mute
    # - Otherwise, don't mute
    
    if key_suggests_attack:
        # Key indicates attack
        if strong_attack_key:
            # Very strong attack indicator - don't let text override
            # Unless it's clearly a preparation/charge
            if any(p in text_lower for p in ["prepares a", "charges a", "is about to", "preparing a"]):
                return False
            return True
        
        # Regular attack indicator - text can override
        if text_suggests_non_attack:
            return False
        return True
    
    # Key is neutral, rely on text analysis
    if text_suggests_non_attack:
        return False
    
    return text_suggests_attack

unchanged = []

def process(obj):
    global changed

    if isinstance(obj, list):
        if len(obj) == 2 and isinstance(obj[0], str) and isinstance(obj[1], str):
            key, text = obj[0], obj[1]
            if text != REPLACEMENT_TEXT:
                if should_replace(key, text):
                    obj[1] = REPLACEMENT_TEXT
                    changed += 1
                else:
                    unchanged.append(f"{key}: {text}")

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

print(f"Replaced text in {changed} entries.")
print("Unchanged strings:")
for s in unchanged:
    print(s)

OUTFILE.parent.mkdir(parents=True, exist_ok=True)
with OUTFILE.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
