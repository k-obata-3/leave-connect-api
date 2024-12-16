from rest_framework import serializers
from config.models import BaseModel
from systemsettings.models import SystemConfigs

class SystemConfigsSerializer(serializers.Serializer):
  class Meta:
    model = SystemConfigs
    fields = ('id', 'company', 'key', 'value')

  def save(self, validated_data, date_now, user):
    return SystemConfigs.objects.create(
      company = validated_data.get('company'),
      key = validated_data.get('key'),
      value = validated_data.get('value'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )

  def update(self, instance, validated_data, date_now, user):
    instance.value = validated_data.get('value', instance.value)
    instance.version = instance.version + 1
    instance.updated_user = user.id
    instance.updated_date = date_now
    instance.save()
    return instance
