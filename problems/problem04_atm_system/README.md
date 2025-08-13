評価7

## 問題概要

あなたは、銀行のATM取引管理システムを作成することになった。このシステムは、顧客からの各種取引要求を受け付け、口座残高を管理し、取引履歴を記録し、セキュリティチェックを行うことが主な役割である。

顧客は、ATMを通じて預金、引出し、振込、残高照会などの取引を行う。取引時には口座番号とPINコードによる認証が必要であり、一定回数認証に失敗すると口座がロックされる。また、各取引には制限があり、1日の引出し限度額や振込限度額が設定されている。

このシステムの特徴として、時間帯による手数料体系が実装される。平日昼間、平日夜間・早朝、土日祝日によって異なる手数料が適用される。また、VIP会員制度により、一定の条件を満たす顧客は手数料が優遇される。

システムは24時間稼働するが、メンテナンス時間（毎日23:30〜00:30）は全ての取引が停止される。また、大口取引（100万円以上）は平日の9:00〜15:00のみ受け付ける。

上記の説明では、細かい仕様や具体的な入出力方式はまだ書かれていないことに注意せよ。下記の「詳細な仕様」に基づいて、ATM取引を適切に処理し、正確な残高管理を行うプログラムを実装せよ。

## 詳細な仕様

### 時刻

与えられる時刻は、以下の制約とフォーマットを満たす。

- 時刻は HH:MM 形式で与えられる。00:00 ≤ HH:MM ≤ 23:59 が保証される。
- 曜日の判定において、土曜日（5）、日曜日（6）は休日として扱う。
- メンテナンス時間は毎日23:30〜00:30とする。

### 口座

口座は以下の情報を持つ。

- 口座番号: 7桁の数字。1000000から9999999までの値を取る。
- 口座名義: 文字列。日本語を含むことができる。
- PINコード: 4桁の数字。0000から9999までの値を取る。
- 残高: 0以上の整数（円）。
- 口座種別: NORMAL（一般）、VIP（VIP会員）のいずれか。
- ロック状態: ACTIVE（正常）、LOCKED（ロック中）のいずれか。
- 認証失敗回数: 0以上の整数。3回失敗でロックされる。
- 当日引出し累計: 当日の引出し合計金額。
- 当日振込累計: 当日の振込合計金額。

### 取引制限

以下の制限が適用される。

#### 引出し制限
- 一般口座: 1日50万円まで
- VIP口座: 1日100万円まで
- 1回の引出し: 最大20万円まで
- 最小引出し金額: 1,000円
- 引出し単位: 1,000円単位

#### 振込制限
- 一般口座: 1日100万円まで
- VIP口座: 1日300万円まで
- 1回の振込: 最大100万円まで
- 最小振込金額: 1円
- 大口振込（100万円以上）: 平日9:00〜15:00のみ

#### その他制限
- 預金: 1回最大100万円まで、最小1円
- 残高照会: 制限なし

### 手数料体系

取引手数料は以下の通りである。

#### 時間帯区分
- 平日昼間: 月〜金 08:00〜18:00
- 平日夜間・早朝: 月〜金 18:00〜08:00
- 土日祝日: 土日終日

#### 手数料一覧

**引出し手数料**
- 平日昼間: 一般110円、VIP無料
- 平日夜間・早朝: 一般220円、VIP110円
- 土日祝日: 一般220円、VIP110円

**振込手数料**
- 同行宛（平日昼間）: 一般110円、VIP無料
- 同行宛（平日夜間・早朝）: 一般220円、VIP110円
- 同行宛（土日祝日）: 一般220円、VIP110円
- 他行宛（平日昼間）: 一般440円、VIP220円
- 他行宛（平日夜間・早朝）: 一般550円、VIP330円
- 他行宛（土日祝日）: 一般550円、VIP330円

**預金・残高照会**
- 手数料無料

### VIP会員の条件

以下のいずれかを満たす口座はVIP会員として扱われる。
- 口座種別がVIPに設定されている
- 残高が500万円以上（取引時点で判定）

### 営業時間とメンテナンス

- 通常営業: 24時間（メンテナンス時間除く）
- メンテナンス時間: 毎日23:30〜00:30
- 大口取引受付時間: 平日9:00〜15:00

### 取引処理の流れ

システムが取引要求を受け取ったら、以下の順序で処理を行う。

1. **メンテナンス時間の確認**: 現在時刻がメンテナンス時間でないか確認する。
2. **口座の存在確認**: 指定された口座番号が登録されているか確認する。
3. **口座ロック状態の確認**: 口座がロックされていないか確認する。
4. **PIN認証**: PINコードが正しいか確認する。認証失敗時は失敗回数を増加させる。
5. **取引種別による個別チェック**: 各取引固有の制限をチェックする。
6. **手数料計算**: 時間帯と口座種別に応じた手数料を計算する。
7. **取引実行**: 残高更新、累計金額更新、取引履歴記録を行う。

### エラー処理

以下の場合はエラーメッセージを出力し、取引を実行しない。

- メンテナンス時間中の場合  
  `ERROR: System is under maintenance (23:30-00:30)`

