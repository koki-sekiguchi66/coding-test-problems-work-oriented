import sys
from typing import Dict, List, Tuple, Optional

class Time:
    """時刻を管理するクラス"""
    def __init__(self, time_str: str):
        parts = time_str.split(':')
        self.hour = int(parts[0])
        self.minute = int(parts[1])
    
    def to_minutes(self) -> int:
        """00:00からの経過分数を返す"""
        return self.hour * 60 + self.minute
    
    def is_in_range(self, start_str: str, end_str: str) -> bool:
        """指定された時間範囲内かチェック（start含む、end含まない）"""
        start = Time(start_str)
        end = Time(end_str)
        current = self.to_minutes()
        
        if start.to_minutes() < end.to_minutes():
            # 通常の時間範囲（例：09:00-22:00）
            return start.to_minutes() <= current < end.to_minutes()
        else:
            # 日付をまたぐ時間範囲（例：22:00-06:00）
            return current >= start.to_minutes() or current < end.to_minutes()
    
    def __str__(self):
        return f"{self.hour:02d}:{self.minute:02d}"

class Product:
    """商品を管理するクラス"""
    def __init__(self, product_id: str, name: str, price: int, category: str):
        self.id = product_id
        self.name = name
        self.price = price
        self.category = category

class Store:
    """店舗を管理するクラス"""
    def __init__(self, store_id: str, open_time: str, close_time: str):
        self.id = store_id
        self.open_time = open_time
        self.close_time = close_time
        self.inventory: Dict[str, int] = {}  # product_id -> stock count
    
    def is_open(self, time: Time) -> bool:
        """営業時間内かチェック"""
        return time.is_in_range(self.open_time, self.close_time)
    
    def add_stock(self, product_id: str, quantity: int):
        """在庫を追加"""
        if product_id not in self.inventory:
            self.inventory[product_id] = 0
        self.inventory[product_id] += quantity
    
    def has_stock(self, product_id: str, quantity: int) -> bool:
        """在庫が十分かチェック"""
        return product_id in self.inventory and self.inventory[product_id] >= quantity
    
    def get_stock(self, product_id: str) -> int:
        """在庫数を取得"""
        return self.inventory.get(product_id, 0)
    
    def reduce_stock(self, product_id: str, quantity: int):
        """在庫を減らす"""
        self.inventory[product_id] -= quantity

class Member:
    """会員を管理するクラス"""
    def __init__(self, member_id: str, rank: str, points: int):
        self.id = member_id
        self.rank = rank
        self.points = points
    
    def get_point_rate(self) -> float:
        """ポイント還元率を取得"""
        rates = {
            "REGULAR": 0.01,
            "SILVER": 0.02,
            "GOLD": 0.03,
            "PLATINUM": 0.05
        }
        return rates.get(self.rank, 0)
    
    def use_points(self, amount: int):
        """ポイントを使用"""
        self.points -= amount
    
    def earn_points(self, amount: int):
        """ポイントを獲得"""
        self.points += amount

