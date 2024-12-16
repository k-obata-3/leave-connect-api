import traceback
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from authentications.views import JWTAuthentication
from django.db import transaction
from application.models import Application, Task
from users.models import User, UserDetails
from systemsettings.models import SystemConfigs
from users.serializers import UserSerializer, UserDetailsSerializer
import datetime
from config.utils import Utils


# ユーザ一覧取得
class UserListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.ValidationError('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.ValidationError('Invalid Parameter:ofset')

    try:
      total_count = UserDetails.objects.filter(user__company=request.user.company).count()
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company).all()[int(ofset):(int(ofset) + int(limit))]
      results = []
      for obj in user_details_obj:
        results.append(createUserInfoObj(obj))

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.renderList(results, total_count, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.renderList([], 0, response.status_code, 'ユーザ一覧情報の取得中にエラーが発生しました。')

    return response

# ユーザ情報取得
class UserDetailsRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    id = self.request.GET.get('id') if self.request.GET.get('id') else request.user.id

    try:
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company, user__id=id).first()
      results = createUserInfoObj(user_details_obj)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ユーザ情報の取得中にエラーが発生しました。')

    return response

# ユーザ名一覧取得
class UserNameListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company).all()
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
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ユーザ名情報の取得中にエラーが発生しました。')

    return response

# ユーザ情報更新
class UpdateUserAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'id' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:id')
    if not 'lastName' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:lastName')
    if not 'firstName' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:firstName')
    if not 'referenceDate' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:referenceDate')
    if not 'workingDays' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:workingDays')
    if not 'totalDeleteDays' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:totalDeleteDays')
    if not 'totalAddDays' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:totalAddDays')
    if not 'totalRemainingDays' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:totalRemainingDays')
    if not 'totalCarryoverDays' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:totalCarryoverDays')

    id = request.data['id']

    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    date_now = datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    try:
      req = {
        'first_name': request.data['firstName'],
        'last_name': request.data['lastName'],
        # 'auth': request.data['auth'],
        # 'reference_date': request.data['referenceDate'].replace('/', '-') + ' ' + request.data['startTime'],
        'reference_date': request.data['referenceDate'].replace('/', '-'),
        'working_days': request.data['workingDays'],
        'total_delete_days': request.data['totalDeleteDays'],
        'total_add_days': request.data['totalAddDays'],
        # 'total_remaining_days': request.data['totalRemainingDays'],
        # 'auto_calc_remaining_days': request.data[''],
        'total_carryover_days': request.data['totalCarryoverDays'],
      }

      with transaction.atomic():
        user_details_obj = UserDetails.objects.select_for_update().get(user=id)

        serializer = UserDetailsSerializer(user_details_obj, data=req)
        if serializer.is_valid():
          serializer.update(user_details_obj, req, date_now, request.user)
        else:
          print('【ERROR】:' + serializer.error_messages['invalid'])
          raise exceptions.APIException('エラーが発生しました。')

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '更新処理中にエラーが発生しました。')

    return response


# 付与日数更新
class UpdateGrantDaysAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'id' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:id')

    id = request.data['id']

    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    date_now = datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    try:
      req = {
        # 'first_name': request.data['firstName'],
        # 'last_name': request.data['lastName'],
        # 'auth': request.data['auth'],
        # 'reference_date': request.data['referenceDate'].replace('/', '-') + ' ' + request.data['startTime'],
        # 'reference_date': request.data['referenceDate'].replace('/', '-'),
        # 'working_days': request.data['workingDays'],
        # 'total_delete_days': request.data['totalDeleteDays'],
        # 'total_add_days': request.data['totalAddDays'],
        # 'total_remaining_days': request.data['totalRemainingDays'],
        # 'auto_calc_remaining_days': request.data[''],
        # 'total_carryover_days': request.data['totalCarryoverDays'],
      }

      with transaction.atomic():
        user_details_obj = UserDetails.objects.select_for_update().get(user=id)

        # serializer = UserDetailsSerializer(user_details_obj, data=req)
        # if serializer.is_valid():
        #   serializer.update(user_details_obj, req, date_now, request.user)
        # else:
        #   print('【ERROR】:' + serializer.error_messages['invalid'])
        #   raise exceptions.APIException('エラーが発生しました。')

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '更新処理中にエラーが発生しました。')

    return response

# パスワード変更
class ChangePasswordAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'oldPassword' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:oldPassword')
    if not 'newPassword' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:newPassword')

    old_password = request.data['oldPassword']
    new_password = request.data['newPassword']

    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    date_now = datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    try:
      with transaction.atomic():
        user_obj = User.objects.select_for_update().get(id=request.user.id)
        if user_obj.password != Utils.getPasswordHash(old_password, user_obj.user_id):
          raise exceptions.ValidationError('パスワードの照合に失敗しました。')

        req = {
          'password': Utils.getPasswordHash(new_password, user_obj.user_id)
        }
        serializer = UserSerializer(user_obj, data=req)
        if serializer.is_valid():
          serializer.update(user_obj, req, date_now, request.user)
        else:
          print('【ERROR】:' + serializer.error_messages['invalid'])
          raise exceptions.APIException()

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
def createUserInfoObj(user_details):
  return {
    'id': user_details.user.id,
    'userId': user_details.user.user_id,
    'companyId': user_details.user.company.id,
    'firstName': user_details.first_name,
    'lastName': user_details.last_name,
    'auth': user_details.auth,
    'referenceDate': user_details.reference_date.strftime('%Y/%m/%d'),
    'workingDays': user_details.working_days,
    'totalDeleteDays': user_details.total_delete_days,
    'totalAddDays': user_details.total_add_days,
    'totalRemainingDays': user_details.total_remaining_days,
    'totalRemainingDays': user_details.total_add_days + user_details.total_carryover_days - user_details.total_delete_days,
    'autoCalcRemainingDays': user_details.auto_calc_remaining_days,
    'totalCarryoverDays': user_details.total_carryover_days,
  }
