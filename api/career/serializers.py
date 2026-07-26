from rest_framework import serializers

from users.models import Users
from career.models import Careers
from career.models import CareerItems
from career.models import CareerMaster

class CareerSerializer(serializers.ModelSerializer):
  # ユーザID
  user_id = Users.id
  # 案件名
  project_name = serializers.CharField()
  # 概要
  overview = serializers.CharField(required=False, allow_null=True)
  # 開始年月日
  start_date = serializers.DateField(required=False, allow_null=False)
  # 終了年月日
  end_date = serializers.DateField(required=False, allow_null=False)

  class Meta:
    model = Careers
    fields = ('user_id', 'project_name', 'overview', 'start_date', 'end_date')

  def save(self, validated_data, date_now, user):
    return Careers.objects.create(
      user_id = validated_data.get('user_id'),
      project_name = validated_data.get('project_name'),
      overview = validated_data.get('overview'),
      start_date = validated_data.get('start_date'),
      end_date = validated_data.get('end_date'), 
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )

  def update(self, instance, validated_data, date_now, user):
    instance.project_name = validated_data.get('project_name', instance.project_name)
    instance.overview = validated_data.get('overview', instance.overview)
    instance.start_date = validated_data.get('start_date', instance.start_date)
    instance.end_date = validated_data.get('end_date', instance.end_date)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance

class CareerItemSerializer(serializers.ModelSerializer):
  # 経歴情報ID
  career_id = Careers.id
  # キー
  key = serializers.CharField()
  # 値
  value = serializers.CharField()

  class Meta:
    model = CareerItems
    fields = ('career_id', 'key', 'value')

  def save(self, validated_data, career_id, date_now, user):
    career_item = CareerItems(
      career_id = career_id,
      key = validated_data.get('key'),
      value = validated_data.get('value'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )
    career_item.save()

  def update(self, instance, validated_data, date_now, user):
    instance.key = validated_data.get('key', instance.key)
    instance.value = validated_data.get('value', instance.value)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance


class CareerMasterSerializer(serializers.ModelSerializer):
  # 会社ID
  company_id = serializers.IntegerField()
  # キー
  key = serializers.CharField()
  # 値
  value = serializers.CharField()

  class Meta:
    model = CareerMaster
    fields = ('company_id', 'key', 'value')

  def save(self, validated_data, date_now, user):
    career_master = CareerMaster(
      company_id = user.company.id,
      key = validated_data.get('key'),
      value = validated_data.get('value'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )
    career_master.save()

    return career_master

  def update(self, instance, validated_data, date_now, user):
    instance.value = validated_data.get('value')
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance