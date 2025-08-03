import sys
from functools import total_ordering

@total_ordering
class Time:
    """時刻を管理するクラス"""
    def __init__(self, d, h, m):
        self.d = d
        self.h = h
        self.m = m

    def __str__(self):
        return f"{self.d} {str(self.h).zfill(2)}:{str(self.m).zfill(2)}"

    def step(self):
        """1分進める"""
        self.m += 1
        if self.m == 60:
            self.m = 0
            self.h += 1
        if self.h == 24:
            self.h = 0
            self.d += 1

    def minutes(self):
        """日付1の00:00からの経過分数を返す"""
        return (self.d - 1) * 24 * 60 + self.h * 60 + self.m

    def __eq__(self, other):
        return self.d == other.d and self.h == other.h and self.m == other.m

    def __lt__(self, other):
        return self.minutes() < other.minutes()

    def add(self, minutes):
        """指定した分数だけ進めた新しいTimeオブジェクトを返す"""
        time = Time(self.d, self.h, self.m)
        for _ in range(minutes):
            time.step()
        return time

    @classmethod
    def from_string(cls, day_str, time_str):
        """文字列から Time オブジェクトを作成"""
        day = int(day_str)
        h, m = map(int, time_str.split(":"))
        return cls(day, h, m)

class Request:
    """配達リクエストを管理するクラス"""
    def __init__(self, time, type_, id_, duration, scheduled_time=None):
        self.time = time
        self.type_ = type_
        self.id_ = id_
        self.duration = duration
        self.status = "awaiting"  # awaiting, delivering, delivered
        self.scheduled_time = scheduled_time  # SCHEDULEDタイプの場合の配達予定時刻
        self.completion_time = None  # 配達完了予定時刻

    def is_valid_duration(self):
        """配達時間が有効かチェック"""
        if self.type_ in ["NORMAL", "EXPRESS"]:
            return self.duration <= 120
        elif self.type_ == "SCHEDULED":
            return self.duration <= 60
        return False

    def get_delivery_period(self):
        """SCHEDULED配達の配達時間帯を返す（開始時刻, 終了時刻）"""
        if self.type_ != "SCHEDULED" or not self.scheduled_time:
            return None
        start_time = Time(self.scheduled_time.d, self.scheduled_time.h, self.scheduled_time.m)
        # 配達時間分だけ前に戻る
        for _ in range(self.duration):
            start_time.m -= 1
            if start_time.m < 0:
                start_time.m = 59
                start_time.h -= 1
            if start_time.h < 0:
                start_time.h = 23
                start_time.d -= 1
        return (start_time, self.scheduled_time)

    def __repr__(self):
        return f"Request({self.id_}, {self.type_}, {self.status})"

class Queue:
    """配達リクエストのキューを管理するクラス"""
    def __init__(self):
        self.requests = []

    def add(self, request):
        """リクエストを追加"""
        self.requests.append(request)

    def search_and_remove(self, current_time, busy_periods):
        """条件に合うリクエストを検索して削除"""
        for i, req in enumerate(self.requests):
            if req.status == "awaiting":
                # 忙しい時間帯との重複チェック
                delivery_end = current_time.add(req.duration)
                if not self._is_conflicting_with_busy_periods(current_time, delivery_end, busy_periods):
                    return self.requests.pop(i)
        return None

    def search_earliest_and_remove(self):
        """最も早い時刻のリクエストを検索して削除"""
        if not self.requests:
            return None
        
        earliest_idx = 0
        for i, req in enumerate(self.requests):
            if req.status == "awaiting" and req.time < self.requests[earliest_idx].time:
                earliest_idx = i
        
        if self.requests[earliest_idx].status == "awaiting":
            return self.requests.pop(earliest_idx)
        return None

    def _is_conflicting_with_busy_periods(self, start_time, end_time, busy_periods):
        """忙しい時間帯と重複するかチェック"""
        for busy_start, busy_end in busy_periods:
            if self._time_overlap(start_time, end_time, busy_start, busy_end):
                return True
        return False

    def _time_overlap(self, start1, end1, start2, end2):
        """2つの時間帯が重複するかチェック"""
        return not (end1.minutes() <= start2.minutes() or end2.minutes() <= start1.minutes())

    def remove_by_id(self, delivery_id):
        """IDでリクエストを削除"""
        for i, req in enumerate(self.requests):
            if req.id_ == delivery_id:
                return self.requests.pop(i)
        return None

    def find_by_id(self, delivery_id):
        """IDでリクエストを検索"""
        for req in self.requests:
            if req.id_ == delivery_id:
                return req
        return None