- 口座が存在しない場合  
  `ERROR: Account [口座番号] not found`

- 口座がロックされている場合  
  `ERROR: Account [口座番号] is locked`

- PIN認証失敗の場合  
  `ERROR: Invalid PIN code`

- 残高不足の場合  
  `ERROR: Insufficient balance (available: [利用可能額], required: [必要額])`

- 引出し限度額超過の場合  
  `ERROR: Daily withdrawal limit exceeded (limit: [限度額], attempted: [金額])`

- 振込限度額超過の場合  
  `ERROR: Daily transfer limit exceeded (limit: [限度額], attempted: [金額])`

- 大口取引時間外の場合  
  `ERROR: Large amount transactions only available on weekdays 09:00-15:00`

- 金額が無効な場合  
  `ERROR: Invalid amount`

- 振込先口座が存在しない場合  
  `ERROR: Destination account [口座番号] not found`

### システムの処理順序

システムは毎回の取引要求に対して以下の3ステップの処理をこの順序で行う。

1. **Step 1**: 現在時刻の更新
2. **Step 2**: 取引要求の処理
3. **Step 3**: 結果の出力

### 入出力形式

プログラムに与えられる入力は、標準入力を介して行われる。
改行コードは\n (<LF>)である。最終行の末尾にも改行コードが付与される。
入力は、各種セットアップコマンドと取引コマンドが時系列順に与えられる。コマンドの数は与えられないので標準入力の最終行まで読み込むこと。これらの数は合計で150以下であることが保証される。

### コマンド

#### SET_TIME コマンド

現在時刻を設定する。
```
SET_TIME [時刻] [曜日]
```

例：現在時刻を10:00、曜日を月曜日（0）に設定
```
SET_TIME 10:00 0
```

曜日は0（月）〜6（日）の数字で指定される。

#### SETUP_ACCOUNT コマンド

口座情報を登録する。
```
SETUP_ACCOUNT [口座番号] [口座名義] [PINコード] [残高] [口座種別]
```

例：口座1234567「田中太郎」をPIN1234、残高100万円、一般口座として登録
```
SETUP_ACCOUNT 1234567 田中太郎 1234 1000000 NORMAL
```

#### DEPOSIT コマンド

預金を行う。
```
DEPOSIT [口座番号] [PINコード] [金額]
```

例：口座1234567にPIN1234で5万円を預金
```
DEPOSIT 1234567 1234 50000
```

#### WITHDRAW コマンド

引出しを行う。
```
WITHDRAW [口座番号] [PINコード] [金額]
```

例：口座1234567からPIN1234で3万円を引出し
```
WITHDRAW 1234567 1234 30000
```

#### TRANSFER コマンド

振込を行う。
```
TRANSFER [送金元口座番号] [PINコード] [送金先口座番号] [金額] [他行フラグ]
```

例：口座1234567からPIN1234で口座2345678に5万円を同行振込
```
TRANSFER 1234567 1234 2345678 50000 SAME
```

他行フラグは SAME（同行）、OTHER（他行）のいずれかを指定する。

#### BALANCE コマンド

残高照会を行う。
```
BALANCE [口座番号] [PINコード]
```

例：口座1234567のPIN1234で残高照会
```
BALANCE 1234567 1234
```

#### UNLOCK コマンド

管理者権限で口座のロックを解除する。
```
UNLOCK [口座番号]
```

例：口座1234567のロックを解除
```
UNLOCK 1234567
```

#### RESET_DAILY コマンド

日次リセット（1日の累計金額をリセット）を行う。
```
RESET_DAILY
```

### 出力

#### DEPOSIT コマンド

成功時：
```
[時刻] DEPOSIT_SUCCESS: Account [口座番号], Amount [金額], Balance [残高], Fee [手数料]
```

エラー時：
```
[時刻] ERROR: [エラーメッセージ]
```

#### WITHDRAW コマンド

成功時：
```
[時刻] WITHDRAW_SUCCESS: Account [口座番号], Amount [金額], Balance [残高], Fee [手数料]
```

エラー時：
```
[時刻] ERROR: [エラーメッセージ]
```

#### TRANSFER コマンド

成功時：
```
[時刻] TRANSFER_SUCCESS: From [送金元口座], To [送金先口座], Amount [金額], Fee [手数料]
```

エラー時：
```
[時刻] ERROR: [エラーメッセージ]
```

#### BALANCE コマンド

成功時：
```
[時刻] BALANCE_SUCCESS: Account [口座番号], Balance [残高]
```

エラー時：
```
[時刻] ERROR: [エラーメッセージ]
```

#### UNLOCK コマンド

成功時：
```
[時刻] UNLOCK_SUCCESS: Account [口座番号] unlocked
```

エラー時：
```
[時刻] ERROR: [エラーメッセージ]
```

#### その他

PIN認証に3回失敗した場合：
```
[時刻] ACCOUNT_LOCKED: Account [口座番号] has been locked due to multiple failed attempts
```

セットアップコマンド（SET_TIME、SETUP_ACCOUNT、RESET_DAILY）に対しては出力を行わない。

## テストケース

### テストケース1: 基本的な取引フロー

