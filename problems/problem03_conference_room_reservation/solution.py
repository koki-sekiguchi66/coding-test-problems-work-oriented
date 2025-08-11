import sys

class Time:
    """時刻を管理するクラス"""
    def __init__(self, time_str):
        parts = time_str.split(':')
        self.hour = int(parts[0])
        self.minute = int(parts[1])
    
    def __str__(self):
        return f"{self.hour:02d}:{self.minute:02d}"
    
    def __eq__(self, other):
        return self.hour == other.hour and self.minute == other.minute
    
    def __lt__(self, other):
        return self.to_minutes() < other.to_minutes()
    
    def __le__(self, other):
        return self.to_minutes() <= other.to_minutes()
    
    def to_minutes(self):
        """00:00からの経過分数を返す"""
        return self.hour * 60 + self.minute
    
    def is_15_minute_interval(self):
        """15分単位かチェック"""
        return self.minute % 15 == 0
    
    def is_business_hours(self):
        """営業時間内かチェック（09:00以上18:00未満）"""
        return 9 * 60 <= self.to_minutes() < 18 * 60
    
    def duration_minutes(self, end_time):
        """終了時刻との差を分で返す"""
        return end_time.to_minutes() - self.to_minutes()

class Date:
    """日付を管理するクラス"""
    def __init__(self, date_str):
        parts = date_str.split('-')
        self.year = int(parts[0])
        self.month = int(parts[1])
        self.day = int(parts[2])
    
    def __str__(self):
        return f"{self.year}-{self.month:02d}-{self.day:02d}"
    
    def __eq__(self, other):
        return self.year == other.year and self.month == other.month and self.day == other.day
    
    def __lt__(self, other):
        if self.year != other.year:
            return self.year < other.year
        if self.month != other.month:
            return self.month < other.month
        return self.day < other.day
    
    def __le__(self, other):
        return self == other or self < other
    
    def get_weekday(self):
        """曜日を取得（0=月曜日, 6=日曜日）"""
        # ツェラーの公式を使用
        year = self.year
        month = self.month
        day = self.day
        
        if month < 3:
            month += 12
            year -= 1
        
        q = day
        m = month
        k = year % 100
        j = year // 100
        
        h = (q + ((13 * (m + 1)) // 5) + k + (k // 4) + (j // 4) - 2 * j) % 7
        
        # ツェラーの公式では土曜日が0、日曜日が1なので調整
        return (h + 5) % 7
    
    def is_business_day(self):
        """平日かチェック（月〜金）"""
        return self.get_weekday() < 5
    
    def add_days(self, days):
        """指定日数後の日付を返す"""
        # 月ごとの日数
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        year = self.year
        month = self.month
        day = self.day + days
        
        while day > self._get_days_in_month(year, month):
            day -= self._get_days_in_month(year, month)
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        return Date(f"{year}-{month:02d}-{day:02d}")
    
    def _get_days_in_month(self, year, month):
        """指定年月の日数を返す"""
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if month == 2 and self._is_leap_year(year):
            return 29
        return days_in_month[month - 1]
    
    def _is_leap_year(self, year):
        """うるう年かチェック"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

class DateTime:
    """日時を管理するクラス"""
    def __init__(self, date, time):
        self.date = date if isinstance(date, Date) else Date(date)
        self.time = time if isinstance(time, Time) else Time(time)
    
    def __str__(self):
        return f"{self.date} {self.time}"
    
    def __eq__(self, other):
        return self.date == other.date and self.time == other.time
    
    def __lt__(self, other):
        if self.date != other.date:
            return self.date < other.date
        return self.time < other.time
    
    def __le__(self, other):
        return self == other or self < other
    
    def is_overlapping(self, other_start, other_end):
        """時間帯が重複するかチェック"""
        return not (other_end <= self or other_start >= DateTime(self.date, self.time))

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
        duration = start_datetime.time.duration_minutes(end_datetime.time)
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
        return (start_datetime.date.is_business_day() and 
                end_datetime.date.is_business_day() and
                start_datetime.time.is_business_hours() and 
                end_datetime.time.is_business_hours())
    
    def _is_15_minute_intervals(self, start_datetime, end_datetime):
        """15分単位かチェック"""
        return (start_datetime.time.is_15_minute_interval() and 
                end_datetime.time.is_15_minute_interval())
    
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
        bookings_created = 0
        current_date = start_date
        target_weekday = start_date.get_weekday()
        
        while current_date <= end_date:
            if current_date.get_weekday() == target_weekday:
                start_datetime = DateTime(current_date, start_time)
                end_datetime = DateTime(current_date, end_time)
                
                # バリデーション
                error = self.system.validator.validate(employee_id, room_id, start_datetime, end_datetime, participants)
                if error:
                    return error, 0
                
                # 予約作成
                self.system._create_booking(employee_id, room_id, start_datetime, end_datetime, participants)
                bookings_created += 1
            
            current_date = current_date.add_days(1)
        
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
        start_date_obj = Date(start_date)
        end_date_obj = Date(end_date)
        start_time_obj = Time(start_time)
        end_time_obj = Time(end_time)
        
        error, bookings_created = self.recurring_generator.generate_weekly_bookings(
            employee_id, room_id, start_time_obj, end_time_obj, participants, start_date_obj, end_date_obj
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
        target_date = Date(date_str)
        print(f"ROOM_STATUS {room_id} {date_str}:")
        
        # 指定日の予約を取得
        day_bookings = self._get_room_bookings_for_date(room_id, target_date)
        
        if not day_bookings:
            print("No bookings")
            return
        
        # 時刻順にソート
        day_bookings.sort(key=lambda b: b.start_datetime.time.to_minutes())
        
        for booking in day_bookings:
            employee_name = self.employees[booking.employee_id].name
            print(f"{booking.start_datetime.time}-{booking.end_datetime.time}: {booking.id} ({employee_name}, {booking.participants}人)")
    
    def list_employee(self, employee_id, start_date, end_date):
        """社員の予約一覧を表示"""
        start_date_obj = Date(start_date)
        end_date_obj = Date(end_date)
        print(f"EMPLOYEE_BOOKINGS {employee_id}:")
        
        # 期間内の予約を取得
        employee_bookings = self._get_employee_bookings_for_period(employee_id, start_date_obj, end_date_obj)
        
        if not employee_bookings:
            print("No bookings")
            return
        
        # 日時順にソート
        employee_bookings.sort(key=lambda b: (b.start_datetime.date.year, b.start_datetime.date.month, 
                                            b.start_datetime.date.day, b.start_datetime.time.to_minutes()))
        
        for booking in employee_bookings:
            print(f"{booking.start_datetime.date} {booking.start_datetime.time}-{booking.end_datetime.time}: {booking.room_id} ({booking.participants}人) {booking.id}")
    
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
                    booking.start_datetime.date == target_date)]
    
    def _get_employee_bookings_for_period(self, employee_id, start_date, end_date):
        """指定社員の指定期間の予約を取得"""
        return [booking for booking in self.bookings.values()
                if (booking.is_active() and 
                    booking.employee_id == employee_id and
                    start_date <= booking.start_datetime.date <= end_date)]

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