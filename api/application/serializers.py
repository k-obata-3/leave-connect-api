from rest_framework import serializers
from application.models import Application, Task
from config.enum import TaskType

class ApplicationSerializer(serializers.Serializer):
  class Meta:
    model = Application
    fields = ('id', 'user_id', 'type', 'classification', 'application_date', 'start_date', 'end_date', 'total_time', 'approval_group_id', 'remarks')

  def save(self, validated_data, date_now, user):
    return Application.objects.create(
      user = user,
      type = validated_data.get('type'),
      classification = validated_data.get('classification'),
      application_date = validated_data.get('application_date'),
      start_date = validated_data.get('start_date'),
      end_date = validated_data.get('end_date'),
      total_time = validated_data.get('total_time'),
      approval_group_id = validated_data.get('approval_group_id'),
      remarks = validated_data.get('remarks'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )

  def update(self, instance, validated_data, date_now, is_update_application_date):
    instance.type = validated_data.get('type', instance.type)
    instance.classification = validated_data.get('classification', instance.classification)
    if is_update_application_date:
      instance.application_date = validated_data.get('application_date', instance.application_date)
    instance.start_date = validated_data.get('start_date', instance.start_date)
    instance.end_date = validated_data.get('end_date', instance.end_date)
    instance.total_time = validated_data.get('total_time', instance.total_time)
    instance.approval_group_id = validated_data.get('approval_group_id', instance.approval_group_id)
    instance.remarks = validated_data.get('remarks', instance.remarks)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.save()
    return instance

class TaskSerializer(serializers.Serializer):
    class Meta:
      model = Task
      fields = ('id', 'application', 'operation_user_id', 'action', 'type', 'comment', 'status', 'operation_date')

    def save_application_task(self, validated_data, date_now, application, user):
      return Task.objects.create(
        application = application,
        operation_user_id = validated_data.get('operation_user_id'),
        action = validated_data.get('action'),
        type = TaskType['APPLICATION'].value,
        comment = validated_data.get('comment'),
        status = validated_data.get('status'),
        operation_date = validated_data.get('operation_date'),
        version = 1,
        created_date = date_now,
        created_user = user.id,
        updated_date = date_now,
        updated_user = user.id,
      )

    def save_approval_task(self, validated_data, date_now, user):
      return Task.objects.create(
        application_id = validated_data.get('application_id'),
        operation_user_id = validated_data.get('operation_user_id'),
        action = validated_data.get('action'),
        type = TaskType['APPROVAL'].value,
        comment = validated_data.get('comment'),
        status = validated_data.get('status'),
        operation_date = validated_data.get('operation_date'),
        version = 1,
        created_date = date_now,
        created_user = user.id,
        updated_date = date_now,
        updated_user = user.id,
      )

    def update_application_task(self, instance, validated_data, date_now, user, is_update_operation_date):
      instance.action = validated_data.get('action', instance.action)
      instance.comment = validated_data.get('comment', instance.comment)
      instance.status = validated_data.get('status', instance.status)
      if is_update_operation_date is True:
        instance.operation_date = validated_data.get('operation_date', instance.operation_date)
      instance.version = instance.version + 1
      instance.updated_date = date_now
      instance.updated_user = user.id
      instance.save()
      return instance

    def update_approval_task(self, instance, validated_data, date_now, user, is_update_operation_date):
      instance.action = validated_data.get('action', instance.action)
      instance.comment = validated_data.get('comment', instance.comment)
      instance.status = validated_data.get('status', instance.status)
      if is_update_operation_date is True:
        instance.operation_date = validated_data.get('operation_date', instance.operation_date)
      instance.version = instance.version + 1
      instance.updated_date = date_now
      instance.updated_user = user.id
      instance.save()
      return instance