class Postman:
    """配達員を管理するクラス"""
    def __init__(self):
        self.current_request = None

    def assign(self, request):
        """配達リクエストを割り当て"""
        self.current_request = request
        request.status = "delivering"

    def is_available(self):
        """配達員が利用可能かチェック"""
        return self.current_request is None

    def complete_delivery(self):
        """配達完了処理"""
        if self.current_request:
            self.current_request.status = "delivered"
            completed_request = self.current_request
            self.current_request = None
            return completed_request
        return None

class System:
    """配達管理システムのメインクラス"""
    def __init__(self):
        self.postman = Postman()
        self.express_queue = Queue()
        self.normal_queue = Queue()
        self.scheduled_queue = Queue()
        self.all_requests = {}  # delivery_id -> Request のマッピング
        self.busy_periods = []  # (start_time, end_time) のリスト

    def parse_query(self, line):
        """クエリをパース"""
        parts = line.strip().split()
        if len(parts) < 3:
            return None
        
        day = parts[0]
        time_str = parts[1]
        query_type = parts[2]
        
        time_obj = Time.from_string(day, time_str)
        
        if query_type in ["NORMAL", "EXPRESS"]:
            if len(parts) >= 5:
                delivery_id = parts[3]
                duration = int(parts[4])
                return {
                    "type": query_type,
                    "time": time_obj,
                    "delivery_id": delivery_id,
                    "duration": duration
                }
        elif query_type == "SCHEDULED":
            if len(parts) >= 7:
                delivery_id = parts[3]
                duration = int(parts[4])
                scheduled_day = parts[5]
                scheduled_time = parts[6]
                scheduled_time_obj = Time.from_string(scheduled_day, scheduled_time)
                return {
                    "type": query_type,
                    "time": time_obj,
                    "delivery_id": delivery_id,
                    "duration": duration,
                    "scheduled_time": scheduled_time_obj
                }
        elif query_type in ["CANCEL", "STATUS"]:
            if len(parts) >= 4:
                delivery_id = parts[3]
                return {
                    "type": query_type,
                    "time": time_obj,
                    "delivery_id": delivery_id
                }
        
        return None

    def process_delivery_request(self, query):
        """配達リクエストを処理"""
        time_obj = query["time"]
        delivery_id = query["delivery_id"]
        duration = query["duration"]
        query_type = query["type"]
        
        # リクエストオブジェクトを作成
        if query_type == "SCHEDULED":
            request = Request(time_obj, query_type, delivery_id, duration, query["scheduled_time"])
        else:
            request = Request(time_obj, query_type, delivery_id, duration)
        
        # 配達時間のバリデーション
        if not request.is_valid_duration():
            if query_type == "SCHEDULED":
                return f"{time_obj} ERROR: Delivery time cannot exceed 60 minutes."
            else:
                return f"{time_obj} ERROR: Delivery time cannot exceed 120 minutes."
        
        # SCHEDULED配達の追加チェック
        if query_type == "SCHEDULED":
            scheduled_time = query["scheduled_time"]
            
            # 今すぐ配達を始めても間に合わないかチェック
            if scheduled_time.minutes() <= time_obj.minutes() + duration:
                return f"{time_obj} ERROR: The scheduled delivery time is too close."
            
            # 現在配達中のものがある場合のチェック
            if not self.postman.is_available():
                current_end_time = self.postman.current_request.completion_time
                if scheduled_time.minutes() <= current_end_time.minutes() + duration:
                    return f"{time_obj} ERROR: The scheduled delivery time is too close because other delivery is being made."
            
            # 忙しい時間帯との重複チェック
            delivery_period = request.get_delivery_period()
            if delivery_period:
                start_time, end_time = delivery_period
                for busy_start, busy_end in self.busy_periods:
                    if self._time_overlap(start_time, end_time, busy_start, busy_end):
                        return f"{time_obj} ERROR: The scheduled delivery time cannot be specified because the delivery person is busy making another delivery."
                
                # 忙しい時間帯に追加
                self.busy_periods.append((start_time, end_time))
        
        # リクエストを受理
        self.all_requests[delivery_id] = request
        
        # 適切なキューに追加
        if query_type == "EXPRESS":
            self.express_queue.add(request)
        elif query_type == "NORMAL":
            self.normal_queue.add(request)
        elif query_type == "SCHEDULED":
            self.scheduled_queue.add(request)
        
        return f"{time_obj} {delivery_id} has been accepted."

    def process_cancel(self, query):
        """キャンセル処理"""
        time_obj = query["time"]
        delivery_id = query["delivery_id"]
        
        # リクエストが存在するかチェック
        if delivery_id not in self.all_requests:
            return f"{time_obj} ERROR: The request is not found."
        
        request = self.all_requests[delivery_id]
        
        # 配達待ち以外はキャンセルできない
        if request.status != "awaiting":
            return f"{time_obj} ERROR: The request that has been processed cannot be cancelled."
        
        # SCHEDULEDの場合は忙しい時間帯から削除
        if request.type_ == "SCHEDULED":
            delivery_period = request.get_delivery_period()
            if delivery_period and delivery_period in self.busy_periods:
                self.busy_periods.remove(delivery_period)
        
        # 各キューから削除
        self.express_queue.remove_by_id(delivery_id)
        self.normal_queue.remove_by_id(delivery_id)
        self.scheduled_queue.remove_by_id(delivery_id)
        
        # 全体のリクエストからも削除
        del self.all_requests[delivery_id]
        
        return f"{time_obj} {delivery_id} has been cancelled."

    def process_status(self, query):
        """ステータス確認処理"""
        time_obj = query["time"]
        delivery_id = query["delivery_id"]
        
        # リクエストが存在するかチェック
        if delivery_id not in self.all_requests:
            return f"{time_obj} ERROR: The request is not found."
        
        request = self.all_requests[delivery_id]
        
        if request.status == "awaiting":
            return f"{time_obj} {delivery_id} is awaiting delivery."
        elif request.status == "delivering":
            return f"{time_obj} {delivery_id} is being delivered."
        elif request.status == "delivered":
            return f"{time_obj} {delivery_id} has been delivered."

    def check_completion(self, current_time):
        """配達完了をチェック"""
        if not self.postman.is_available():
            current_request = self.postman.current_request
            if current_request and current_request.completion_time and current_request.completion_time == current_time:
                completed_request = self.postman.complete_delivery()
                return f"{current_time} {completed_request.id_} has been delivered."
        return None

    def assign_delivery(self, current_time):
        """配達リクエストの割り当て"""
        if not self.postman.is_available():
            return None
        
        # SCHEDULED配達のチェック
        for req in self.scheduled_queue.requests:
            if req.status == "awaiting" and req.scheduled_time:
                # 現在時刻から配達時間後が配達予定時刻と一致するかチェック
                expected_completion = current_time.add(req.duration)
                if expected_completion == req.scheduled_time:
                    self.scheduled_queue.remove_by_id(req.id_)
                    req.completion_time = expected_completion
                    self.postman.assign(req)
                    return f"{current_time} {req.id_} has been assigned."
        
        # EXPRESS配達のチェック
        express_req = self.express_queue.search_and_remove(current_time, self.busy_periods)
        if express_req:
            express_req.completion_time = current_time.add(express_req.duration)
            self.postman.assign(express_req)
            return f"{current_time} {express_req.id_} has been assigned."
        
        # NORMAL配達のチェック
        normal_req = self.normal_queue.search_and_remove(current_time, self.busy_periods)
        if normal_req:
            normal_req.completion_time = current_time.add(normal_req.duration)
            self.postman.assign(normal_req)
            return f"{current_time} {normal_req.id_} has been assigned."
        
        return None

    def _time_overlap(self, start1, end1, start2, end2):
        """2つの時間帯が重複するかチェック"""
        return not (end1.minutes() <= start2.minutes() or end2.minutes() <= start1.minutes())

    def process_query(self, query):
        """クエリを処理"""
        if query["type"] in ["NORMAL", "EXPRESS", "SCHEDULED"]:
            return self.process_delivery_request(query)
        elif query["type"] == "CANCEL":
            return self.process_cancel(query)
        elif query["type"] == "STATUS":
            return self.process_status(query)
        
        return None

def main():
    system = System()
    
    # 入力を読み込み
    queries = []
    for line in sys.stdin:
        if line.strip():
            query = system.parse_query(line)
            if query:
                queries.append(query)
    

    
    
    current_time = Time(1, 0, 0)
    query_index = 0
        
        # システム実行中フラグ
    running = True
        
    while running:
            # Step 1: 配達完了チェック
        completion_msg = system.check_completion(current_time)
        if completion_msg:
            print(completion_msg)
            
            # Step 2: クエリ処理
        if query_index < len(queries) and queries[query_index]["time"] == current_time:
            query_result = system.process_query(queries[query_index])
            if query_result:
                print(query_result)
            query_index += 1
            
            # Step 3: 配達割り当て
        assignment_msg = system.assign_delivery(current_time)
        if assignment_msg:
            print(assignment_msg)
            
            # 次の時刻へ
        current_time.step()
            
            # 終了条件: 全クエリ処理済み かつ 配達員が空いている かつ キューが空
        if (query_index >= len(queries) and 
            system.postman.is_available() and 
            len(system.express_queue.requests) == 0 and 
            len(system.normal_queue.requests) == 0 and 
            len(system.scheduled_queue.requests) == 0):
            running = False

if __name__ == '__main__':
    main()