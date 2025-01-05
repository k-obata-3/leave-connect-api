import traceback
from django.db.models import Q
from django.db import transaction
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView

from config.utils import Utils
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers

from authentications.views import JWTAuthentication

from users.models import UserDetails
from systemsettings.models import SystemConfigs
from systemsettings.serializers import SystemConfigsSerializer


"""
  システム設定情報取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class SystemConfigsRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    key = self.request.GET.get('key')
    try:
      system_configs_obj = SystemConfigs.objects.filter(company=request.user.company, key=key)
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
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'システム設定情報取得中にエラーが発生しました。')

    return response


"""
  システム設定情報削除

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
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
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '削除処理中にエラーが発生しました。')

    return response


"""
  承認グループ一覧取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApprovalGroupListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      system_configs_obj = SystemConfigs.objects.filter(company=request.user.company, key='approvalGroup')
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company)

      results = []
      for obj in system_configs_obj:
        value = JsonEncoder.toJson(obj.value)
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
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '承認グループ情報の取得中にエラーが発生しました。')

    return response


"""
  承認グループ登録/更新

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApprovalGroupAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'groupName' in request.data:
      raise exceptions.APIException('Invalid Parameter:groupName')
    if not 'approval' in request.data:
      raise exceptions.APIException('Invalid Parameter:approval')

    id = request.data['id'] if 'id' in request.data else None
    approval = request.data['approval']

    date_now = Utils.get_now_to_string()
    req_value = {
      "groupName": request.data['groupName'],
      "approver1": approval[0] if len(approval) > 0 else "",
      "approver2": approval[1] if len(approval) > 1 else "",
      "approver3": approval[2] if len(approval) > 2 else "",
      "approver4": approval[3] if len(approval) > 3 else "",
      "approver5": approval[4] if len(approval) > 4 else "",
    }

    req = {
      'company': request.user.company,
      'key': 'approvalGroup',
      'value': JsonEncoder.toString(req_value)
    }

    try:
      with transaction.atomic():
        if id is None:
          # 作成
          serializer = SystemConfigsSerializer(req, data=req)
          if serializer.is_valid():
            serializer.save(req, date_now, request.user)
          else:
            raise exceptions.APIException(serializer.error_messages['invalid'])
        else:
          system_configs_obj = SystemConfigs.objects.select_for_update().filter(pk=id, company=request.user.company, key='approvalGroup').first()
          serializer = SystemConfigsSerializer(system_configs_obj, data=req)
          if serializer.is_valid():
            serializer.update(system_configs_obj, req, date_now, request.user)
          else:
            raise exceptions.APIException(serializer.error_messages['invalid'])

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '登録処理中にエラーが発生しました。')

    return response


"""
  申請タイプ設定取得

Returns:
  _type_: _description_
"""
class ApplicationTypeListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      date_now = Utils.get_now_to_datetime()
      start_str = date_now.strftime('%Y-%m-%d')
      end_str = date_now.strftime('%Y-%m-%d')
      start_end_exp = Q(Q(start_date__isnull=True, end_date__isnull=True) | Q(start_date__gte=f'{start_str} 00:00:00', end_date__lte=f'{end_str} 23:59:59'))
      application_type_obj = SystemConfigs.objects.filter(start_end_exp, company=request.user.company, key='applicationType')
      application_type_result = []
      for application_type in application_type_obj:
        application_type_result.append(JsonEncoder.toJson(application_type.value))

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(application_type_result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '申請タイプ設定情報取得中にエラーが発生しました。')

    return response
