import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from utils.config import (
    SPREADSHEET_URL_METADATA, SCOPES, SERVICE_ACCOUNT_FILE, SHOP_SHEET_NAME
)
from utils.settings import load_settings, save_settings

logger = logging.getLogger(__name__)
SHOP_FILE = "data/shop_items.json"

def get_sheet_client():
    """구글 시트 인증 및 클라이언트 반환"""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

async def sync_shop_data():
    """상점 데이터를 구글 시트에서 로컬로 동기화합니다."""
    logger.info("상점 데이터 동기화 시작")
    try:
        gc = get_sheet_client()
        sheet = gc.open_by_url(SPREADSHEET_URL_METADATA).worksheet(SHOP_SHEET_NAME)
        rows = sheet.get_all_values()
        
        items = []
        # 헤더 건너뛰고 데이터 파싱
        for r in rows[1:]:
            if len(r) < 4: continue
            name = r[0].strip()
            if not name: continue
            
            try:
                price = int(r[1].replace(",", "").strip())
                qty = int(r[2].replace(",", "").strip())
            except ValueError:
                continue
            
            desc = r[3].strip()
            items.append({
                "name": name, 
                "price": price, 
                "quantity": qty, 
                "description": desc
            })
            
        save_shop_items(items)
        logger.info(f"상점 동기화 완료: {len(items)}개 아이템")
        return items
    except Exception as e:
        logger.error(f"상점 동기화 실패: {e}")
        return []

def load_shop_items():
    """로컬 상점 아이템 로드"""
    if not os.path.exists(SHOP_FILE): return []
    try:
        with open(SHOP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: return []

def save_shop_items(items):
    """로컬 상점 아이템 저장"""
    try:
        with open(SHOP_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"상점 데이터 저장 실패: {e}")

def get_shop_open_status():
    """상점 개장 여부 반환 (기본값 True)"""
    settings = load_settings()
    return settings.get("shop_open", True)

def set_shop_open_status(is_open: bool):
    """상점 개장 여부 설정"""
    settings = load_settings()
    settings["shop_open"] = is_open
    save_settings(settings)
