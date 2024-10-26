from django.db import models
from django.forms.models import model_to_dict


""" 基底モデル """
class BaseModel(models.Model):
  class Meta:
    # マイグレーション時にテーブルを作成しないModelは以下のオプションが必要
    abstract = True

  # バージョン
  version = models.BigIntegerField(default=1, blank=False, null=False)
  # 登録日時
  created_date = models.DateTimeField(auto_now_add=True, null=True)
  # 登録者
  created_user = models.BigIntegerField(blank=False, null=False)
  # 更新日時
  updated_date = models.DateTimeField(auto_now=True, null=True)
  # 更新者
  updated_user = models.BigIntegerField(blank=False, null=False)

  def to_dict(self):
    return model_to_dict(self)
