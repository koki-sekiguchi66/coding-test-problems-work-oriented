import sys
from datetime import datetime, timedelta

class DateTime:
    """日時を管理するクラス"""
    def __init__(self, date_str, time_str):
        self.date_str = date_str
        self.time_str = time_str
        self.dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    def __str__(self):
        return f"{self.date_str} {self.time_str}"
    
    def __eq__(self, other):
        return self.dt == other.dt
    
    def __lt__(self, other):
        return self.dt < other.dt
    
    def __le__(self, other):
        return self.dt <= other.dt
    
    def is_business_day(self):
        """平日かチェック（月〜金）"""
        return self.dt.weekday() < 5
    
    def is_business_hours(self):
        """営業時間内かチェック（09:00以上18:00未満）"""
        hour_minutes = self.dt.hour * 60 + self.dt.minute
        return 9 * 60 <= hour_minutes < 18 * 60
    
    def is_15_minute_interval(self):
        """15分単位かチェック"""
        return self.dt.minute % 15 == 0
    
    def duration_minutes(self, other):
        """他のDateTimeとの時間差を分で返す"""
        return int((other.dt - self.dt).total_seconds() / 60)

class Room:
    """会議室を管理するクラス"""
    def __init__(self, room_id, name, capacity, equipment_type):
        self.id = room_id
        self.name = name
        self.capacity = int(capacity)
        self.equipment_type = equipment_type

class Employee:
    """社員を管理するクラス"""
    def __init__(self, employee_id, name, department):
        self.id = employee_id
        self.name = name
        self.department = department

class Booking:
    """予約を管理するクラス"""
    def __init__(self, booking_id, employee_id, room_id, start_datetime, end_datetime, participants):
        self.id = str(booking_id)
        self.employee_id = employee_id
        self.room_id = room_id
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.participants = int(participants)
        self.status = "ACTIVE"
    
    def is_overlapping(self, start_datetime, end_datetime):
        """時間帯が重複するかチェック"""
        return not (self.end_datetime <= start_datetime or end_datetime <= self.start_datetime)
    
    def is_active(self):
        """予約が有効かチェック"""
        return self.status == "ACTIVE"
    
    def cancel(self):
        """予約を取り消し"""
        self.status = "CANCELLED"

class BookingValidator:
    """予約のバリデーションを担当するクラス"""
    def __init__(self, system):
        self.system = system
    
    def validate(self, employee_id, room_id, start_datetime, end_datetime, participants):
        """予約の妥当性をチェック"""
        # 社員の存在確認
        if employee_id not in self.system.employees:
            return f"ERROR: Employee {employee_id} not found"
        
        # 会議室の存在確認
        if room_id not in self.system.rooms:
            return f"ERROR: Room {room_id} not found"
        
        # 営業時間と営業日の確認
        if not self._is_valid_business_time(start_datetime, end_datetime):
            return "ERROR: Booking outside business hours (Mon-Fri 09:00-18:00)"
        
        # 過去の時刻の確認
        if start_datetime < self.system.current_datetime:
            return "ERROR: Cannot book in the past"
        
        # 開始時刻が終了時刻より前かチェック
        if start_datetime >= end_datetime:
            return "ERROR: Start time must be before end time"
        
        # 15分単位の確認
        if not self._is_15_minute_intervals(start_datetime, end_datetime):
            return "ERROR: Time must be in 15-minute intervals"
        
        # 予約時間の確認
        duration = start_datetime.duration_minutes(end_datetime)
        if duration < 30:
            return "ERROR: Minimum booking duration is 30 minutes"
        if duration > 240:
            return "ERROR: Maximum booking duration is 4 hours"
        
        # 収容人数の確認
        room = self.system.rooms[room_id]
        if int(participants) > room.capacity:
            return f"ERROR: Participants exceed room capacity (capacity: {room.capacity})"
        
        # 重複予約の確認
        overlap_error = self._check_overlapping_bookings(employee_id, room_id, start_datetime, end_datetime)
        if overlap_error:
            return overlap_error
        
        return None
    
    def _is_valid_business_time(self, start_datetime, end_datetime):
        """営業時間と営業日をチェック"""
        return (start_datetime.is_business_day() and 
                end_datetime.is_business_day() and
                start_datetime.is_business_hours() and 
                end_datetime.is_business_hours())
    
    def _is_15_minute_intervals(self, start_datetime, end_datetime):
        """15分単位かチェック"""
        return (start_datetime.is_15_minute_interval() and 
                end_datetime.is_15_minute_interval())
    
    def _check_overlapping_bookings(self, employee_id, room_id, start_datetime, end_datetime):
        """重複予約をチェック"""
        for booking in self.system.bookings.values():
            if not booking.is_active():
                continue
            
            if booking.is_overlapping(start_datetime, end_datetime):
                # 会議室の重複
                if booking.room_id == room_id:
                    return f"ERROR: Room {room_id} is already booked for this time"
                # 社員の重複
                if booking.employee_id == employee_id:
                    return f"ERROR: Employee {employee_id} already has a booking for this time"
        
        return None

