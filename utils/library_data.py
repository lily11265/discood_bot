import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from utils.config import (
    SPREADSHEET_URL_METADATA, SCOPES, SERVICE_ACCOUNT_FILE, LIBRARY_SHEET_NAME
)

logger = logging.getLogger(__name__)
DATA_FILE = "data/library_books.json"

def get_sheet_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

async def sync_library_data():
    """도서실 데이터를 구글 시트에서 로컬로 동기화합니다."""
    logger.info("도서실 데이터 동기화 시작")
    try:
        gc = get_sheet_client()
        sheet = gc.open_by_url(SPREADSHEET_URL_METADATA).worksheet(LIBRARY_SHEET_NAME)
        rows = sheet.get_all_values()
        
        # 기존 데이터 로드 (select_count 유지 위해)
        old_data = load_library_data()
        old_map = {item["title"]: item.get("select_count", 0) for item in old_data}
        
        new_items = []
        for r in rows[1:]: # 헤더 스킵
            if len(r) < 2: continue
            title = r[0].strip()
            content = r[1].strip()
            if not title: continue
            
            # select_count 유지는 제목 기준
            count = old_map.get(title, 0)
            
            new_items.append({
                "title": title,
                "content": content,
                "select_count": count
            })
            
        save_library_data(new_items)
        logger.info(f"도서실 동기화 완료: {len(new_items)}권")
        return new_items
    except Exception as e:
        logger.error(f"도서실 동기화 실패: {e}")
        return []

def load_library_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: return []

def save_library_data(items):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"도서실 데이터 저장 실패: {e}")
