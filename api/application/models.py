from django.db import models
from config.models import BaseModel
from users.models import Users

""" 申請モデル """
class Applications(BaseModel):
  class Meta:
    db_table = "applications"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 申請ユーザID
  user = models.ForeignKey(Users, on_delete=models.CASCADE)
  # 申請タイプ
  type = models.BigIntegerField(blank=False, null=False)
  # 区分
  classification = models.BigIntegerField(blank=False, null=False)
  # 申請日時
  application_date = models.DateTimeField(blank=False, null=False)
  # 開始日時
  start_date = models.DateTimeField(blank=False, null=False)
  # 終了日時
  end_date = models.DateTimeField(blank=False, null=False)
  # 合計時間
  total_time = models.BigIntegerField(blank=False, null=False)
  # 承認グループID
  approval_group_id = models.BigIntegerField(blank=False, null=False)
  # 備考
  remarks = models.CharField(blank=False, null=True, max_length=1000)


""" タスクモデル """
class Tasks(BaseModel):
  class Meta:
    db_table = "tasks"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 申請ID
  application = models.ForeignKey(Applications, on_delete=models.CASCADE)
  # 操作ユーザID
  operation_user = models.ForeignKey(Users, on_delete=models.CASCADE)
  # 操作
  action = models.BigIntegerField(blank=False, null=True)
  # 種類
  type = models.BigIntegerField(blank=False, null=False)
  # コメント
  comment = models.CharField(blank=False, null=True, max_length=1000)
  # ステータス
  status = models.BigIntegerField(blank=False, null=False)
  # 操作日時
  operation_date = models.DateTimeField(blank=False, null=True)
