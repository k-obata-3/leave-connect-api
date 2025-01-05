from rest_framework import serializers
from users.models import User, UserDetails


class UserSerializer(serializers.Serializer):
  class Meta:
    model = User
    fields = ('company', 'user_id', 'password', 'status')

  def update(self, instance, validated_data, date_now, user):
    instance.user_id = validated_data.get('user_id', instance.user_id)
    instance.password = validated_data.get('password', instance.password)
    instance.status = validated_data.get('status', instance.status)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance

  # def save(self, validated_data, login_user, company_id):
    # return User.objects.create(
    #   company = Company.objects.get(pk = company_id),
    #   mail_address = validated_data.get('mail_address'),
    #   password = validated_data.get('password'),
    #   authority = validated_data.get('authority'),
    #   state = validated_data.get('state'),
    #   add_user = login_user.id,
    #   ud_user = login_user.id
    # )

class UserDetailsSerializer(serializers.Serializer):
  class Meta:
    model = UserDetails
    fields = ('id', 'first_name', 'last_name', 'auth', 'reference_date', 'working_days', 'total_delete_days', 'total_add_days', 'total_remaining_days', 'total_carryover_days', 'last_grant_date', 'user_id')

  def update(self, instance, validated_data, date_now, user):
    instance.first_name = validated_data.get('first_name', instance.first_name)
    instance.last_name = validated_data.get('last_name', instance.last_name)
    instance.auth = validated_data.get('auth', instance.auth)
    instance.reference_date = validated_data.get('reference_date', instance.reference_date)
    instance.working_days = validated_data.get('working_days', instance.working_days)
    instance.total_delete_days = validated_data.get('total_delete_days', instance.total_delete_days)
    instance.total_add_days = validated_data.get('total_add_days', instance.total_add_days)
    instance.total_remaining_days = validated_data.get('total_remaining_days', instance.total_remaining_days)
    instance.total_carryover_days = validated_data.get('total_carryover_days', instance.total_carryover_days)
    instance.last_grant_date = validated_data.get('last_grant_date', instance.last_grant_date)
    instance.version = instance.version + 1
    instance.updated_date = date_now
    instance.updated_user = user.id
    instance.save()

    return instance