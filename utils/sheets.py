
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from itertools import zip_longest
from utils.config import (
    SPREADSHEET_URL_INVENTORY, SPREADSHEET_URL_METADATA, SCOPES, SERVICE_ACCOUNT_FILE,
    INVENTORY_SHEET_NAME, METADATA_SHEET_NAME, METADATA_RANGE, INVENTORY_RANGE, INVENTORY_START_ROW
)
from utils.cache import cache_manager

logger = logging.getLogger(__name__)

# Google Sheets Auth
CREDENTIALS = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(CREDENTIALS)

inventory_sheet = gc.open_by_url(SPREADSHEET_URL_INVENTORY).worksheet(INVENTORY_SHEET_NAME)
metadata_sheet = gc.open_by_url(SPREADSHEET_URL_METADATA).worksheet(METADATA_SHEET_NAME)

async def get_cached_metadata():
    cached_data = await cache_manager.get("user_metadata")
    if cached_data:
        return json.loads(cached_data)

    try:
        metadata_range = metadata_sheet.get(METADATA_RANGE)
        inventory_names = inventory_sheet.get(f"B{INVENTORY_RANGE.split(':')[0][1:]}:B{INVENTORY_RANGE.split(':')[1][1:]}")
    except Exception as e:
        logger.error(f"시트 로딩 실패: {e}")
        return {}

    user_mapping = {}
    for idx, row in enumerate(metadata_range):
        if len(row) < 4 or not row[1]: 
            continue
            
        name = row[0].strip()
        user_id = row[1].strip()
        user_type = row[3].strip()
        
        # Simple name matching or index matching
        inventory_name = "Unknown"
        if idx < len(inventory_names) and inventory_names[idx]:
            inventory_name = inventory_names[idx][0].strip()
            
        # If mismatch, search
        if name != inventory_name:
            matching_idx = next((i for i, r in enumerate(inventory_names) if r and r[0].strip() == name), None)
            if matching_idx is not None:
                inventory_name = inventory_names[matching_idx][0].strip()
                
        user_mapping[user_id] = {
            "user_id": user_id,
            "name": name,
            "inventory_name": inventory_name,
            "type": user_type
        }

    await cache_manager.set("user_metadata", json.dumps(user_mapping), ex=86400)
    return user_mapping

async def get_admin_id():
    admin_id = await cache_manager.get("admin_id")
    if admin_id: return admin_id
    
    val = metadata_sheet.acell("B2").value
    await cache_manager.set("admin_id", val, ex=86400)
    return val

async def get_user_inventory(user_id):
    user_metadata = await get_cached_metadata()
    if user_id not in user_metadata:
        return None
        
    target_name = user_metadata[user_id]["inventory_name"]
    # Read B, C, D columns. 
    # B: Name, C: Coin, D: Item
    data = inventory_sheet.get(INVENTORY_RANGE)
    
    for row in data:
        if not row or not row[0]: continue
        if row[0].strip() == target_name:
            # Ensure row has enough columns
            while len(row) < 3: row.append("")

            try:
                current_coins = int(row[1])
            except (ValueError, TypeError):
                current_coins = 0

            return {
                "user_id": user_id,
                "name": target_name,
                "coins": current_coins,
                "items": row[2].split(",") if row[2] else []
            }
    return None

async def update_user_inventory(user_id, coins=None, items=None):
    user_metadata = await get_cached_metadata()
    if user_id not in user_metadata: return

    target_name = user_metadata[user_id]["inventory_name"]
    data = inventory_sheet.get(INVENTORY_RANGE)
    updated_data = []

    for row in data:
        while len(row) < 3: row.append("")
        
        if row[0].strip() == target_name:
            if coins is not None: row[1] = str(coins)
            if items is not None: row[2] = ",".join(items)
        
        updated_data.append(row[:3]) # Keep only B, C, D

    inventory_sheet.update(values=updated_data, range_name=INVENTORY_RANGE)

async def increment_daily_values():
    """Increments coins by 1 for all alive users at midnight"""
    data = inventory_sheet.get(INVENTORY_RANGE)
    updated_data = []

    for row in data:
        while len(row) < 3: row.append("")
        
        # B: Name, C: Coin, D: Item
        name = row[0].strip()
        items = row[2].split(",") if row[2] else []
        
        # Check death
        if "-사망-" not in items:
            try:
                current_coins = int(row[1])
                row[1] = str(current_coins + 1)
            except (ValueError, TypeError):
                pass # Or set to 1 if you want to initialize
        
        updated_data.append(row[:3])

    inventory_sheet.update(values=updated_data, range_name=INVENTORY_RANGE)

async def get_all_users_inventory():
    """For batch operations"""
    user_metadata = await get_cached_metadata()
    data = inventory_sheet.get(INVENTORY_RANGE)
    users = {}
    
    for row in data:
        if not row or not row[0]: continue
        while len(row) < 3: row.append("")
        
        name = row[0].strip()
        # Find user_id by name
        user_id = next((uid for uid, m in user_metadata.items() if m["inventory_name"] == name), None)
        if user_id:
            try:
                coins = int(row[1])
            except (ValueError, TypeError):
                coins = 0

            users[user_id] = {
                "user_id": user_id,
                "name": name,
                "coins": coins,
                "items": row[2].split(",") if row[2] else []
            }
    return users
