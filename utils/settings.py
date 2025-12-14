import json
import os
import logging

logger = logging.getLogger(__name__)

SETTINGS_FILE = "data/settings.json"

DEFAULT_SETTINGS = {
    "fishing_cooldown_hours": 1,
    "price_multiplier_mode": False,  # False: 고정 가격, True: 길이 비례 가격
    "gacha_cooldown_hours": 1,
    "gacha_cost": 100,
    "bribe_max_coin": 100,
    "bribe_max_coin": 100,
    "bribe_fail_rate": 1.5,  # % 단위
    "library_cooldown_hours": 1,
    "library_open": True
}

def load_settings():
    """설정을 로드합니다. 파일이 없으면 기본값을 생성합니다."""
    if not os.path.exists("data"):
        os.makedirs("data")
        
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
        
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"설정 로드 실패: {e}")
        return DEFAULT_SETTINGS

def save_settings(settings):
    """설정을 저장합니다."""
    if not os.path.exists("data"):
        os.makedirs("data")

    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"설정 저장 실패: {e}")