class OrderSystem:
    """注文システムのメインクラス"""
    def __init__(self):
        self.stores: Dict[str, Store] = {}
        self.products: Dict[str, Product] = {}
        self.members: Dict[str, Member] = {}
    
    def setup_store(self, store_id: str, open_time: str, close_time: str):
        """店舗を登録"""
        self.stores[store_id] = Store(store_id, open_time, close_time)
    
    def setup_product(self, product_id: str, name: str, price: str, category: str):
        """商品を登録"""
        self.products[product_id] = Product(product_id, name, int(price), category)
    
    def setup_member(self, member_id: str, rank: str, points: str):
        """会員を登録"""
        self.members[member_id] = Member(member_id, rank, int(points))
    
    def add_stock(self, store_id: str, product_id: str, quantity: str):
        """在庫を追加"""
        if store_id in self.stores:
            self.stores[store_id].add_stock(product_id, int(quantity))
    
    def calculate_time_discount(self, time: Time, items: List[Tuple[str, int]], 
                               base_total: int) -> Tuple[int, str]:
        """時間帯割引を計算"""
        discount_amount = 0
        discount_type = ""
        
        # 商品カテゴリを集計
        has_food = any(self.products[pid].category == "FOOD" for pid, _ in items)
        has_drink = any(self.products[pid].category == "DRINK" for pid, _ in items)
        
        # モーニング割引（06:00〜10:00）：FOOD 10%OFF
        if time.is_in_range("06:00", "10:00"):
            food_total = sum(self.products[pid].price * qty 
                           for pid, qty in items 
                           if self.products[pid].category == "FOOD")
            morning_discount = int(food_total * 0.1)
            if morning_discount > discount_amount:
                discount_amount = morning_discount
                discount_type = "morning"
        
        # ランチ割引（11:00〜14:00）：FOOD+DRINKで全体15%OFF
        if time.is_in_range("11:00", "14:00") and has_food and has_drink:
            lunch_discount = int(base_total * 0.15)
            if lunch_discount > discount_amount:
                discount_amount = lunch_discount
                discount_type = "lunch"
        
        # ハッピーアワー割引（17:00〜19:00）：DRINK 20%OFF
        if time.is_in_range("17:00", "19:00"):
            drink_total = sum(self.products[pid].price * qty 
                            for pid, qty in items 
                            if self.products[pid].category == "DRINK")
            happy_discount = int(drink_total * 0.2)
            if happy_discount > discount_amount:
                discount_amount = happy_discount
                discount_type = "happy"
        
        # 深夜割引（22:00〜06:00）：全商品5%OFF
        if time.is_in_range("22:00", "06:00"):
            night_discount = int(base_total * 0.05)
            if night_discount > discount_amount:
                discount_amount = night_discount
                discount_type = "night"
        
        return base_total - discount_amount, discount_type
    
    def apply_coupon(self, coupon_code: str, items: List[Tuple[str, int]], 
                    current_total: int) -> Tuple[int, bool]:
        """クーポンを適用"""
        if coupon_code == "NONE":
            return current_total, True
        
        # FIXED_金額
        if coupon_code.startswith("FIXED_"):
            try:
                discount = int(coupon_code[6:])
                return max(0, current_total - discount), True
            except:
                return current_total, False
        
        # PERCENT_割合
        if coupon_code.startswith("PERCENT_"):
            try:
                percent = int(coupon_code[8:])
                discount = int(current_total * percent / 100)
                return current_total - discount, True
            except:
                return current_total, False
        
        # CATEGORY_カテゴリ_割合
        if coupon_code.startswith("CATEGORY_"):
            parts = coupon_code.split('_')
            if len(parts) == 3:
                category = parts[1]
                try:
                    percent = int(parts[2])
                    # カテゴリ別の合計を計算（時間帯割引後の価格で）
                    category_total = 0
                    for pid, qty in items:
                        if self.products[pid].category == category:
                            # 時間帯割引後の単価を推定（簡略化のため、全体の割引率を適用）
                            discount_rate = current_total / sum(self.products[p].price * q for p, q in items)
                            discounted_price = int(self.products[pid].price * discount_rate)
                            category_total += discounted_price * qty
                    
                    discount = int(category_total * percent / 100)
                    return current_total - discount, True
                except:
                    return current_total, False
        
        return current_total, False
    
    def process_order(self, time_str: str, store_id: str, member_id: str, 
                     items_str: str, coupon_code: str, use_points: str) -> str:
        """注文を処理"""
        time = Time(time_str)
        use_points = int(use_points)
        
        # 1. 店舗の存在確認
        if store_id not in self.stores:
            return f"{time_str} ERROR: Store {store_id} not found"
        
        store = self.stores[store_id]
        
        # 2. 営業時間の確認
        if not store.is_open(time):
            return f"{time_str} ERROR: Store {store_id} is closed"
        
        # 3. 商品の解析と存在確認
        items = []
        for item_str in items_str.split(','):
            parts = item_str.split(':')
            product_id = parts[0]
            quantity = int(parts[1])
            
            if product_id not in self.products:
                return f"{time_str} ERROR: Product {product_id} not found"
            
            items.append((product_id, quantity))
        
        # 4. 在庫の確認
        for product_id, quantity in items:
            if not store.has_stock(product_id, quantity):
                available = store.get_stock(product_id)
                return f"{time_str} ERROR: Insufficient stock for product {product_id} (requested: {quantity}, available: {available})"
        
        # 5. 会員の確認
        member = None
        if member_id != "GUEST":
            if member_id not in self.members:
                return f"{time_str} ERROR: Member {member_id} not found"
            member = self.members[member_id]
            
            # 6. ポイント残高の確認
            if use_points > 0 and member.points < use_points:
                return f"{time_str} ERROR: Insufficient points (requested: {use_points}, available: {member.points})"
        
        # 7. 価格計算
        # 基本価格の計算
        base_total = sum(self.products[pid].price * qty for pid, qty in items)
        
        # 時間帯割引の適用
        total_after_time_discount, _ = self.calculate_time_discount(time, items, base_total)
        
        # クーポン割引の適用
        total_after_coupon, coupon_valid = self.apply_coupon(coupon_code, items, total_after_time_discount)
        if not coupon_valid:
            return f"{time_str} ERROR: Invalid coupon code {coupon_code}"
        
        # ポイント使用
        actual_points_used = min(use_points, total_after_coupon)
        final_total = max(0, total_after_coupon - actual_points_used)
        
        # ポイント付与計算
        points_earned = 0
        if member:
            points_earned = int(final_total * member.get_point_rate())
        
        # 8. 在庫の更新
        for product_id, quantity in items:
            store.reduce_stock(product_id, quantity)
        
        # 9. ポイントの更新
        if member:
            if actual_points_used > 0:
                member.use_points(actual_points_used)
            if points_earned > 0:
                member.earn_points(points_earned)
        
        return f"{time_str} ORDER_SUCCESS: Total={final_total}, Points_Earned={points_earned}, Points_Used={actual_points_used}"

class CommandProcessor:
    """コマンド処理を管理するクラス"""
    def __init__(self, system: OrderSystem):
        self.system = system
        self.commands = {
            "SETUP_STORE": self.setup_store,
            "SETUP_PRODUCT": self.setup_product,
            "SETUP_MEMBER": self.setup_member,
            "ADD_STOCK": self.add_stock,
            "ORDER": self.order
        }
    
    def setup_store(self, *args):
        """SETUP_STORE store_id open_time close_time"""
        self.system.setup_store(*args)
    
    def setup_product(self, *args):
        """SETUP_PRODUCT product_id name price category"""
        self.system.setup_product(*args)
    
    def setup_member(self, *args):
        """SETUP_MEMBER member_id rank points"""
        self.system.setup_member(*args)
    
    def add_stock(self, *args):
        """ADD_STOCK store_id product_id quantity"""
        self.system.add_stock(*args)
    
    def order(self, *args):
        """ORDER time store_id member_id items coupon_code use_points"""
        result = self.system.process_order(*args)
        print(result)
    
    def process(self, line: str):
        """コマンドラインを処理"""
        if not line.strip():
            return
        
        parts = line.strip().split()
        if not parts:
            return
        
        command = parts[0]
        args = parts[1:]
        
        if command in self.commands:
            self.commands[command](*args)

def main():
    system = OrderSystem()
    processor = CommandProcessor(system)
    
    # 標準入力からコマンドを読み込み
    for line in sys.stdin:
        processor.process(line)

if __name__ == "__main__":
    main()