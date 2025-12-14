
# Configuration Constants

# 봇 설정
BOT_TOKEN = ""
SPREADSHEET_URL_INVENTORY = "https://docs.google.com/spreadsheets/d/1JDdxlmo2rIIBJZvGUQ9cdIhpmINwDsl6YdYnu7mHHAo/edit?usp=sharing"
SPREADSHEET_URL_METADATA = "https://docs.google.com/spreadsheets/d/1v5-LocmoOKwLmRdSLoRnktOWkP27brJGwlyLdNN8_rk/edit?usp=sharing"

# Google Sheets 인증
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "service_account.json"

# Inventory Sheet Settings
INVENTORY_SHEET_NAME = "인벤토리"
METADATA_SHEET_NAME = "메타데이터시트"

# Rows
METADATA_RANGE = "A2:D31"
INVENTORY_RANGE = "B7:D36"  # Modified for B, C, D columns
INVENTORY_START_ROW = 7
FISHING_SHEET_NAME = "낚시데이타"
GACHA_SHEET_NAME = "가챠 아이템"
SHOP_SHEET_NAME = "상점 데이터"
LIBRARY_SHEET_NAME = "도서실 책자"
LIBRARY_GUILD_ID = 1448253689142968453
LIBRARY_CHANNEL_ID = 1448259225410080810

# Admin IDs
ADMIN_IDS = [
    "1007172975222603798", 
    "1180364209683439692", 
    "1090546247770832910"
]