**入力:**
```
SET_TIME 10:00 1
SETUP_ACCOUNT 1234567 田中太郎 1234 1000000 NORMAL
DEPOSIT 1234567 1234 50000
WITHDRAW 1234567 1234 30000
BALANCE 1234567 1234
```

**期待出力:**
```
10:00 DEPOSIT_SUCCESS: Account 1234567, Amount 50000, Balance 1050000, Fee 0
10:00 WITHDRAW_SUCCESS: Account 1234567, Amount 30000, Balance 1020000, Fee 110
10:00 BALANCE_SUCCESS: Account 1234567, Balance 1020000
```

### テストケース2: PIN認証失敗とアカウントロック

**入力:**
```
SET_TIME 14:00 2
SETUP_ACCOUNT 2345678 佐藤花子 5678 500000 NORMAL
WITHDRAW 2345678 1111 10000
WITHDRAW 2345678 2222 10000
WITHDRAW 2345678 3333 10000
WITHDRAW 2345678 5678 10000
```

**期待出力:**
```
14:00 ERROR: Invalid PIN code
14:00 ERROR: Invalid PIN code
14:00 ACCOUNT_LOCKED: Account 2345678 has been locked due to multiple failed attempts
14:00 ERROR: Account 2345678 is locked
```

### テストケース3: 時間帯による手数料変動とVIP優遇

**入力:**
```
SET_TIME 19:00 3
SETUP_ACCOUNT 3456789 山田VIP 9999 5000000 VIP
SETUP_ACCOUNT 4567890 鈴木一般 1111 500000 NORMAL
WITHDRAW 3456789 9999 50000
WITHDRAW 4567890 1111 50000
```

**期待出力:**
```
19:00 WITHDRAW_SUCCESS: Account 3456789, Amount 50000, Balance 4950000, Fee 110
19:00 WITHDRAW_SUCCESS: Account 4567890, Amount 50000, Balance 450000, Fee 220
```

### テストケース4: 振込取引と他行手数料

**入力:**
```
SET_TIME 11:00 4
SETUP_ACCOUNT 5678901 送金者 1234 300000 NORMAL
SETUP_ACCOUNT 6789012 受取人 5678 100000 NORMAL
TRANSFER 5678901 1234 6789012 100000 SAME
TRANSFER 5678901 1234 6789012 50000 OTHER
```

**期待出力:**
```
11:00 TRANSFER_SUCCESS: From 5678901, To 6789012, Amount 100000, Fee 110
11:00 TRANSFER_SUCCESS: From 5678901, To 6789012, Amount 50000, Fee 440
```

### テストケース5: 限度額超過エラー

**入力:**
```
SET_TIME 12:00 1
SETUP_ACCOUNT 7890123 限度額テスト 1234 800000 NORMAL
WITHDRAW 7890123 1234 300000
WITHDRAW 7890123 1234 300000
```

**期待出力:**
```
12:00 WITHDRAW_SUCCESS: Account 7890123, Amount 300000, Balance 500000, Fee 110
12:00 ERROR: Daily withdrawal limit exceeded (limit: 500000, attempted: 300000)
```

### テストケース6: メンテナンス時間と大口取引制限

**入力:**
```
SET_TIME 23:45 0
SETUP_ACCOUNT 8901234 メンテテスト 1234 2000000 VIP
DEPOSIT 8901234 1234 10000
SET_TIME 16:00 6
TRANSFER 8901234 1234 1234567 1500000 OTHER
```

**期待出力:**
```
23:45 ERROR: System is under maintenance (23:30-00:30)
16:00 ERROR: Large amount transactions only available on weekdays 09:00-15:00
```

### テストケース7: 残高不足と無効金額エラー

**入力:**
```
SET_TIME 09:00 2
SETUP_ACCOUNT 9012345 残高不足 1234 50000 NORMAL
WITHDRAW 9012345 1234 100000
WITHDRAW 9012345 1234 500
DEPOSIT 9012345 1234 0
```

**期待出力:**
```
09:00 ERROR: Insufficient balance (available: 50000, required: 100110)
09:00 ERROR: Invalid amount
09:00 ERROR: Invalid amount
```

### テストケース8: アカウントロック解除と日次リセット

**入力:**
```
SET_TIME 15:00 1
SETUP_ACCOUNT 1111111 ロックテスト 1234 1000000 NORMAL
WITHDRAW 1111111 9999 10000
WITHDRAW 1111111 8888 10000
WITHDRAW 1111111 7777 10000
UNLOCK 1111111
WITHDRAW 1111111 1234 200000
RESET_DAILY
WITHDRAW 1111111 1234 200000
```

**期待出力:**
```
15:00 ERROR: Invalid PIN code
15:00 ERROR: Invalid PIN code
15:00 ACCOUNT_LOCKED: Account 1111111 has been locked due to multiple failed attempts
15:00 UNLOCK_SUCCESS: Account 1111111 unlocked
15:00 WITHDRAW_SUCCESS: Account 1111111, Amount 200000, Balance 800000, Fee 110
15:00 WITHDRAW_SUCCESS: Account 1111111, Amount 200000, Balance 600000, Fee 110
```