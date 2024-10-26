from django.db import models
from config.models import BaseModel
from users.models import User


""" 申請モデル """
class Application(BaseModel):
  class Meta:
    db_table = "application"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 申請ユーザID
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  # 申請タイプ
  type = models.BigIntegerField(blank=False, null=False)
  # 区分
  classification = models.BigIntegerField(blank=False, null=False)
  # 申請日時
  application_date = models.DateTimeField(auto_now_add=True, blank=False, null=False)
  # 開始日時
  start_date = models.DateTimeField(blank=False, null=False)
  # 終了日時
  end_date = models.DateTimeField(blank=False, null=False)
  # 合計時間
  total_time = models.BigIntegerField(blank=False, null=False)
  # 承認グループID
  approval_group_id = models.BigIntegerField(blank=False, null=False)


""" タスクモデル """
class Task(BaseModel):
  class Meta:
    db_table = "task"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 申請ID
  application = models.ForeignKey(Application, on_delete=models.CASCADE)
  # 操作ユーザID
  operation_user = models.ForeignKey(User, on_delete=models.CASCADE)
  # 操作
  action = models.BigIntegerField(blank=False, null=True)
  # 種類
  type = models.BigIntegerField(blank=False, null=False)
  # コメント
  comment = models.CharField(blank=False, null=True, max_length=1000)
  # ステータス
  status = models.BigIntegerField(blank=False, null=False)
  # 操作日時
  application_date = models.DateTimeField(blank=False, null=True)
