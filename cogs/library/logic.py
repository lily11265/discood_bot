import random
from utils.library_data import load_library_data, save_library_data

def roll_dice():
    """1d100 굴리기"""
    return random.randint(1, 100)

def select_random_book():
    """
    가중치 랜덤 선택:
    많이 선택된 책일수록 확률 감소.
    W = 1 / (select_count + 1)
    """
    books = load_library_data()
    if not books: return None

    weights = [1.0 / (book.get("select_count", 0) + 1) for book in books]
    
    # random.choices는 모집단에서 weights에 따라 k개 선택
    selected = random.choices(books, weights=weights, k=1)[0]
    
    # 선택 횟수 증가 및 저장
    selected["select_count"] = selected.get("select_count", 0) + 1
    
    # 리스트 내 객체가 변경되었으므로 전체 저장 필요 
    # (selected는 books 내부의 dict 참조이므로 books 저장시 반영됨)
    save_library_data(books)
    
    return selected
