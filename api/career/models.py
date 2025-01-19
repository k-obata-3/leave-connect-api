from django.db import models
from config.models import BaseModel
from systemsettings.models import Company
from users.models import User

""" 経歴情報モデル """
class Career(BaseModel):
  class Meta:
    db_table = "career"

  # ID
  id = models.BigAutoField(primary_key=True)
  # ユーザID
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  # 案件名
  project_name = models.CharField(blank=False, null=False, max_length=50)
  # 概要
  overview = models.CharField(blank=True, null=True, max_length=100)
  # 開始年月日
  start_date = models.DateTimeField(blank=False, null=False)
  # 終了年月日
  end_date = models.DateTimeField(blank=False, null=False)

""" 経歴情報項目モデル """
class CareerItem(BaseModel):
  class Meta:
    db_table = "career_item"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 経歴情報ID
  career = models.ForeignKey(Career, on_delete=models.CASCADE)
  # キー
  key = models.CharField(blank=False, null=False, max_length=50)
  # 値
  value = models.CharField(blank=False, null=False, max_length=100)

""" マスタ項目モデル """
class CareerMaster(BaseModel):
  class Meta:
    db_table = "career_master"
    constraints = [models.UniqueConstraint(fields=["company", "key", "value"], name="career_master_unique")]

  # ID
  id = models.BigAutoField(primary_key=True)
  # 会社ID
  company = models.ForeignKey(Company, on_delete=models.CASCADE)
  # キー
  key = models.CharField(blank=False, null=False, max_length=50)
  # 値
  value = models.CharField(blank=False, null=False, max_length=100)
  # 開始日
  start_date = models.DateTimeField(blank=False, null=True)
  # 終了日
  end_date = models.DateTimeField(blank=False, null=True)