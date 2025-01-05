import traceback
from django.db.models import Q
from django.db import transaction
from django.conf import settings
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from config.utils import Utils
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from config.enum import TaskType, TaskStatus, TaskAction, TaskActionName

from authentications.views import JWTAuthentication

from users.models import UserDetails
from systemsettings.models import SystemConfigs
from application.models import Application, Task
from application.serializers import TaskSerializer
from users.serializers import UserDetailsSerializer


"""
  承認一覧取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApproveListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]
  serializer_class = TaskSerializer

  def get(self, request):
    param_search_user_id = self.request.GET.get('searchUserId')
    param_search_action = self.request.GET.get('searchAction')
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.APIException('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.APIException('Invalid Parameter:ofset')

    try:
      # 承認タスクのみを取得
      where_params = {
        'application__user__company': request.user.company,
        'operation_user_id': request.user.id,
        'type': TaskType['APPROVAL'].value,
        'action__in': [TaskAction['PANDING'].value, TaskAction['APPROVAL'].value, TaskAction['REJECT'].value],
        'status__in': [TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value, TaskStatus['HISTORY'].value],
      }

      # 検索条件 申請者
      if param_search_user_id:
        where_params['application__user_id'] = param_search_user_id

      # 検索条件 アクション
      if param_search_action:
        where_params['action'] = param_search_action

      application_ids = Task.objects.filter(**where_params).order_by('application__start_date').values_list('application__id', flat=True)
      total_count = len(application_ids)
      application_obj = Application.objects.filter(id__in=application_ids[int(ofset):(int(ofset) + int(limit))]).order_by('start_date')

      # ユーザ情報取得
      user_ids = set([obj.user.id for obj in application_obj])
      user_obj = UserDetails.objects.filter(user__in=user_ids)

      date_now = Utils.get_now_to_datetime()
      start_str = date_now.strftime('%Y-%m-%d')
      end_str = date_now.strftime('%Y-%m-%d')
      start_end_exp = Q(Q(start_date__isnull=True, end_date__isnull=True) | Q(start_date__gte=f'{start_str} 00:00:00', end_date__lte=f'{end_str} 23:59:59'))
      application_type_obj = SystemConfigs.objects.filter(start_end_exp, company=request.user.company, key='applicationType')
      application_type_result = []
      for application_type in application_type_obj:
        application_type_result.append(JsonEncoder.toJson(application_type.value))

      results = []
      for application in application_obj:
        application_user_details = user_obj.filter(user=application.user).values('last_name', 'first_name').first()
        task = Task.objects.filter(application=application.id, **where_params).values('id', 'action', 'comment').last()
        result = {
          'id': task['id'],
          'applicationId': application.id,
          'applicationUserId': application.user.id,
          'type': application.type,
          'sType': Utils.get_application_type_name(application_type_result, application.type),
          'classification': application.classification,
          'sClassification': Utils.get_application_classification_name(application_type_result, application.classification, application.type),
          'applicationDate': application.application_date,
          'sApplicationDate': application.application_date.strftime('%Y/%m/%d'),
          'action': task['action'],
          'sAction': TaskActionName[TaskAction(task['action']).name].value,
          'startDate': application.start_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sStartDate': application.start_date.strftime('%Y/%m/%d'),
          'sStartTime': application.start_date.strftime('%H:%M'),
          'endDate': application.end_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sEndDate': application.end_date.strftime('%Y/%m/%d'),
          'sEndTime': application.end_date.strftime('%H:%M'),
          'comment': task['comment'],
          'applicationUserName': application_user_details['last_name'] + " " + application_user_details['first_name'],
        }
        results.append(result)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.renderList(results, total_count, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.renderList([], 0, response.status_code, '承認情報一覧の取得中にエラーが発生しました。')

    return response


"""
  承認

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApproveAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    application_id = request.data['application_id']
    task_id = request.data['task_id']
    comment = request.data['comment']
    action = request.data['action']

    if not application_id:
      raise exceptions.APIException('Invalid Parameter:application_id')
    if not task_id:
      raise exceptions.APIException('Invalid Parameter:task_id')
    if not comment:
      raise exceptions.APIException('Invalid Parameter:comment')
    if not action:
      raise exceptions.APIException('Invalid Parameter:action')

    try:
      date_now = Utils.get_now_to_string()
      with transaction.atomic():
        application_task = Task.objects.select_for_update().get(application=application_id, status=TaskStatus['ACTIVE'].value, type=TaskType['APPLICATION'].value)
        approval_task_obj = Task.objects.select_for_update().filter(application=application_id, status=TaskStatus['ACTIVE'].value, type=TaskType['APPROVAL'].value)

        is_task_all_approval = True     # 承認タスクがすべて「承認」状態か
        approval_task = None            # 承認者自身の承認タスク
        approval_tasks = []             # その他の承認者の承認タスク
        for obj in approval_task_obj:
          # 承認タスク
          if obj.id == task_id:
            approval_task = obj
          else:
            approval_tasks.append(obj)
            # 承認タスクがすべて「承認」状態かを判定
            # 承認者が無効化されている場合もあるため、無効な承認者の承認タスクは除外して判定
            if obj.action != TaskAction['APPROVAL'].value and obj.operation_user.status == settings.USER_EFFECTIVE_STATUS:
              is_task_all_approval = False

        approve_task_req = {
          'operation_user_id': request.user.id,
          'action': action,
          'comment': comment,
          'operation_date': date_now,
        }

        approve_task_serializer = TaskSerializer(approve_task_req, data=approve_task_req)
        if not approve_task_serializer.is_valid():
          raise exceptions.APIException(approve_task_serializer.error_messages['invalid'])

        if approve_task_req['action'] == TaskAction['APPROVAL'].value:
          # 承認操作の場合
          # 承認タスクがすべて「承認」状態の場合、承認完了処理を実行する
          if is_task_all_approval:
            # 申請タスク完了処理
            self.complete_application_task(application_id, date_now)
            # 承認タスククローズ処理
            self.close_application_task(approval_task_obj, task_id, comment, date_now)
            # 年次有給休暇申請の場合、取得日数に加算する
            if application_task.application.type == settings.PAID_HOLIDAY_VALUE:
              self.recalculationForTotalDeleteDays(application_task.application, date_now)
          else:
            approve_task_serializer.update_approval_task(approval_task, approve_task_req, date_now, request.user, True)

        elif approve_task_req['action'] == TaskAction['REJECT'].value:
          # 差戻操作の場合
          application_task_req = {
            'action': action,
            'operation_date': date_now,
          }
          application_task_serializer = TaskSerializer(application_task_req, data=application_task_req)
          if not application_task_serializer.is_valid():
            raise exceptions.APIException(application_task_serializer.error_messages['invalid'])

          # 承認タスクを「差戻」で更新
          approve_task_serializer.update_approval_task(approval_task, approve_task_req, date_now, request.user, True)
          # 申請タスクも「差戻」状態に変更する
          application_task_serializer.update_application_task(application_task, application_task_req, date_now, self.request.user, False)

          for approval_task in approval_tasks:
            # 差戻した場合、申請に紐づく「承認待ち」状態の承認タスクのアクションは「システム取消」に変更する
            if approval_task.action == TaskAction['PANDING'].value:
              other_approval_task_req = {
                'action': TaskAction['SYSTEM_CANCEL'].value,
                'status': TaskStatus['NON_ACTIVE'].value,
              }

              other_approval_task_serializer = TaskSerializer(approve_task_req, data=approve_task_req)
              if not other_approval_task_serializer.is_valid():
                raise exceptions.APIException(other_approval_task_serializer.error_messages['invalid'])

              other_approval_task_serializer.update_approval_task(approval_task, other_approval_task_req, date_now, request.user, False)

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '承認処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response

  # 申請タスク完了処理
  # 申請タスクのアクションを「COMPLETE」、ステータスを「CLOSED」に変更する
  def complete_application_task(self, application_id, date_now):
    task = Task.objects.select_for_update().get(application=application_id, type=TaskType['APPLICATION'].value, status=TaskStatus['ACTIVE'].value)
    task_req = {
      'action': TaskAction['COMPLETE'].value,
      'status': TaskStatus['CLOSED'].value,
    }
    serializer = TaskSerializer(task, data=task_req)
    if not serializer.is_valid():
      raise exceptions.APIException(serializer.error_messages['invalid'])

    serializer.update_approval_task(task, task_req, date_now, self.request.user, False)

    return

  # 承認タスククローズ処理
  # 申請タスクのステータスを「CLOSED」に変更する
  def close_application_task(self, approval_task_obj, approval_task_id, comment, date_now):
    task_req = {}
    for task in approval_task_obj:
      if task.id == approval_task_id:
        # 承認者自身の承認タスク更新
        task_req = {
          'action': TaskAction['APPROVAL'].value,
          'status': TaskStatus['CLOSED'].value,
          'comment': comment,
          'operation_date': date_now,
        }
      elif task.operation_user.status != settings.USER_EFFECTIVE_STATUS:
        # 無効なユーザの承認タスク更新 ※「システム取消」扱いとする
        task_req = {
          'action': TaskAction['SYSTEM_CANCEL'].value,
          'status': TaskStatus['NON_ACTIVE'].value,
        }
      else:
        task_req = {
          'status': TaskStatus['CLOSED'].value,
          'operation_date': date_now,
        }

      serializer = TaskSerializer(task, data=task_req)
      if not serializer.is_valid():
        raise exceptions.APIException(serializer.error_messages['invalid'])

      serializer.update_approval_task(task, task_req, date_now, self.request.user, task.id == approval_task_id)

    return

  # 取得日数に加算する
  def recalculationForTotalDeleteDays(self, application, date_now):
    user_details_obj = UserDetails.objects.select_for_update().get(user__id=application.user.id)
    result_hours = Utils.get_application_hour(application.total_time)

    # 残日数 < 申請日数　※残日数: (繰越日数 + 付与日数) - 取得日数
    if (user_details_obj.total_carryover_days + user_details_obj.total_add_days) - user_details_obj.total_delete_days < result_hours:
      raise exceptions.ValidationError('残日数を超過しているため承認を完了できません。')

    req = {
      'total_delete_days': user_details_obj.total_delete_days + result_hours
    }

    serializer = UserDetailsSerializer(user_details_obj, data=req)
    if not serializer.is_valid():
      raise exceptions.APIException(serializer.error_messages['invalid'])

    serializer.update(user_details_obj, req, date_now, self.request.user)

    return
