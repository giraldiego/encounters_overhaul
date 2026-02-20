import json
import re
import sys
from pathlib import Path


# Editable list of words to match (case-insensitive).
# If either string in a [str, str] element contains any word below,
# the whole element is removed.
WORDS_TO_REMOVE = [
    "attack",
    "combo",
    "jumphit",
    "aoe",
    "ultimate",
    "range",
    "melee",
    "shoot ",
] 


SKILL_TO_REMOVE = [
    "ST_GO_Bourgeon_SuckupHero",
    "ST_GO_Bourgeon_MiasmaSpit",
    "ST_GO_Goblu_Bighit",
    "ST_YF_Glaise_3xSingle",
    "ST_YF_Boss_Scavenger_FacesShoot",
    "ST_YF_Boss_Scavenger_Masks_Fire",
    "ST_YF_Boss_Scavenger_Building1",
    "ST_YF_Boss_Scavenger_Building2",
    "ST_YF_Boss_Scavenger_Building3",
    "ST_YF_Boss_Scavenger_Building4",
    "ST_AS_PotatoBag_Tank_RightSlam",
    "ST_AS_PotatoBag_Tank_ShieldHit",
    "ST_AS_PotatoBag_Tank_LastStand",
    "ST_AS_PotatoBag_Mage_ThunderLaunch",
    "ST_AS_PotatoBag_Mage_LastStand",
    "ST_AS_PotatoBag_Boss_RightSlam",
    "ST_AS_PotatoBag_Boss_StunningGrenade",
    "ST_AS_PotatoBag_Boss_ShieldPunch",
    "ST_AS_PotatoBag_Boss_CounterFire",
    "ST_GV_Sciel_TwilightSlash",
    "ST_SC_Lampmaster_Skill4",
    "ST_SC_Lampmaster_Skill8",
    "ST_CW_LampMasterAlpha_LightEplosion",
    "ST_CW_LampMasterAlpha_HyperLightSlash",
    "ST_FB_Ramasseur_Alpha_MortalBlow",
    "ST_FB_Benisseur_Mortar",
    "ST_FB_Chalier_GradientCounterTutorial_GradientCounterTutorial",
    "ST_MM_Stalact_ExplosionOnHeroes",
    "ST_MM_Gargant_IcePunchA",
    "ST_MM_Gargant_IcePunchB",
    "ST_MM_Gargant_IcyRavageA",
    "ST_MM_Gargant_IcyRavageB",
    "ST_MF_Boucheclier_ShieldSmash",
    "ST_MF_Chapelier_AxeBash",
    "ST_MF_Chapelier_AxeSlash",
    "ST_MF_Contorsionniste_JoyfulImpale",
    "ST_MF_Grosstete_Skill3_EarthquakeJump",
    "ST_MF_Grosstete_Skill4_FireSpits",
    "ST_RE_Veilleur_BlightSmash",
    "ST_SI_Ballet_SwordSwipe",
    "ST_SI_Glissando_HeadSlam",
    "ST_SI_Glissando_GobbleUp",
    "ST_SI_Tisseur_Clap",
    "ST_SI_Glissando_Alpha_BigHeadsmash",
    "ST_L_Creation_BlackOrbExplode",
    "ST_WM_Serpenphare_HeadCrush1",
    "ST_WM_Serpenphare_HeadCrush2",
    "ST_WM_Serpenphare_HeadCrush3",
    "ST_WM_Serpenphare_LaserSwipe1",
    "ST_WM_Serpenphare_LaserSwipe2",
    "ST_WM_Serpenphare_TailSwipe1",
    "ST_WM_Serpenphare_TailSwipe2",
    "ST_WM_Serpenphare_TailSwipe3",
    "ST_WM_Boss_Sprong_Skill1A",
    "ST_WM_Boss_Sprong_Skill1B",
    "ST_WM_Boss_Sprong_Skill1C",
    "ST_WM_Boss_Sprong_Skill5A",
    "ST_SL_Sapling_CrushingWall_WallMoveFinal",
    "ST_Quest_SleepingBenisseur_BubbleThrow_1",
    "ST_Quest_SleepingBenisseur_BubbleThrow_2",
    "ST_Quest_SleepingBenisseur_BubbleThrow_3",
    "ST_Licorne_Skill1_Rainbow",
    "ST_Barbasucette_Skill4_ThrowBubbles",
        "ST_Franctale_Lasers",
        "ST_GO_Luster_UnleashFury",
        "ST_GO_Demineur_ALPHA_UnleashFire",
        "ST_GV_Sciel_SealedFate",
        "ST_GV_Sciel_MarkingCard",
        "ST_SC_Lampmaster_Skill1",
        "ST_FB_Troubadour_TrickyShot",
        "ST_FB_Troubadour_TrumpetConcerto",
        "ST_FB_Troubadour_CursedSong",
        "ST_FB_DuallisteLR_StormBlood",
        "ST_MM_Danseuse_Fire_GradientFall",
        "ST_MM_Stalact_Fire_Earthquakes",
        "ST_MM_Braseleur_Fire_DroneFire",
        "ST_MM_Braseleur_Fire_HammerSmash",
        "ST_CZ_ChromaMaelle_ChromaFury"
  ]


def compile_word_patterns(words: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(re.escape(word), re.IGNORECASE) for word in words if word.strip()]


def contains_any_word(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def remove_matching_elements(obj, patterns: list[re.Pattern[str]]) -> tuple[object, int]:
    removed_count = 0

    if isinstance(obj, list):
        new_list = []
        for item in obj:
            if (
                isinstance(item, list)
                and len(item) == 2
                and isinstance(item[0], str)
                and isinstance(item[1], str)
            ):
                left, right = item
                if contains_any_word(left, patterns) or contains_any_word(right, patterns):
                    removed_count += 1
                    continue

            processed_item, item_removed = remove_matching_elements(item, patterns)
            removed_count += item_removed
            new_list.append(processed_item)

        return new_list, removed_count

    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            processed_value, value_removed = remove_matching_elements(value, patterns)
            removed_count += value_removed
            new_dict[key] = processed_value
        return new_dict, removed_count

    return obj, removed_count


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python remove_elements_by_words.py <input_json_file>")
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.exists() or not input_path.is_file():
        print(f"Input file not found: {input_path}")
        return 1

    patterns = compile_word_patterns(WORDS_TO_REMOVE + SKILL_TO_REMOVE)
    if not patterns:
        print("No valid words configured in WORDS_TO_REMOVE.")
        return 1

    with input_path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)

    updated_data, removed = remove_matching_elements(data, patterns)

    output_path = input_path.with_name(f"Adj-{input_path.name}")
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(updated_data, outfile, indent=2, ensure_ascii=False)

    print(f"Removed {removed} elements.")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
