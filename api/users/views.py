import traceback
import json
import datetime
import math
from decimal import Decimal
from django.db.models import Q
from django.db import transaction
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from config.utils import Utils
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from config.enum import TaskType, TaskStatus, TaskAction

from authentications.views import JWTAuthentication

from users.models import User, UserDetails
from systemsettings.models import SystemConfigs
from application.models import Task
from users.serializers import UserSerializer, UserDetailsSerializer


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
  permission_classes = [IsAuthenticated]

  def get(self, request):
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.APIException('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.APIException('Invalid Parameter:ofset')

    try:
      total_count = UserDetails.objects.filter(user__company=request.user.company).count()
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company)[int(ofset):(int(ofset) + int(limit))]

      date_now = Utils.get_now_to_datetime()
      results = []
      for obj in user_details_obj:
        user = createUserInfoObj(obj, '/')
        user['periodStart'] = None
        user['periodEnd'] = None
        user['isUpdateGrant'] = False

        # 基準日から現在日時までの通算月数を算出する(現在日時 - 基準日)
        # 算出した通算月数が0以上の場合、継続勤続期間が6ヶ月以上と見做す
        passedyears = Utils.get_service_years(obj.reference_date, date_now)
        if passedyears[1] >= 0:
          # 現在年に換算した付与対象期間の開始日、終了日を算出する
          grant_period = getGrantPeriod(obj.reference_date, passedyears[1])
          period_start = grant_period[0]
          period_end = grant_period[1]
          is_update_grant = is_update_grant_date(obj.last_grant_date, period_start, period_end)
          user['periodStart'] = period_start.strftime('%Y/%m/%d')
          user['periodEnd'] = period_end.strftime('%Y/%m/%d')
          user['isUpdateGrant'] = is_update_grant

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
  permission_classes = [IsAuthenticated]

  def get(self, request):
    id = self.request.GET.get('id') if self.request.GET.get('id') else request.user.id

    try:
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company, user__id=id).first()
      results = createUserInfoObj(user_details_obj, '/')

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
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company)
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
    if not 'id' in request.data:
      raise exceptions.APIException('Invalid Parameter:id')
    if not 'firstName' in request.data:
      raise exceptions.APIException('Invalid Parameter:firstName')
    if not 'lastName' in request.data:
      raise exceptions.APIException('Invalid Parameter:lastName')
    if not 'referenceDate' in request.data:
      raise exceptions.APIException('Invalid Parameter:referenceDate')
    if not 'workingDays' in request.data:
      raise exceptions.APIException('Invalid Parameter:workingDays')
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
      # 'auth': request.data['auth'],
      'reference_date': request.data['referenceDate'].replace('/', '-'),
      'working_days': request.data['workingDays'],
    }

    try:
      with transaction.atomic():
        user_details_obj = UserDetails.objects.select_for_update().get(user=user_id)

        date_now = Utils.get_now_to_string()
        serializer = UserDetailsSerializer(user_details_obj, data=req)
        if serializer.is_valid():
          serializer.update(user_details_obj, req, date_now, request.user)
        else:
          raise exceptions.APIException(serializer.error_messages['invalid'])

        result_user_details = UserDetails.objects.get(user=user_id)

      result = createUserInfoObj(result_user_details, None)
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '更新処理中にエラーが発生しました。')

    return response


