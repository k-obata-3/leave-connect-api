from django.db import models
from config.models import BaseModel
from systemsettings.models import Companies
from users.models import Users

""" 経歴情報モデル """
class Careers(BaseModel):
  class Meta:
    db_table = "careers"

  # ID
  id = models.BigAutoField(primary_key=True)
  # ユーザID
  user = models.ForeignKey(Users, on_delete=models.CASCADE)
  # 案件名
  project_name = models.CharField(blank=False, null=False, max_length=50)
  # 概要
  overview = models.CharField(blank=True, null=True, max_length=100)
  # 開始年月日
  start_date = models.DateTimeField(blank=False, null=False)
  # 終了年月日
  end_date = models.DateTimeField(blank=False, null=False)


""" 経歴情報項目モデル """
class CareerItems(BaseModel):
  class Meta:
    db_table = "career_items"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 経歴情報ID
  career = models.ForeignKey(Careers, on_delete=models.CASCADE)
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
  company = models.ForeignKey(Companies, on_delete=models.CASCADE)
  # キー
  key = models.CharField(blank=False, null=False, max_length=50)
  # 値
  value = models.CharField(blank=False, null=False, max_length=100)
  # 開始日
  start_date = models.DateTimeField(blank=False, null=True)
  # 終了日
  end_date = models.DateTimeField(blank=False, null=True)
