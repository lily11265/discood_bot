import logging
from collections import Counter
from utils.shop_data import load_shop_items, save_shop_items
from utils.fishing_data import load_fishing_data
from utils.sheets import update_user_inventory

logger = logging.getLogger(__name__)

def get_fishing_item_info(name):
    """낚시 아이템 정보 조회"""
    items = load_fishing_data()
    for item in items:
        if item["name"] == name: return item
    return None

async def process_sell(interaction, inv, item_name, amount_str):
    """판매 로직 처리"""
    if item_name == "전부":
        try:
            f_data = load_fishing_data()
            f_names = [f["name"] for f in f_data]
            
            sell_list = []
            current_items = inv["items"][:]
            new_items = []
            total_gain = 0
            
            cnt = Counter(current_items)
            sold_details = []
            
            for i_name, count in cnt.items():
                info = get_fishing_item_info(i_name)
                if info: 
                    price = info["price"]
                    total_gain += price * count
                    sold_details.append(f"{i_name} x{count}")
                else:
                    new_items.extend([i_name] * count)
            
            await update_user_inventory(inv["user_id"], coins=inv["coins"] + total_gain, items=new_items)
            await interaction.response.send_message(f"낚시 아이템을 모두 판매했습니다! (+{total_gain}코인)\n목록: {', '.join(sold_details)}")
            
        except Exception as e:
            logger.error(f"전체 판매 오류: {e}")
            await interaction.response.send_message("판매 중 오류가 발생했습니다.", ephemeral=True)
        return

    try:
        qty = int(amount_str)
        if qty <= 0: raise ValueError
    except:
        await interaction.response.send_message("수량은 자연수여야 합니다.", ephemeral=True)
        return

    cnt = inv["items"].count(item_name)
    if cnt < qty:
        await interaction.response.send_message(f"보유 수량이 부족합니다. (보유: {cnt}개)", ephemeral=True)
        return

    info = get_fishing_item_info(item_name)
    if not info:
            await interaction.response.send_message("판매할 수 없는 아이템입니다.", ephemeral=True)
            return

    new_items = inv["items"][:]
    for _ in range(qty):
        new_items.remove(item_name)
        
    gain = info["price"] * qty
    await update_user_inventory(inv["user_id"], coins=inv["coins"] + gain, items=new_items)
    await interaction.response.send_message(f"{item_name} {qty}개를 판매하여 {gain}코인을 획득했습니다.")

async def process_buy(interaction, inv, item_name, amount_str):
    """구매 로직 처리"""
    try:
        qty = int(amount_str)
        if qty <= 0: raise ValueError
    except:
        await interaction.response.send_message("수량은 자연수여야 합니다.", ephemeral=True)
        return

    shop_items = load_shop_items()
    target = next((x for x in shop_items if x["name"] == item_name), None)
    
    if not target:
        await interaction.response.send_message("상점에 없는 물건입니다.", ephemeral=True)
        return
        
    if target["quantity"] < qty:
        await interaction.response.send_message(f"재고가 부족합니다. (남은 수량: {target['quantity']}개)", ephemeral=True)
        return
        
    cost = target["price"] * qty
    if inv["coins"] < cost:
        await interaction.response.send_message(f"코인이 부족합니다. (필요: {cost}, 보유: {inv['coins']})", ephemeral=True)
        return
        
    target["quantity"] -= qty
    save_shop_items(shop_items)
    
    new_items = inv["items"] + [item_name] * qty
    await update_user_inventory(inv["user_id"], coins=inv["coins"] - cost, items=new_items)
    
    item_str = ",".join([item_name] * qty)
    await interaction.response.send_message(f"{item_name} {qty}개를 구매했습니다! (-{cost}코인)\n획득: {item_str}")