"""
  付与日数取得

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
    id = self.request.GET.get('id')
    if not id:
      raise exceptions.APIException('Invalid Parameter:id')

    HALF_YEAR_MONTH = 6
    YEAR_MONTH = 12
    try:
      warnings = []
      valid_errors= []
      # date_now = datetime.datetime(2024, 5, 1)    # テスト用
      date_now = Utils.get_now_to_datetime()
      total_delete_days_after_value = 0       # 更新後 取得日数
      total_remaining_days_after_value = ''   # 更新後 残日数
      total_carryover_days_after_value = ''   # 更新後 繰越日数
      total_add_days_after_value = ''         # 更新後 付与日数

      user_details_obj = UserDetails.objects.get(user_id=id)

      # 基準日から現在日時までの通算月数を算出する(現在日時 - 基準日)
      # 算出した通算月数が0以上の場合、継続勤続期間が6ヶ月以上と見做す
      passedyears = Utils.get_service_years(user_details_obj.reference_date, date_now)
      is_total_service_year_half_over = passedyears[1] >= 0

      # 現在年に換算した付与対象期間の開始日、終了日を算出する
      grant_period = getGrantPeriod(user_details_obj.reference_date, passedyears[1])
      period_start = grant_period[0]
      period_end = grant_period[1]

      # 継続勤続期間が6ヶ月以上の場合
      if is_total_service_year_half_over:
        # 最終更新日から対象期間内の更新有無をチェック
        if is_update_grant_date(user_details_obj.last_grant_date, period_start, period_end):
          warnings.append('対象期間内に付与日が更新済みです。')
        else:
          warnings.append('対象期間内に付与日が更新されていません。')

        # 対象期間(念のため前年申請分も含めてお知らせするために-1年する)に未完了(承認待ち、差戻)の申請情報がないかチェック
        period_start_str = Utils.sub_year(period_start, 1).strftime('%Y-%m-%d')
        period_end_str = period_end.strftime('%Y-%m-%d')
        where_params = {
          'application__user__company': request.user.company,
          'operation_user_id': user_details_obj.id,
          'type': TaskType['APPLICATION'].value,
          'action__in': [TaskAction['PANDING'].value, TaskAction['REJECT'].value],
          'status__in': [TaskStatus['ACTIVE'].value],
          'application__start_date__gte': f'{period_start_str} 00:00:00',  # type: ignore
          'application__start_date__lte': f'{period_end_str} 23:59:59',  # type: ignore
        }
        application_task_obj = Task.objects.filter(**where_params)
        if application_task_obj:
          warnings.append('未完了(承認待ち、差戻)の申請情報が存在します。')
          warnings.append('※期間: ' + period_start_str.replace('-', '/') + ' ～ ' + period_end_str.replace('-', '/') + '、申請ID: ' + str(list(application_task_obj.values_list('application__id', flat=True))))

        # 付与ルールを取得する
        start_str = date_now.strftime('%Y-%m-%d')
        end_str = date_now.strftime('%Y-%m-%d')
        start_end_exp = Q(Q(start_date__isnull=True, end_date__isnull=True) | Q(start_date__gte=f'{start_str} 00:00:00', end_date__lte=f'{end_str} 23:59:59'))
        system_configs_obj = SystemConfigs.objects.get(start_end_exp, company=request.user.company, key='grantRule')
        grantRule = JsonEncoder.toJson(system_configs_obj.value)

        # 経過月数から該当付与ルールのインデックスを取得する
        grant_rule_index = 0
        grant_rule_add_days = 0
        for index, month in enumerate(grantRule['sectionMonth']):
          if passedyears[1] >= int(month):  #通算月数 >= 規定の通算月数
            grant_rule_index = index
          elif passedyears[1] < int(month):
            break

        # 通算月数から規定付与日数を算出する
        for working in grantRule['workingDays']:
          if user_details_obj.working_days == working['day']:
            grant_rule_add_days = working['grantDays'][grant_rule_index]
            break

        # 更新後 繰越日数を算出する(2年消滅を考慮)
        if user_details_obj.total_carryover_days >= user_details_obj.total_delete_days:
          total_carryover_days_after_value = user_details_obj.total_add_days
        else:
          total_carryover_days_after_value = (user_details_obj.total_carryover_days + user_details_obj.total_add_days) - user_details_obj.total_delete_days

        # 更新後 付与日数
        total_add_days_after_value = grant_rule_add_days

        # 更新後 残日数を算出する
        # 繰越日数 + 付与ルールから取得した規定付与日数
        total_remaining_days_after_value = total_carryover_days_after_value + int(grant_rule_add_days)
      else:
        valid_errors.append('継続勤続期間が6ヶ月未満のため付与対象外です。')

      GRANT_DAYS = ['取得日数', '残日数', '繰越日数', '付与日数']
      # 更新前　残日数　※(繰越日数 + 付与日数) - 取得日数
      total_remaining_days_before_value = (user_details_obj.total_carryover_days + user_details_obj.total_add_days) - user_details_obj.total_delete_days
      grant_days = [
        { 'key': 'totalDeleteDays', 'label': GRANT_DAYS[0], 'beforeValue': user_details_obj.total_delete_days, 'afterValue': total_delete_days_after_value },
        { 'key': 'totalRemainingDays', 'label': GRANT_DAYS[1], 'beforeValue': total_remaining_days_before_value, 'afterValue': total_remaining_days_after_value },
        { 'key': 'totalCarryoverDays', 'label': GRANT_DAYS[2], 'beforeValue': user_details_obj.total_carryover_days, 'afterValue': total_carryover_days_after_value },
        { 'key': 'totalAddDays', 'label': GRANT_DAYS[3], 'beforeValue': user_details_obj.total_add_days, 'afterValue': total_add_days_after_value },
      ]

      # 継続勤続期間を取得する
      # 基準日(reference_date)は、6ヶ月が加算されている前提なので、通算月数を算出するために6ヶ月減算した日付をもとに計算する
      total_service = None
      total_service_months = Utils.get_service_years(Utils.sub_month(user_details_obj.reference_date, HALF_YEAR_MONTH), date_now)
      if total_service_months[1] >= 0:
        total_service = str(total_service_months[0]) + '年' + str(total_service_months[2]) + 'ヶ月' + '（' + str(total_service_months[1]) + '）'

      result = {
        'warnings': warnings,
        'validErrors': valid_errors,
        'grantDays': grant_days,
        'referenceDate': user_details_obj.reference_date.strftime('%Y/%m/%d'),
        'totalService': total_service,
        'lastGrantDate': user_details_obj.last_grant_date.strftime('%Y/%m/%d') if user_details_obj.last_grant_date else None,
        'periodStart': period_start.strftime('%Y/%m/%d') if is_total_service_year_half_over else None,
        'periodEnd': period_end.strftime('%Y/%m/%d') if is_total_service_year_half_over else None,
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '付与日数情報の取得中にエラーが発生しました。'
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
    if not 'totalDeleteDays' in request.data:
      raise exceptions.APIException('Invalid Parameter:totalDeleteDays')
    if not 'totalRemainingDays' in request.data:
      raise exceptions.APIException('Invalid Parameter:totalRemainingDays')
    if not 'totalCarryoverDays' in request.data:
      raise exceptions.APIException('Invalid Parameter:totalCarryoverDays')
    if not 'totalAddDays' in request.data:
      raise exceptions.APIException('Invalid Parameter:totalAddDays')

    userId = request.data['userId']
    total_delete_days = request.data['totalDeleteDays']
    total_remaining_days = request.data['totalRemainingDays']
    total_carryover_days = request.data['totalCarryoverDays']
    total_add_days = request.data['totalAddDays']

    date_now = Utils.get_now_to_string()
    req = {
      'total_delete_days': Decimal(total_delete_days),
      'total_remaining_days': Decimal(total_remaining_days),
      'total_carryover_days': Decimal(total_carryover_days),
      'total_add_days': Decimal(total_add_days),
      'last_grant_date': date_now,
    }

    try:
      if req['total_remaining_days'] != req['total_carryover_days'] + req['total_add_days'] - req['total_delete_days']:
        raise exceptions.ValidationError('入力値の関係が不正です。 ※残日数 = 繰越日数 + 付与日数 - 取得日数')

      with transaction.atomic():
        user_details_obj = UserDetails.objects.select_for_update().get(user_id=userId)

        serializer = UserDetailsSerializer(user_details_obj, data=req)
        if serializer.is_valid():
          serializer.update(user_details_obj, req, date_now, request.user)
        else:
          raise exceptions.APIException(serializer.error_messages['invalid'])

        result_user_details = UserDetails.objects.get(user=userId)

      result = createUserInfoObj(result_user_details, None)
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
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'oldPassword' in request.data:
      raise exceptions.APIException('Invalid Parameter:oldPassword')
    if not 'newPassword' in request.data:
      raise exceptions.APIException('Invalid Parameter:newPassword')

    old_password = request.data['oldPassword']
    new_password = request.data['newPassword']

    try:
      with transaction.atomic():
        user_obj = User.objects.select_for_update().get(id=request.user.id)
        if user_obj.password != Utils.get_password_hash(old_password, user_obj.user_id):
          raise exceptions.ValidationError('パスワードの照合に失敗しました。')

        req = {
          'password': Utils.get_password_hash(new_password, user_obj.user_id)
        }
        date_now = Utils.get_now_to_string()
        serializer = UserSerializer(user_obj, data=req)
        if serializer.is_valid():
          serializer.update(user_obj, req, date_now, request.user)
        else:
          raise exceptions.APIException(serializer.error_messages['invalid'])

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
def createUserInfoObj(user_details, reference_date_separator):
  return {
    'id': user_details.user.id,
    'userId': user_details.user.user_id,
    'companyId': user_details.user.company.id,
    'status': user_details.user.status,
    'firstName': user_details.first_name,
    'lastName': user_details.last_name,
    'auth': user_details.auth,
    'referenceDate': user_details.reference_date if reference_date_separator is None else user_details.reference_date.strftime(f'%Y{reference_date_separator}%m{reference_date_separator}%d'),
    'workingDays': user_details.working_days,
    'totalDeleteDays': user_details.total_delete_days,
    'totalAddDays': user_details.total_add_days,
    # 残日数 = (繰越日数 + 付与日数) - 取得日数
    'totalRemainingDays': (user_details.total_carryover_days + user_details.total_add_days) - user_details.total_delete_days,
    'totalCarryoverDays': user_details.total_carryover_days,
    'lastGrantDate': None if user_details.last_grant_date is None else user_details.last_grant_date.strftime(f'%Y/%m/%d'),
  }

def getGrantPeriod(reference_date, total_service_months):
  # total_service_months = 基準日から現在日付までの通算月数
  # 通算月数を12(ヶ月)で割った値の小数点以下切り捨てした値を係数として、現在年に換算した付与対象期間の開始日、終了日を算出する
  YEAR_MONTH = 12
  coef = math.floor(total_service_months//YEAR_MONTH)
  period_start = Utils.add_month(reference_date, coef * YEAR_MONTH)
  period_end = Utils.sub_day(Utils.add_month(period_start, YEAR_MONTH), 1)
  
  return (period_start, period_end)

def is_update_grant_date(last_grant_date, period_start, period_end):
  if last_grant_date and (period_start <= last_grant_date and last_grant_date <= period_end):
    return True
  else:
    return False
