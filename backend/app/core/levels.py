from typing import Optional, Dict
import string

RANK_CONFIG = [
    {"level": 1, "name": "童生", "key": "tongsheng", "exp_required": 0, "desc": "初入诗门，蒙学启智"},
    {"level": 2, "name": "秀才", "key": "xiucai", "exp_required": 100, "desc": "通晓诗文，小有所成"},
    {"level": 3, "name": "举人", "key": "juren", "exp_required": 400, "desc": "乡试及第，学贯古今"},
    {"level": 4, "name": "贡士", "key": "gongshi", "exp_required": 800, "desc": "会试中式，才华出众"},
    {"level": 5, "name": "进士", "key": "jinshi", "exp_required": 1500, "desc": "殿试入围，博古通今"},
    {"level": 6, "name": "探花", "key": "tanhua", "exp_required": 2500, "desc": "金榜题名，才情卓绝"},
    {"level": 7, "name": "榜眼", "key": "bangyan", "exp_required": 4400, "desc": "名列前茅，学富五车"},
    {"level": 8, "name": "状元", "key": "zhuangyuan", "exp_required": 6000, "desc": "独占鳌头，天下无双"},
]


def get_rank_by_level(level: int) -> Dict:
    level = max(1, min(level, len(RANK_CONFIG)))
    return RANK_CONFIG[level - 1]


def get_rank_by_exp(exp: int) -> Dict:
    result = RANK_CONFIG[0]
    for rank in RANK_CONFIG:
        if exp >= rank["exp_required"]:
            result = rank
        else:
            break
    return result


def calculate_level(exp: int) -> int:
    return get_rank_by_exp(exp)["level"]


def get_next_rank(level: int) -> Optional[Dict]:
    if level >= len(RANK_CONFIG):
        return None
    return RANK_CONFIG[level]


def exp_to_next_level(exp: int) -> Optional[int]:
    current = get_rank_by_exp(exp)
    nxt = get_next_rank(current["level"])
    if nxt is None:
        return None
    return nxt["exp_required"] - exp


FHL_EXP_RATE = 0.5
RELAY_EXP_RATE = 0.5
RELAY_POINTS_RATE = 0.1
CHALLENGE_BASE_EXP = 10
CHALLENGE_BASE_POINTS = 2
LEARNING_EXP_PER_POEM = 2
LEARNING_MIN_DURATION_SECONDS = 8
FEIHUALING_DIFFICULTY_SCORE_MULTIPLIER = {5: 1.0, 10: 1.5, 15: 2.0}
FEIHUALING_BASE_SCORE = 10
FEIHUALING_COMBO_BONUS = [0, 0, 2, 4, 6, 8, 10, 12, 15, 18, 20]

WORK_PUBLISH_EXP_MIN = 4
WORK_PUBLISH_EXP_MAX = 16
WORK_PUBLISH_PUNCTUATION = set(string.punctuation + "，。！？、；：”“‘’（）《》【】—…·")


def calculate_feihualing_score(target_rounds: int, response_time: int, combo: int) -> int:
    multiplier = FEIHUALING_DIFFICULTY_SCORE_MULTIPLIER.get(target_rounds, 1.0)
    time_bonus = max(0, (30 - max(0, response_time))) // 5
    combo_idx = min(max(combo, 0), len(FEIHUALING_COMBO_BONUS) - 1)
    combo_bonus = FEIHUALING_COMBO_BONUS[combo_idx]
    return int((FEIHUALING_BASE_SCORE + time_bonus + combo_bonus) * multiplier)


def calculate_feihualing_exp(score_gained: int) -> int:
    return max(0, int(score_gained * FHL_EXP_RATE))


def calculate_relay_rewards(total_score: int) -> Dict[str, int]:
    return {
        "exp": max(0, int(total_score * RELAY_EXP_RATE)),
        "points": max(0, int(total_score * RELAY_POINTS_RATE))
    }


def calculate_challenge_rewards() -> Dict[str, int]:
    return {
        "exp": CHALLENGE_BASE_EXP,
        "points": CHALLENGE_BASE_POINTS
    }


def calculate_learning_exp(action: str, is_first_view: bool, duration: int = 0) -> int:
    if action != "view" or not is_first_view or duration < LEARNING_MIN_DURATION_SECONDS:
        return 0
    return LEARNING_EXP_PER_POEM


TIMED_CHALLENGE_EXP_BASE = {"easy": 1.0, "medium": 1.5, "hard": 2.0}


def calculate_timed_challenge_exp(correct: int, total: int, difficulty: str, max_combo: int) -> int:
    if correct == 0:
        return 0
    base = correct * 2
    multiplier = TIMED_CHALLENGE_EXP_BASE.get(difficulty, 1.0)
    accuracy_bonus = 3 if total > 0 and correct / total >= 0.8 else 0
    combo_bonus = min(max_combo, 5)
    return max(1, int((base + accuracy_bonus + combo_bonus) * multiplier))


def calculate_work_publish_exp(content: str, genre: Optional[str] = None) -> int:
    normalized_lines = [line.strip() for line in content.replace("\r\n", "\n").split("\n") if line.strip()]
    if not normalized_lines:
        return WORK_PUBLISH_EXP_MIN

    char_count = sum(
        1
        for line in normalized_lines
        for char in line
        if not char.isspace() and char not in WORK_PUBLISH_PUNCTUATION
    )
    length_bonus = min(char_count // 14, 5)

    if genre in {"五言绝句", "七言绝句"}:
        structure_bonus = 3 if len(normalized_lines) >= 4 else 1
    elif genre in {"五言律诗", "七言律诗"}:
        structure_bonus = 5 if len(normalized_lines) >= 8 else 2
    elif genre == "词":
        structure_bonus = 4 if len(normalized_lines) >= 4 else 2
    elif genre == "自由体":
        structure_bonus = 3 if len(normalized_lines) >= 3 else 1
    else:
        structure_bonus = min(len(normalized_lines), 3)

    exp = 4 + length_bonus + structure_bonus
    return max(WORK_PUBLISH_EXP_MIN, min(exp, WORK_PUBLISH_EXP_MAX))
