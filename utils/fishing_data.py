import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from utils.config import (
    SPREADSHEET_URL_METADATA, SCOPES, SERVICE_ACCOUNT_FILE, FISHING_SHEET_NAME
)

logger = logging.getLogger(__name__)
DATA_FILE = "data/fishing_items.json"

def get_google_sheet_client():
    """구글 시트 클라이언트를 생성합니다."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

async def sync_fishing_data():
    """구글 시트에서 낚시 데이터를 가져와 로컬에 저장합니다."""
    logger.info("낚시 데이터 동기화 시작...")
    try:
        gc = get_google_sheet_client()
        sheet = gc.open_by_url(SPREADSHEET_URL_METADATA).worksheet(FISHING_SHEET_NAME)
        
        # 모든 데이터 가져오기 (헤더 포함)
        all_values = sheet.get_all_values()
        
        if not all_values:
            logger.warning("낚시 데이터 시트가 비어있습니다.")
            return

        items = []
        # 첫 번째 행은 헤더로 가정하고 2번째 행부터 처리
        for row in all_values[1:]:
            if len(row) < 3: continue
            
            # A: 아이템 이름, B: 가격, C: 아이템설명
            name = row[0].strip()
            if not name: continue
            
            try:
                price = int(row[1].replace(",", "").strip())
            except ValueError:
                price = 0
                
            description = row[2].strip()
            
            items.append({
                "name": name,
                "price": price,
                "description": description
            })
            
        if not os.path.exists("data"):
            os.makedirs("data")
            
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
            
        logger.info(f"낚시 데이터 동기화 완료: {len(items)}개 아이템")
        return items
        
    except Exception as e:
        logger.error(f"낚시 데이터 동기화 실패: {e}")
        return []

def load_fishing_data():
    """로컬에 저장된 낚시 데이터를 로드합니다."""
    if not os.path.exists(DATA_FILE):
        return []
        
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"낚시 데이터 로드 실패: {e}")
        return []
