import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from utils.config import (
    SPREADSHEET_URL_METADATA, SCOPES, SERVICE_ACCOUNT_FILE, GACHA_SHEET_NAME
)

logger = logging.getLogger(__name__)
DATA_FILE = "data/gacha_items.json"

def get_google_sheet_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

async def sync_gacha_data():
    """구글 시트에서 가챠 데이터를 가져와 로컬에 저장합니다."""
    logger.info("가챠 데이터 동기화 시작...")
    try:
        gc = get_google_sheet_client()
        sheet = gc.open_by_url(SPREADSHEET_URL_METADATA).worksheet(GACHA_SHEET_NAME)
        
        all_values = sheet.get_all_values()
        
        if not all_values:
            logger.warning("가챠 데이터 시트가 비어있습니다.")
            return []

        items = []
        # 첫 번째 행은 헤더로 가정
        for row in all_values[1:]:
            if len(row) < 2: continue
            
            # A: 아이템 이름, B: 아이템 설명
            name = row[0].strip()
            if not name: continue
            
            description = row[1].strip()
            
            items.append({
                "name": name,
                "description": description
            })
            
        if not os.path.exists("data"):
            os.makedirs("data")
            
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
            
        logger.info(f"가챠 데이터 동기화 완료: {len(items)}개 아이템")
        return items
        
    except Exception as e:
        logger.error(f"가챠 데이터 동기화 실패: {e}")
        return []

def load_gacha_data():
    """로컬에 저장된 가챠 데이터를 로드합니다."""
    if not os.path.exists(DATA_FILE):
        return []
        
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"가챠 데이터 로드 실패: {e}")
        return []
