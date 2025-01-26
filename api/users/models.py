from django.db import models
from config.models import BaseModel
from systemsettings.models import Company


""" ユーザモデル """
class User(BaseModel):
  class Meta:
    db_table = "user"
    constraints = [models.UniqueConstraint(fields=["company", "user_id"], name="user_unique")]

  # ID
  id = models.BigAutoField(primary_key=True)
  # 会社ID
  company = models.ForeignKey(Company, on_delete=models.CASCADE)
  # ユーザID
  user_id = models.CharField(blank=False, null=False, max_length=255)
  # パスワード
  password = models.CharField(blank=False, null=False, max_length=255)
  # ステータス
  status = models.BigIntegerField(blank=False, null=False, default=1)

""" ユーザ詳細モデル """
class UserDetails(BaseModel):
  class Meta:
    db_table = "user_details"

  # ID
  id = models.BigAutoField(primary_key=True)
  # ユーザID
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  # 名
  first_name = models.CharField(blank=False, null=False, max_length=100)
  # 姓
  last_name = models.CharField(blank=False, null=False, max_length=100)
  # 名(カナ)
  first_name_kana = models.CharField(blank=False, null=False, max_length=100)
  # 姓(カナ)
  last_name_kana = models.CharField(blank=False, null=False, max_length=100)
  # 生年月日
  date_of_birth = models.DateField(blank=False, null=False)
  # 権限
  auth = models.BigIntegerField(blank=False, null=False, default=0)
  # 入社日
  joining_date = models.DateField(blank=False, null=False)
  # 基準日
  reference_date = models.DateField(blank=False, null=False)
  # 週労働日数
  working_days = models.BigIntegerField(blank=False, null=False, default=0)
  # 消化日数
  total_delete_days = models.DecimalField(blank=False, null=False, max_digits=5, decimal_places=3, default=0)
  # 付与日数
  total_add_days = models.DecimalField(blank=False, null=False, max_digits=5, decimal_places=3, default=0)
  # 残日数
  total_remaining_days = models.DecimalField(blank=False, null=False, max_digits=5, decimal_places=3, default=0)
  # 繰越日数
  total_carryover_days = models.DecimalField(blank=False, null=False, max_digits=5, decimal_places=3, default=0)
  # 最終付与日
  last_grant_date = models.DateTimeField(blank=False, null=True)
