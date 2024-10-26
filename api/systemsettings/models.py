from django.db import models
from config.models import BaseModel
from django.forms.models import model_to_dict


""" 会社モデル """
class Company(BaseModel):
  class Meta:
    db_table = "company"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 名前
  name = models.CharField(blank=False, null=False, max_length=255)


""" システム設定モデル """
class SystemConfigs(BaseModel):
  class Meta:
    db_table = "system_configs"

  # ID
  id = models.BigAutoField(primary_key=True)
  # 会社ID
  company = models.ForeignKey(Company, on_delete=models.CASCADE)
  # キー
  name = models.CharField(blank=False, null=False, max_length=255)
  # 値
  name = models.CharField(blank=False, null=False, max_length=10000)
