import sys
from datetime import datetime, time

class TimeManager:
    """時刻管理クラス"""
    def __init__(self, time_str, day_of_week):
        self.time_str = time_str
        self.time_obj = datetime.strptime(time_str, "%H:%M").time()
        self.day_of_week = int(day_of_week)  # 0=月曜日, 6=日曜日
    
    def __str__(self):
        return self.time_str
    
    def is_maintenance_time(self):
        """メンテナンス時間（23:30-00:30）かチェック"""
        return (self.time_obj >= time(23, 30) or 
                self.time_obj <= time(0, 30))
    
    def is_weekday(self):
        """平日かチェック"""
        return self.day_of_week < 5
    
    def is_business_hours(self):
        """営業時間（平日9:00-15:00）かチェック"""
        return (self.is_weekday() and 
                time(9, 0) <= self.time_obj <= time(15, 0))
    
    def get_time_zone(self):
        """時間帯区分を取得"""
        if not self.is_weekday():
            return "WEEKEND"
        
        if time(8, 0) <= self.time_obj < time(18, 0):
            return "WEEKDAY_DAYTIME"
        else:
            return "WEEKDAY_NIGHTTIME"

class Account:
    """口座クラス"""
    def __init__(self, account_number, name, pin_code, balance, account_type):
        self.account_number = account_number
        self.name = name
        self.pin_code = pin_code
        self.balance = int(balance)
        self.account_type = account_type
        self.status = "ACTIVE"
        self.failed_attempts = 0
        self.daily_withdrawal = 0
        self.daily_transfer = 0
    
    def is_vip(self):
        """VIP会員かどうか判定"""
        return self.account_type == "VIP" or self.balance >= 5000000
    
    def is_locked(self):
        """口座がロックされているかチェック"""
        return self.status == "LOCKED"
    
    def authenticate(self, pin_code):
        """PIN認証"""
        if self.pin_code == pin_code:
            return True
        
        self.failed_attempts += 1
        if self.failed_attempts >= 3:
            self.status = "LOCKED"
            return "LOCKED"
        return False
    
    def unlock(self):
        """口座ロック解除"""
        self.status = "ACTIVE"
        self.failed_attempts = 0
    
    def reset_daily_limits(self):
        """日次制限リセット"""
        self.daily_withdrawal = 0
        self.daily_transfer = 0

class TransactionValidator:
    """取引バリデーター"""
    
    WITHDRAWAL_LIMITS = {
        "NORMAL": {"daily": 500000, "single": 200000},
        "VIP": {"daily": 1000000, "single": 200000}
    }
    
    TRANSFER_LIMITS = {
        "NORMAL": {"daily": 1000000, "single": 1000000},
        "VIP": {"daily": 3000000, "single": 1000000}
    }
    
    @classmethod
    def validate_withdrawal(cls, account, amount):
        """引出しバリデーション"""
        if amount <= 0:
            return "ERROR: Invalid amount"
        
        if amount < 1000:
            return "ERROR: Invalid amount"
        
        if amount % 1000 != 0:
            return "ERROR: Invalid amount"
        
        account_type = "VIP" if account.is_vip() else "NORMAL"
        limits = cls.WITHDRAWAL_LIMITS[account_type]
        
        if amount > limits["single"]:
            return "ERROR: Invalid amount"
        
        if account.daily_withdrawal + amount > limits["daily"]:
            return f"ERROR: Daily withdrawal limit exceeded (limit: {limits['daily']}, attempted: {amount})"
        
        return None
    
    @classmethod
    def validate_transfer(cls, account, amount, time_manager):
        """振込バリデーション"""
        if amount <= 0:
            return "ERROR: Invalid amount"
        
        account_type = "VIP" if account.is_vip() else "NORMAL"
        limits = cls.TRANSFER_LIMITS[account_type]
        
        if amount > limits["single"]:
            return "ERROR: Invalid amount"
        
        # 大口取引時間チェック
        if amount >= 1000000 and not time_manager.is_business_hours():
            return "ERROR: Large amount transactions only available on weekdays 09:00-15:00"
        
        if account.daily_transfer + amount > limits["daily"]:
            return f"ERROR: Daily transfer limit exceeded (limit: {limits['daily']}, attempted: {amount})"
        
        return None
    
    @classmethod
    def validate_deposit(cls, amount):
        """預金バリデーション"""
        if amount <= 0 or amount > 1000000:
            return "ERROR: Invalid amount"
        return None

