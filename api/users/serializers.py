from rest_framework import serializers
from users.models import Users, UserDetails, GrantHistories


class UserSerializer(serializers.Serializer):
  class Meta:
    model = Users
    fields = ('company', 'user_id', 'password', 'status')

  def save(self, validated_data, date_now, user):
    return Users.objects.create(
      company = user.company,
      user_id = validated_data.get('user_id'),
      password = validated_data.get('password'),
      status = validated_data.get('status'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )

  def update(self, instance, validated_data, date_now, user):
    instance.user_id = validated_data.get('user_id', instance.user_id)
    instance.password = validated_data.get('password', instance.password)
    instance.status = validated_data.get('status', instance.status)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

  def updatePassword(self, instance, validated_data):
    instance.password = validated_data.get('password', instance.password)
    instance.save()

    return instance


class UserDetailsSerializer(serializers.Serializer):
  class Meta:
    model = UserDetails
    fields = ('id', 'first_name', 'last_name', 'first_name_kana', 'last_name_kana', 'auth', 'date_of_birth', 'joining_date', 'reference_date', 'working_days', 'user_id')

  def save(self, validated_data, date_now, user):
    return UserDetails.objects.create(
      user_id = validated_data.get('user_id'),
      first_name = validated_data.get('first_name'),
      last_name = validated_data.get('last_name'),
      first_name_kana = validated_data.get('first_name_kana'),
      last_name_kana = validated_data.get('last_name_kana'),
      auth = validated_data.get('auth'),
      date_of_birth = validated_data.get('date_of_birth'),
      joining_date = validated_data.get('joining_date'),
      reference_date = validated_data.get('reference_date'),
      working_days = validated_data.get('working_days'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )

  def update(self, instance, validated_data, date_now, user):
    instance.first_name = validated_data.get('first_name', instance.first_name)
    instance.last_name = validated_data.get('last_name', instance.last_name)
    instance.first_name_kana = validated_data.get('first_name_kana', instance.first_name_kana)
    instance.last_name_kana = validated_data.get('last_name_kana', instance.last_name_kana)
    instance.auth = validated_data.get('auth', instance.auth)
    instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
    instance.joining_date = validated_data.get('joining_date', instance.joining_date)
    instance.reference_date = validated_data.get('reference_date', instance.reference_date)
    instance.working_days = validated_data.get('working_days', instance.working_days)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance


class GrantHistorySerializer(serializers.Serializer):
  class Meta:
    model = GrantHistories
    fields = ('id', 'user_id', 'add_date', 'extinction_date', 'elapsed_month', 'add_days', 'total_delete_time', 'total_delete_time_hour_unit')

  def save(self, validated_data, date_now, user):
    return GrantHistories.objects.create(
      user_id = validated_data.get('user_id'),
      add_date = validated_data.get('add_date'),
      extinction_date = validated_data.get('extinction_date'),
      elapsed_month = validated_data.get('elapsed_month'),
      add_days = validated_data.get('add_days'),
      # total_delete_time = validated_data.get('total_delete_time'),
      # total_delete_time_hour_unit = validated_data.get('total_delete_time_hour_unit'),
      version = 1,
      created_date = date_now,
      created_user = user.id,
      updated_date = date_now,
      updated_user = user.id,
    )

  def update(self, instance, validated_data, date_now, user):
    instance.add_days = validated_data.get('add_days', instance.add_days)
    instance.total_delete_time = validated_data.get('total_delete_time', instance.total_delete_time)
    instance.total_delete_time_hour_unit = validated_data.get('total_delete_time_hour_unit', instance.total_delete_time_hour_unit)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance