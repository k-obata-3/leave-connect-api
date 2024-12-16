from enum import Enum

class NumStatus(Enum):
    ONE = 'いち'
    TWO = 'に'
    THREE = 'さん'

# name or valueでメンバーアクセス
# print(NumStatus('いち').name) #=> 'ONE'
# print(NumStatus('いち').value) #=> 'いち'

# print(NumStatus['ONE'].name) #=> 'ONE'
# print(NumStatus['ONE'].value) #=> 'いち'

"""_summary_
"""
class TaskType(Enum):
  APPLICATION = 0
  APPROVAL = 1

class TaskTypeName(Enum):
  APPLICATION = '申請タスク'
  APPROVAL = '承認タスク'

"""_summary_
"""
class ApplicationType(Enum):
  PAID_HOLIDAY = 0
  NORMAL_HOLIDAY = 1

class ApplicationTypeName(Enum):
  PAID_HOLIDAY = '年次有給休暇申請'
  NORMAL_HOLIDAY = '休暇申請'

"""_summary_
"""
class TaskStatus(Enum):
  NON_ACTIVE = 0
  ACTIVE = 1
  HISTORY = 2
  CLOSED = 3

class TaskStatusName(Enum):
  NON_ACTIVE = '無効'
  ACTIVE = '進行中'
  HISTORY = '履歴'
  CLOSED = '処理済'

"""_summary_
"""
class TaskAction(Enum):
  DRAFT = 0
  PANDING = 1
  APPROVAL = 2
  COMPLETE = 3
  REJECT = 4
  CANCEL = 5
  SYSTEM_CANCEL = 9

class TaskActionName(Enum):
  DRAFT = '下書き'
  PANDING = '承認待ち'
  APPROVAL = '承認'
  COMPLETE = '完了'
  REJECT = '差戻'
  CANCEL = '取消'
  SYSTEM_CANCEL = 'システム取消'

"""_summary_
"""
class ApplicationClassification(Enum):
  ALL_DAYS = 0
  HALF_DAYS_AM = 1
  HALF_DAYS_PM = 2
  TIME = 3

class ApplicationClassificationName(Enum):
  ALL_DAYS = '全日'
  HALF_DAYS_AM = 'AM半休'
  HALF_DAYS_PM = 'PM半休'
  TIME = '時間単位'
