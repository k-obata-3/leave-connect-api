from django.db import models
from config.models import BaseModel
from django.forms.models import model_to_dict

""" 会社モデル """
class Companies(BaseModel):
  class Meta:
    db_table = "companies"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 名前
  name = models.CharField(blank=False, null=False, max_length=255)


""" システム設定モデル """
class SystemSettings(BaseModel):
  class Meta:
    db_table = "system_settings"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 会社ID
  company = models.ForeignKey(Companies, on_delete=models.CASCADE)
  # キー
  key = models.CharField(blank=False, null=False, max_length=255)
  # 値
  value = models.CharField(blank=False, null=False, max_length=10000)
  # 開始日
  start_date = models.DateTimeField(blank=False, null=True)
  # 終了日
  end_date = models.DateTimeField(blank=False, null=True)