class RecurringBookingGenerator:
    """繰り返し予約の生成を担当するクラス"""
    def __init__(self, system):
        self.system = system
    
    def generate_weekly_bookings(self, employee_id, room_id, start_time, end_time, participants, start_date, end_date):
        """週次の繰り返し予約を生成"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        bookings_created = 0
        current_dt = start_dt
        target_weekday = start_dt.weekday()
        
        while current_dt <= end_dt:
            if current_dt.weekday() == target_weekday:
                current_date_str = current_dt.strftime("%Y-%m-%d")
                start_datetime = DateTime(current_date_str, start_time)
                end_datetime = DateTime(current_date_str, end_time)
                
                # バリデーション
                error = self.system.validator.validate(employee_id, room_id, start_datetime, end_datetime, participants)
                if error:
                    return error, 0
                
                # 予約作成
                self.system._create_booking(employee_id, room_id, start_datetime, end_datetime, participants)
                bookings_created += 1
            
            current_dt += timedelta(days=1)
        
        return None, bookings_created

class BookingSystem:
    """会議室予約システムのメインクラス"""
    def __init__(self):
        self.current_datetime = None
        self.rooms = {}
        self.employees = {}
        self.bookings = {}
        self.next_booking_id = 10001
        self.validator = BookingValidator(self)
        self.recurring_generator = RecurringBookingGenerator(self)
    
    def set_time(self, date_str, time_str):
        """現在時刻を設定"""
        self.current_datetime = DateTime(date_str, time_str)
    
    def setup_room(self, room_id, name, capacity, equipment_type):
        """会議室を登録"""
        self.rooms[room_id] = Room(room_id, name, capacity, equipment_type)
    
    def setup_employee(self, employee_id, name, department):
        """社員を登録"""
        self.employees[employee_id] = Employee(employee_id, name, department)
    
    def book(self, employee_id, room_id, start_date, start_time, end_date, end_time, participants):
        """単発予約"""
        start_datetime = DateTime(start_date, start_time)
        end_datetime = DateTime(end_date, end_time)
        
        error = self.validator.validate(employee_id, room_id, start_datetime, end_datetime, participants)
        if error:
            print(error)
            return
        
        booking_id = self._create_booking(employee_id, room_id, start_datetime, end_datetime, participants)
        print(f"BOOKING_SUCCESS: {booking_id} booked for {employee_id} in room {room_id} from {start_datetime} to {end_datetime}")
    
    def book_recurring(self, employee_id, room_id, start_time, end_time, participants, start_date, end_date):
        """繰り返し予約"""
        error, bookings_created = self.recurring_generator.generate_weekly_bookings(
            employee_id, room_id, start_time, end_time, participants, start_date, end_date
        )
        
        if error:
            print(error)
            return
        
        print(f"RECURRING_SUCCESS: {bookings_created} bookings created from {start_date} to {end_date}")
    
    def cancel(self, booking_id):
        """予約取り消し"""
        if booking_id not in self.bookings:
            print(f"ERROR: Booking {booking_id} not found")
            return
        
        booking = self.bookings[booking_id]
        if booking.status == "CANCELLED":
            print(f"ERROR: Booking {booking_id} is already cancelled")
            return
        
        booking.cancel()
        print(f"CANCEL_SUCCESS: Booking {booking_id} cancelled")
    
    def status(self, room_id, date_str):
        """会議室の予約状況を表示"""
        print(f"ROOM_STATUS {room_id} {date_str}:")
        
        # 指定日の予約を取得
        day_bookings = self._get_room_bookings_for_date(room_id, date_str)
        
        if not day_bookings:
            print("No bookings")
            return
        
        # 時刻順にソート
        day_bookings.sort(key=lambda b: b.start_datetime.dt)
        
        for booking in day_bookings:
            employee_name = self.employees[booking.employee_id].name
            print(f"{booking.start_datetime.time_str}-{booking.end_datetime.time_str}: {booking.id} ({employee_name}, {booking.participants}人)")
    
    def list_employee(self, employee_id, start_date, end_date):
        """社員の予約一覧を表示"""
        print(f"EMPLOYEE_BOOKINGS {employee_id}:")
        
        # 期間内の予約を取得
        employee_bookings = self._get_employee_bookings_for_period(employee_id, start_date, end_date)
        
        if not employee_bookings:
            print("No bookings")
            return
        
        # 日時順にソート
        employee_bookings.sort(key=lambda b: b.start_datetime.dt)
        
        for booking in employee_bookings:
            print(f"{booking.start_datetime.date_str} {booking.start_datetime.time_str}-{booking.end_datetime.time_str}: {booking.room_id} ({booking.participants}人) {booking.id}")
    
    def _create_booking(self, employee_id, room_id, start_datetime, end_datetime, participants):
        """予約を作成"""
        booking_id = str(self.next_booking_id)
        self.next_booking_id += 1
        
        booking = Booking(booking_id, employee_id, room_id, start_datetime, end_datetime, participants)
        self.bookings[booking_id] = booking
        
        return booking_id
    
    def _get_room_bookings_for_date(self, room_id, target_date):
        """指定会議室の指定日の予約を取得"""
        return [booking for booking in self.bookings.values()
                if (booking.is_active() and 
                    booking.room_id == room_id and 
                    booking.start_datetime.date_str == target_date)]
    
    def _get_employee_bookings_for_period(self, employee_id, start_date, end_date):
        """指定社員の指定期間の予約を取得"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        return [booking for booking in self.bookings.values()
                if (booking.is_active() and 
                    booking.employee_id == employee_id and
                    start_dt <= booking.start_datetime.dt.replace(hour=0, minute=0, second=0, microsecond=0) <= end_dt)]

