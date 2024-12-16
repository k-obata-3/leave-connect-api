import traceback
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from config.renderers import JSONRenderer
from config.jsonEncoder import JsonEncoder
from config.enum import TaskType, TaskTypeName, TaskStatus, TaskStatusName, TaskAction, TaskActionName, ApplicationClassification, ApplicationClassificationName, ApplicationType, ApplicationTypeName
from config.responseRenderers import ResponseRenderers
from authentications.views import JWTAuthentication
from application.serializers import TaskSerializer
from users.serializers import UserDetailsSerializer
from django.db.models import Q
from application.models import Application, Task
from users.models import UserDetails
from django.db import transaction
# from datetime import datetime
import datetime
# from zoneinfo import ZoneInfo
# import time
from config.utils import Utils
# from django.http.response import JsonResponse
import time


class ApproveListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]
  serializer_class = TaskSerializer
  queryset = Task.objects.all()

  def get(self, request):
    param_search_user_id = self.request.GET.get('searchUserId')
    param_search_action = self.request.GET.get('searchAction')
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.ValidationError('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.ValidationError('Invalid Parameter:ofset')

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

      # 検索条件 状況
      if param_search_action:
        where_params['action'] = param_search_action

      task_obj = self.queryset.filter(**where_params).all()
      application_ids = list(set([t.application.id for t in task_obj]))
      total_count = len(application_ids)
      application_obj = Application.objects.filter(id__in=application_ids[int(ofset):(int(ofset) + int(limit))]).all()

      # ユーザ情報取得
      user_ids = set([obj.user.id for obj in application_obj])
      user_obj = UserDetails.objects.filter(user__in=user_ids).all()

      results = []
      for application in application_obj:
        application_user_details = user_obj.filter(user=application.user).values('last_name', 'first_name').first()
        task = Task.objects.filter(application=application.id, **where_params).values('id', 'action', 'comment').last()
        result = {
          'id': task['id'],
          'applicationId': application.id,
          'applicationUserId': application.user.id,
          'type': application.type,
          'sType': ApplicationTypeName[ApplicationType(application.type).name].value,
          'classification': application.classification,
          'sClassification': ApplicationClassificationName[ApplicationClassification(application.classification).name].value,
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
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.renderList([], 0, response.status_code, '承認情報一覧の取得中にエラーが発生しました。')

    return response


class ApproveAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    application_id = request.data['application_id']
    task_id = request.data['task_id']
    comment = request.data['comment']
    action = request.data['action']

    if not application_id:
      raise exceptions.ValidationError('Invalid Parameter:application_id')
    if not task_id:
      raise exceptions.ValidationError('Invalid Parameter:task_id')
    if not comment:
      raise exceptions.ValidationError('Invalid Parameter:comment')
    if not action:
      raise exceptions.ValidationError('Invalid Parameter:action')

    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    date_now = datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    try:
      approve_task_req = {
        'operation_user_id': request.user.id,
        'action': action,
        'comment': comment,
        'operation_date': date_now,
      }

      with transaction.atomic():
        task_obj = Task.objects.select_for_update().filter(application=application_id, status=TaskStatus['ACTIVE'].value).all()

        is_task_all_approval = True
        application_task = None
        approval_task = None
        approval_tasks = []
        for task in task_obj:
          if task.type == TaskType['APPLICATION'].value:
            # 申請タスク
            application_task = task
          else:
            # 承認タスク
            if task.id == task_id:
              approval_task = task
            else:
              approval_tasks.append(task)
              # 承認タスクがすべて「承認」状態かを判定
              if task.action != TaskAction['APPROVAL'].value:
                is_task_all_approval = False

        application_task_req = {
          'action': action,
          'operation_date': date_now,
        }

        approve_task_serializer = TaskSerializer(approve_task_req, data=approve_task_req)
        application_task_serializer = TaskSerializer(application_task_req, data=application_task_req)
        if not approve_task_serializer.is_valid():
          print('【ERROR】:' + approve_task_serializer.error_messages['invalid'])
          raise exceptions.APIException('エラーが発生しました。')
        if not application_task_serializer.is_valid():
          print('【ERROR】:' + application_task_serializer.error_messages['invalid'])
          raise exceptions.APIException('エラーが発生しました。')

        if approve_task_req['action'] == TaskAction['APPROVAL'].value:
          # 承認操作の場合
          # 承認タスクがすべて「承認」状態の場合、承認完了処理を実行する
          if is_task_all_approval:
            # 申請タスク完了処理
            self.complete_application_task(application_id, date_now)
            # 承認タスククローズ処理
            self.close_application_task(application_id, task_id, comment, date_now)
            # 年次有給休暇申請の場合、取得日数に加算する
            if application_task.application.type == ApplicationType['PAID_HOLIDAY'].value:
              self.recalculationForTotalDeleteDays(application_task.application, date_now)

          else:
            approve_task_serializer.update_approval_task(approval_task, approve_task_req, date_now, request.user, True)

        elif approve_task_req['action'] == TaskAction['REJECT'].value:
          # 差戻操作の場合
          approve_task_serializer.update_approval_task(approval_task, approve_task_req, date_now, request.user, True)
          # 申請タスクも「差戻」状態に変更する
          application_task_serializer.update_application_task(application_task, application_task_req, date_now, self.request.user, False)

          for approval_task in approval_tasks:
            # 差戻した場合、申請に紐づく「承認待ち」状態の承認タスクのアクションは「システム取消」に変更する
            if approval_task.action == TaskAction['PANDING'].value:
              other_approval_task_req = {
                'action': TaskAction['SYSTEM_CANCEL'].value,
                'status': TaskStatus['NON_ACTIVE'].value,
                'operation_date': date_now,
              }

              other_approval_task_serializer = TaskSerializer(approve_task_req, data=approve_task_req)
              if not other_approval_task_serializer.is_valid():
                print('【ERROR】:' + other_approval_task_serializer.error_messages['invalid'])
                raise exceptions.APIException('エラーが発生しました。')

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
      print('【ERROR】:' + serializer.error_messages['invalid'])
      raise exceptions.APIException('エラーが発生しました。')

    serializer.update_approval_task(task, task_req, date_now, self.request.user, False)

    return

  # 承認タスククローズ処理
  # 申請タスクのステータスを「CLOSED」に変更する
  def close_application_task(self, application_id, approval_task_id, comment, date_now):
    tasks = Task.objects.select_for_update().filter(application=application_id, type=TaskType['APPROVAL'].value, status=TaskStatus['ACTIVE'].value).all()
    for task in tasks:
      task_req = {
        'status': TaskStatus['CLOSED'].value,
        'action': TaskAction['APPROVAL'].value if task.id == approval_task_id else task.action,
        'comment': comment if task.id == approval_task_id else task.comment,
        'operation_date': date_now,
      }
      serializer = TaskSerializer(task, data=task_req)
      if not serializer.is_valid():
        print('【ERROR】:' + serializer.error_messages['invalid'])
        raise exceptions.APIException('エラーが発生しました。')

      serializer.update_approval_task(task, task_req, date_now, self.request.user, task.id == approval_task_id)

    return

  # 取得日数に加算する
  def recalculationForTotalDeleteDays(self, application, date_now):
    user_details_obj = UserDetails.objects.select_for_update().get(user__id=application.user.id)
    result_hours = Utils.getApplicationHour(application.total_time)

    if user_details_obj.auto_calc_remaining_days < result_hours:
      raise exceptions.ValidationError('残日数を超過しているため承認を完了できません。')

    req = {
      'auto_calc_remaining_days': user_details_obj.auto_calc_remaining_days - result_hours,
      'total_delete_days': user_details_obj.total_delete_days + result_hours
    }

    serializer = UserDetailsSerializer(user_details_obj, data=req)
    if not serializer.is_valid():
      print('【ERROR】:' + serializer.error_messages['invalid'])
      raise exceptions.APIException('エラーが発生しました。')

    serializer.update(user_details_obj, req, date_now, self.request.user)

    return

