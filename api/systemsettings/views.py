import traceback
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from authentications.views import JWTAuthentication
from systemsettings.serializers import SystemConfigsSerializer
from django.db import transaction
from users.models import UserDetails
from systemsettings.models import SystemConfigs
import datetime
import json


# システム設定情報取得
class SystemConfigsRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    key = self.request.GET.get('key')
    try:
      system_configs_obj = SystemConfigs.objects.filter(company=request.user.company, key=key).all()
      results = []
      for obj in system_configs_obj:
        results.append({
          'id': obj.id,
          'key': obj.key,
          'value': obj.value
        })

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'システム設定情報取得中にエラーが発生しました。')

    return response

# システム設定情報削除
class SystemConfigsDestroyAPIView(DestroyAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def destroy(self, request):
    id = self.request.GET.get('id')
    try:
      system_configs_obj = SystemConfigs.objects.get(pk=id)
      if system_configs_obj.company != request.user.company:
        raise exceptions.APIException('削除に失敗しました。')

      system_configs_obj.delete()

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '削除処理中にエラーが発生しました。')

    return response

# 承認グループ一覧取得
class ApprovalGroupListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      system_configs_obj = SystemConfigs.objects.filter(company=request.user.company, key='approvalGroup').all()
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company).all()

      results = []
      for obj in system_configs_obj:
        value = json.loads(obj.value)
        user_ids = [value['approver1'], value['approver2'], value['approver3'], value['approver4'], value['approver5']]
        approvers = []
        for user_id in user_ids:
          user_name = None
          if user_id:
            user = user_details_obj.filter(user=user_id).first()
            user_name = user.last_name + " " + user.first_name if user else None
          approvers.append({
            'id': user_id,
            'name': user_name,
          })

        results.append({
          'groupId': obj.id,
          'groupName': value['groupName'],
          'approver': approvers,
        })

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '承認グループ情報の取得中にエラーが発生しました。')

    return response

# 承認グループ登録/更新
class ApprovalGroupAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'groupName' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:groupName')
    if not 'approval' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:approval')

    id = request.data['id'] if 'id' in request.data else None
    groupName = request.data['groupName']
    approval = request.data['approval']

    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    date_now = datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    try:
      req_value = {
        "groupName": groupName,
        "approver1": approval[0] if len(approval) > 0 else "",
        "approver2": approval[1] if len(approval) > 1 else "",
        "approver3": approval[2] if len(approval) > 2 else "",
        "approver4": approval[3] if len(approval) > 3 else "",
        "approver5": approval[4] if len(approval) > 4 else "",
      }

      req = {
        'company': request.user.company,
        'key': 'approvalGroup',
        'value': JsonEncoder.getJson(req_value)
      }

      with transaction.atomic():
        if id is None:
          # 作成
          serializer = SystemConfigsSerializer(req, data=req)
          if serializer.is_valid():
            serializer.save(req, date_now, request.user)
          else:
            print('【ERROR】:' + serializer.error_messages['invalid'])
            raise exceptions.APIException('エラーが発生しました。')
        else:
          system_configs_obj = SystemConfigs.objects.select_for_update().filter(pk=id, company=request.user.company, key='approvalGroup').first()
          serializer = SystemConfigsSerializer(system_configs_obj, data=req)
          if serializer.is_valid():
            serializer.update(system_configs_obj, req, date_now, request.user)
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
      response.data = ResponseRenderers.render({}, response.status_code, '登録処理中にエラーが発生しました。')

    return response