class CommandProcessor:
    """コマンド処理を管理するクラス"""
    def __init__(self, system):
        self.system = system
        self.commands = {
            "SET_TIME": self.set_time,
            "SETUP_ROOM": self.setup_room,
            "SETUP_EMPLOYEE": self.setup_employee,
            "BOOK": self.book,
            "BOOK_RECURRING": self.book_recurring,
            "CANCEL": self.cancel,
            "STATUS": self.status,
            "LIST_EMPLOYEE": self.list_employee
        }
    
    def set_time(self, *args):
        """SET_TIME date time"""
        self.system.set_time(*args)
    
    def setup_room(self, *args):
        """SETUP_ROOM room_id name capacity equipment_type"""
        self.system.setup_room(*args)
    
    def setup_employee(self, *args):
        """SETUP_EMPLOYEE employee_id name department"""
        self.system.setup_employee(*args)
    
    def book(self, *args):
        """BOOK employee_id room_id start_date start_time end_date end_time participants"""
        self.system.book(*args)
    
    def book_recurring(self, *args):
        """BOOK_RECURRING employee_id room_id start_time end_time participants start_date end_date"""
        self.system.book_recurring(*args)
    
    def cancel(self, *args):
        """CANCEL booking_id"""
        self.system.cancel(*args)
    
    def status(self, *args):
        """STATUS room_id date"""
        self.system.status(*args)
    
    def list_employee(self, *args):
        """LIST_EMPLOYEE employee_id start_date end_date"""
        self.system.list_employee(*args)
    
    def process(self, line):
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
    system = BookingSystem()
    processor = CommandProcessor(system)
    
    # 標準入力からコマンドを読み込み
    for line in sys.stdin:
        processor.process(line)

if __name__ == "__main__":
    main()