class FeeCalculator:
    """手数料計算クラス"""
    
    FEE_TABLE = {
        "NORMAL": {
            "WEEKDAY_DAYTIME": {
                "WITHDRAW": 110,
                "TRANSFER_SAME": 110,
                "TRANSFER_OTHER": 440
            },
            "WEEKDAY_NIGHTTIME": {
                "WITHDRAW": 220,
                "TRANSFER_SAME": 220,
                "TRANSFER_OTHER": 550
            },
            "WEEKEND": {
                "WITHDRAW": 220,
                "TRANSFER_SAME": 220,
                "TRANSFER_OTHER": 550
            }
        },
        "VIP": {
            "WEEKDAY_DAYTIME": {
                "WITHDRAW": 0,
                "TRANSFER_SAME": 0,
                "TRANSFER_OTHER": 220
            },
            "WEEKDAY_NIGHTTIME": {
                "WITHDRAW": 110,
                "TRANSFER_SAME": 110,
                "TRANSFER_OTHER": 330
            },
            "WEEKEND": {
                "WITHDRAW": 110,
                "TRANSFER_SAME": 110,
                "TRANSFER_OTHER": 330
            }
        }
    }
    
    @classmethod
    def calculate_fee(cls, account, transaction_type, time_zone, bank_type=None):
        """手数料計算"""
        if transaction_type in ["DEPOSIT", "BALANCE"]:
            return 0
        
        account_category = "VIP" if account.is_vip() else "NORMAL"
        
        if transaction_type == "WITHDRAW":
            return cls.FEE_TABLE[account_category][time_zone]["WITHDRAW"]
        elif transaction_type == "TRANSFER":
            transfer_key = f"TRANSFER_{bank_type}"
            return cls.FEE_TABLE[account_category][time_zone][transfer_key]
        
        return 0

