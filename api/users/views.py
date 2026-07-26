import traceback
from datetime import datetime, time
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from monthdelta import monthmod

from config.utils import Utils
from config.responseRenderers import ResponseRenderers
from config.enum import TaskType, TaskAction, TaskActionName, WeekDayName

from authentications.views import JWTAuthentication, IsAuthenticated

from users.models import Users, UserDetails, GrantHistories
from application.models import Tasks
from users.serializers import UserSerializer, UserDetailsSerializer, GrantHistorySerializer


"""
  ログインユーザ情報取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class LoginUserInfoRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    try:
      user_obj = Users.objects.get(id=request.user.id, status=settings.USER_EFFECTIVE_STATUS)
      user_details_obj = UserDetails.objects.get(user=user_obj.id)

      response = Response()
      response.status_code = status.HTTP_200_OK
      result = createUserInfoObj(user_details_obj, '/', True)
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ログインユーザ情報取得中にエラーが発生しました。')

    return response


"""
  ユーザ一覧取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class UserListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.APIException('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.APIException('Invalid Parameter:ofset')

    try:
      total_count = UserDetails.objects.filter(user__company=request.user.company).count()
      user_details_obj = UserDetails.objects.order_by('user_id').filter(user__company=request.user.company)[int(ofset):(int(ofset) + int(limit))]

      results = []
      for obj in user_details_obj:
        user = createUserInfoObj(obj, '/', False)
        results.append(user)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.renderList(results, total_count, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.renderList([], 0, response.status_code, 'ユーザ一覧情報の取得中にエラーが発生しました。')

    return response


"""
  ユーザ情報取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class UserDetailsRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    id = self.request.GET.get('id') if self.request.GET.get('id') else request.user.id

    try:
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company, user__id=id).first()
      results = createUserInfoObj(user_details_obj, '/', True)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ユーザ情報の取得中にエラーが発生しました。')

    return response


"""
  ユーザ名一覧取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class UserNameListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    try:
      user_details_obj = UserDetails.objects.order_by('user_id').filter(user__company=request.user.company)
      results = []
      for obj in user_details_obj:
        results.append({
          'id': obj.id,
          'fullName': obj.last_name + " " + obj.first_name,
          'auth': obj.auth
        })

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ユーザ名情報の取得中にエラーが発生しました。')

    return response


"""
  ユーザ情報更新

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class UpdateUserAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'userId' in request.data:
      raise exceptions.APIException('Invalid Parameter:userId')
    if not 'firstName' in request.data:
      raise exceptions.APIException('Invalid Parameter:firstName')
    if not 'lastName' in request.data:
      raise exceptions.APIException('Invalid Parameter:lastName')
    if not 'firstNameKana' in request.data:
      raise exceptions.APIException('Invalid Parameter:firstNameKana')
    if not 'lastNameKana' in request.data:
      raise exceptions.APIException('Invalid Parameter:lastNameKana')
    if not 'dateOfBirth' in request.data:
      raise exceptions.APIException('Invalid Parameter:dateOfBirth')
    if not 'joiningDate' in request.data:
      raise exceptions.APIException('Invalid Parameter:joiningDate')
    if not 'referenceDate' in request.data:
      raise exceptions.APIException('Invalid Parameter:referenceDate')
    if not 'workingDays' in request.data:
      raise exceptions.APIException('Invalid Parameter:workingDays')
    if not 'auth' in request.data:
      raise exceptions.APIException('Invalid Parameter:auth')
    # if not 'totalDeleteDays' in request.data:
    #   raise exceptions.APIException('Invalid Parameter:totalDeleteDays')
    # if not 'totalAddDays' in request.data:
    #   raise exceptions.APIException('Invalid Parameter:totalAddDays')
    # if not 'totalRemainingDays' in request.data:
    #   raise exceptions.APIException('Invalid Parameter:totalRemainingDays')
    # if not 'totalCarryoverDays' in request.data:
    #   raise exceptions.APIException('Invalid Parameter:totalCarryoverDays')

    user_id = request.data['id']
    req = {
      'first_name': request.data['firstName'],
      'last_name': request.data['lastName'],
      'first_name_kana': request.data['firstNameKana'],
      'last_name_kana': request.data['lastNameKana'],
      'date_of_birth': request.data['dateOfBirth'].replace('/', '-'),
      'joining_date': request.data['joiningDate'].replace('/', '-'),
      'auth': request.data['auth'],
      'reference_date': request.data['referenceDate'].replace('/', '-'),
      'working_days': request.data['workingDays'],
    }

    try:
      with transaction.atomic():
        date_now = Utils.get_now_to_string()
        result_user_details = {}

        if user_id:
          user_details_obj = UserDetails.objects.select_for_update().get(user=user_id)
          update_serializer = UserDetailsSerializer(user_details_obj, data=req)
          if not update_serializer.is_valid():
            raise exceptions.APIException(update_serializer.errors)
          update_serializer.update(user_details_obj, req, date_now, request.user)
          result_user_details = UserDetails.objects.get(user=user_id)
        else:
          user_req = {
            'user_id': request.data['userId'],
            'password': 'dummy',
            'status': settings.USER_EFFECTIVE_STATUS,
          }

          user_serializer = UserSerializer(data=user_req)
          if not user_serializer.is_valid():
            raise exceptions.APIException(user_serializer.errors)
          
          new_user = user_serializer.save(user_req, date_now, request.user)
          user_password_req = {
            'password': Utils.get_password_hash(request.data['password'], new_user)
          }
          user_serializer.updatePassword(new_user, user_password_req)
          req['user_id'] = new_user.id
          serializer = UserDetailsSerializer(data=req)
          if not serializer.is_valid():
            raise exceptions.APIException(serializer.errors)
          serializer.save(req, date_now, request.user)
          result_user_details = UserDetails.objects.get(user=new_user.id)

      result = createUserInfoObj(result_user_details, None, True)
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      if e.args[0] == 1062:
        error_message = '入力されたユーザIDは既に登録されているため利用できません。'
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  休暇付与情報取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""

class GetGrantDaysRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    user_id = self.request.GET.get('userId')
    if not user_id:
      raise exceptions.APIException('Invalid Parameter:userId')

    try:
      # ユーザ詳細情報を取得する
      user_details_obj = UserDetails.objects.get(user_id=user_id)

      # 付与対象の全期間情報を配列で取得
      grant_periods = []
      datetime_now = Utils.get_now_to_datetime()
      for period in Utils.get_grant_period(user_details_obj, datetime_now):
        grant_periods.append({
          'startDate':  period['start_date'].strftime('%Y/%m/%d'),
          'endDate': period['end_date'].strftime('%Y/%m/%d'),
          'months': period['months'],
          'totalYear': "{}年6ヶ月".format(period['months'] // 12) if period['months'] // 12 > 0 else "{}ヶ月".format(period['months']),
          'grantRuleAddDays': period['grant_rule_add_days'],
          'isGranted': period['is_granted'],
          'isValid': period['is_valid'],
        })

      result = {
        'grantPeriods': grant_periods,
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '休暇付与情報の取得中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  付与日数更新

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class UpdateGrantDaysAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'userId' in request.data:
      raise exceptions.APIException('Invalid Parameter:userId')

    try:
      userId = request.data['userId']
      date_now = Utils.get_now_to_string()

      with transaction.atomic():
        user_details_obj = UserDetails.objects.get(user_id=userId)

        # 付与対象の全期間情報を配列で取得
        for period in Utils.get_grant_period(user_details_obj, Utils.get_now_to_datetime()):
          # 付与日未設定の期間の場合、付与日情報を登録する
          if period['is_granted'] is False:
            # 対象期間の申請情報から有給休暇の取得日数を算出
            # total_delete_time = 0
            # total_delete_time_hour_unit = 0
            # period_start_str = period['start_date'].strftime('%Y-%m-%d')
            # period_end_str = period['end_date'].strftime('%Y-%m-%d')
            # where_params = {
            #   'application__user__company': user_details_obj.user.company,
            #   'operation_user_id': user_details_obj.id,
            #   'type': TaskType['APPLICATION'].value,
            #   'action__in': [TaskAction['COMPLETE'].value],
            #   'application__start_date__gte': f'{period_start_str} 00:00:00',  # type: ignore
            #   'application__start_date__lte': f'{period_end_str} 23:59:59',  # type: ignore
            # }
            # application_task_obj = Tasks.objects.filter(**where_params)
            # for task in application_task_obj:
            #   if task.application.classification == settings.APPLICATION_CLASSIFICATION_TIME_VALUE:
            #     total_delete_time_hour_unit += task.application.total_time
            #   else:
            #     total_delete_time += task.application.total_time

            grant_history_req = {
              'user_id': user_details_obj.user.id,
              'add_date': period['start_date'],
              'extinction_date': Utils.sub_day(Utils.add_year(period['start_date'], settings.APPLICATION_CARRYOVER_DEADLINE), 1),
              'elapsed_month': period['months'],
              'add_days': period['grant_rule_add_days'],
              # 'total_delete_time': total_delete_time,
              # 'total_delete_time_hour_unit': total_delete_time_hour_unit,
            }
            grant_history_serializer = GrantHistorySerializer(data=grant_history_req)
            if not grant_history_serializer.is_valid():
              raise exceptions.APIException(grant_history_serializer.errors)

            grant_history_serializer.save(grant_history_req, date_now, self.request.user)

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '付与日数更新処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  パスワード変更

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ChangePasswordAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def post(self, request):
    if not 'oldPassword' in request.data:
      raise exceptions.APIException('Invalid Parameter:oldPassword')
    if not 'newPassword' in request.data:
      raise exceptions.APIException('Invalid Parameter:newPassword')

    old_password = request.data['oldPassword']
    new_password = request.data['newPassword']

    try:
      with transaction.atomic():
        user_obj = Users.objects.select_for_update().get(id=request.user.id)
        if user_obj.password != Utils.get_password_hash(old_password, user_obj):
          raise exceptions.ValidationError('パスワードの照合に失敗しました。')

        req = {
          'password': Utils.get_password_hash(new_password, user_obj)
        }
        date_now = Utils.get_now_to_string()
        serializer = UserSerializer(user_obj, data=req)
        if serializer.is_valid():
          serializer.update(user_obj, req, date_now, request.user)
        else:
          raise exceptions.APIException(serializer.errors)

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = 'パスワード変更処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


# ユーザ情報オブジェクト作成
# 注意：serializerから返却されるのは更新後のインスタンス情報なので、フォーマット等が異なる場合がある
# ex) 日付更新リクエスト後のserializerではリクエストにはタイムゾーンが存在していない場合がある
def createUserInfoObj(user_details: UserDetails, date_separator: None | str, is_get_application: bool):
  is_update_grant = False
  total_add_days = 0
  total_delete_days = 0
  total_delete_time = 0
  total_delete_time_hour_unit = 0
  total_remaining_days = 0
  total = 0
  datetime_now = Utils.get_now_to_datetime()
  # 有効な付与日数を取得
  grant_history_obj = GrantHistories.objects.filter(user=user_details.user.id, extinction_date__gte=datetime_now)

  reference_date_time = datetime.combine(user_details.reference_date, time())
  elapsed_period = Utils.get_elapsed_period(reference_date_time, datetime_now)
  # 現在年に換算した付与対象期間の開始日を算出する
  grant_current_period = Utils.get_grant_current_period(reference_date_time, elapsed_period[1])
  current_grant_history = grant_history_obj.filter(add_date=grant_current_period[0]).first()

  if current_grant_history:
    is_update_grant = True

  # 有効な付与日数が存在する場合
  for grant_history in grant_history_obj:
    # 対象期間の申請情報を取得する
    paid_holiday_application = Utils.get_paid_holiday_application(user_details.user, grant_history.add_date, Utils.add_year(grant_history.add_date, 1), [TaskAction['COMPLETE'].value])
    # 付与日数を合算
    total_add_days += grant_history.add_days
    total += paid_holiday_application['total_delete_time'] + paid_holiday_application['total_delete_time_hour_unit']

    # 取得日数は今年度分のみを計上
    if current_grant_history and paid_holiday_application['start_date'] == current_grant_history.add_date:
      total_delete_days = paid_holiday_application['total_delete_days']
      total_delete_time = paid_holiday_application['total_delete_time']
      total_delete_time_hour_unit = paid_holiday_application['total_delete_time_hour_unit']

    total_delete_days = paid_holiday_application['total_delete_days']
    total_delete_time = paid_holiday_application['total_delete_time']
    total_delete_time_hour_unit = paid_holiday_application['total_delete_time_hour_unit']
    total_remaining_days = total_add_days - Utils.convert_application_hours_to_days(total)

  return {
    'id': user_details.user.id,
    'userId': user_details.user.user_id,
    'companyId': user_details.user.company.id,
    'status': user_details.user.status,
    'firstName': user_details.first_name,
    'lastName': user_details.last_name,
    'firstNameKana': user_details.first_name_kana,
    'lastNameKana': user_details.last_name_kana,
    'dateOfBirth': user_details.date_of_birth if date_separator is None else user_details.date_of_birth.strftime(f'%Y{date_separator}%m{date_separator}%d'),
    'auth': user_details.auth,
    'joiningDate': user_details.joining_date if date_separator is None else user_details.joining_date.strftime(f'%Y{date_separator}%m{date_separator}%d'),
    'referenceDate': user_details.reference_date if date_separator is None else user_details.reference_date.strftime(f'%Y{date_separator}%m{date_separator}%d'),
    'workingDays': user_details.working_days,
    'totalDeleteDays': total_delete_days,
    'totalDeleteTimes': total_delete_time_hour_unit,
    'totalAddDays': total_add_days,
    'totalRemainingDays': total_remaining_days,
    'periodStart': None if grant_current_period is None else grant_current_period[0].strftime('%Y/%m/%d'),
    'periodEnd': None if grant_current_period is None else grant_current_period[1].strftime('%Y/%m/%d'),
    'isUpdateGrant': is_update_grant
  }
