from enum import Enum


"""_summary_
"""
class TaskType(Enum):
  APPLICATION = 0   #申請タスク
  APPROVAL = 1      #承認タスク

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