class ATMSystem:
    """ATMシステムメインクラス"""
    def __init__(self):
        self.accounts = {}
        self.current_time = None
    
    def set_time(self, time_str, day_of_week):
        """現在時刻設定"""
        self.current_time = TimeManager(time_str, day_of_week)
    
    def setup_account(self, account_number, name, pin_code, balance, account_type):
        """口座登録"""
        self.accounts[account_number] = Account(
            account_number, name, pin_code, balance, account_type
        )
    
    def _basic_validation(self, account_number, pin_code):
        """基本バリデーション"""
        # メンテナンス時間チェック
        if self.current_time.is_maintenance_time():
            return "ERROR: System is under maintenance (23:30-00:30)"
        
        # 口座存在チェック
        if account_number not in self.accounts:
            return f"ERROR: Account {account_number} not found"
        
        account = self.accounts[account_number]
        
        # ロック状態チェック
        if account.is_locked():
            return f"ERROR: Account {account_number} is locked"
        
        # PIN認証
        auth_result = account.authenticate(pin_code)
        if auth_result == "LOCKED":
            return "LOCK_TRIGGERED"  # 特別な戻り値
        elif not auth_result:
            return "ERROR: Invalid PIN code"
        
        return None
    
    def deposit(self, account_number, pin_code, amount):
        """預金処理"""
        error = self._basic_validation(account_number, pin_code)
        if error:
            if error == "LOCK_TRIGGERED":
                print(f"{self.current_time} ACCOUNT_LOCKED: Account {account_number} has been locked due to multiple failed attempts")
                return
            print(f"{self.current_time} {error}")
            return
        
        amount = int(amount)
        
        # 金額バリデーション
        validation_error = TransactionValidator.validate_deposit(amount)
        if validation_error:
            print(f"{self.current_time} {validation_error}")
            return
        
        account = self.accounts[account_number]
        time_zone = self.current_time.get_time_zone()
        fee = FeeCalculator.calculate_fee(account, "DEPOSIT", time_zone)
        
        # 残高更新
        account.balance += amount
        
        print(f"{self.current_time} DEPOSIT_SUCCESS: Account {account_number}, Amount {amount}, Balance {account.balance}, Fee {fee}")
    
    def withdraw(self, account_number, pin_code, amount):
        """引出し処理"""
        error = self._basic_validation(account_number, pin_code)
        if error:
            if error == "LOCK_TRIGGERED":
                print(f"{self.current_time} ACCOUNT_LOCKED: Account {account_number} has been locked due to multiple failed attempts")
                return
            print(f"{self.current_time} {error}")
            return
        
        amount = int(amount)
        account = self.accounts[account_number]
        
        # 引出しバリデーション
        validation_error = TransactionValidator.validate_withdrawal(account, amount)
        if validation_error:
            print(f"{self.current_time} {validation_error}")
            return
        
        time_zone = self.current_time.get_time_zone()
        fee = FeeCalculator.calculate_fee(account, "WITHDRAW", time_zone)
        total_required = amount + fee
        
        # 残高チェック
        if account.balance < total_required:
            print(f"{self.current_time} ERROR: Insufficient balance (available: {account.balance}, required: {total_required})")
            return
        
        # 取引実行
        account.balance -= total_required
        account.daily_withdrawal += amount
        
        print(f"{self.current_time} WITHDRAW_SUCCESS: Account {account_number}, Amount {amount}, Balance {account.balance}, Fee {fee}")
    
    def transfer(self, from_account, pin_code, to_account, amount, bank_type):
        """振込処理"""
        error = self._basic_validation(from_account, pin_code)
        if error:
            if error == "LOCK_TRIGGERED":
                print(f"{self.current_time} ACCOUNT_LOCKED: Account {from_account} has been locked due to multiple failed attempts")
                return
            print(f"{self.current_time} {error}")
            return
        
        amount = int(amount)
        
        # 振込先口座チェック
        if to_account not in self.accounts:
            print(f"{self.current_time} ERROR: Destination account {to_account} not found")
            return
        
        from_acc = self.accounts[from_account]
        
        # 振込バリデーション
        validation_error = TransactionValidator.validate_transfer(from_acc, amount, self.current_time)
        if validation_error:
            print(f"{self.current_time} {validation_error}")
            return
        
        time_zone = self.current_time.get_time_zone()
        bank_type_key = "SAME" if bank_type == "SAME" else "OTHER"
        fee = FeeCalculator.calculate_fee(from_acc, "TRANSFER", time_zone, bank_type_key)
        total_required = amount + fee
        
        # 残高チェック
        if from_acc.balance < total_required:
            print(f"{self.current_time} ERROR: Insufficient balance (available: {from_acc.balance}, required: {total_required})")
            return
        
        # 取引実行
        from_acc.balance -= total_required
        from_acc.daily_transfer += amount
        self.accounts[to_account].balance += amount
        
        print(f"{self.current_time} TRANSFER_SUCCESS: From {from_account}, To {to_account}, Amount {amount}, Fee {fee}")
    
    def balance(self, account_number, pin_code):
        """残高照会"""
        error = self._basic_validation(account_number, pin_code)
        if error:
            if error == "LOCK_TRIGGERED":
                print(f"{self.current_time} ACCOUNT_LOCKED: Account {account_number} has been locked due to multiple failed attempts")
                return
            print(f"{self.current_time} {error}")
            return
        
        account = self.accounts[account_number]
        print(f"{self.current_time} BALANCE_SUCCESS: Account {account_number}, Balance {account.balance}")
    
    def unlock(self, account_number):
        """口座ロック解除"""
        if account_number not in self.accounts:
            print(f"{self.current_time} ERROR: Account {account_number} not found")
            return
        
        account = self.accounts[account_number]
        account.unlock()
        print(f"{self.current_time} UNLOCK_SUCCESS: Account {account_number} unlocked")
    
    def reset_daily(self):
        """日次リセット"""
        for account in self.accounts.values():
            account.reset_daily_limits()

class CommandProcessor:
    """コマンド処理クラス"""
    def __init__(self, system):
        self.system = system
        self.commands = {
            "SET_TIME": self.system.set_time,
            "SETUP_ACCOUNT": self.system.setup_account,
            "DEPOSIT": self.system.deposit,
            "WITHDRAW": self.system.withdraw,
            "TRANSFER": self.system.transfer,
            "BALANCE": self.system.balance,
            "UNLOCK": self.system.unlock,
            "RESET_DAILY": self.system.reset_daily
        }
    
    def process(self, line):
        """コマンド処理"""
        if not line.strip():
            return
        
        parts = line.strip().split()
        command = parts[0]
        args = parts[1:]
        
        if command in self.commands:
            self.commands[command](*args)

def main():
    """メイン関数"""
    system = ATMSystem()
    processor = CommandProcessor(system)
    
    for line in sys.stdin:
        processor.process(line)

if __name__ == "__main__":
    main()