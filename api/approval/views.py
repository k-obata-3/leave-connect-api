import traceback
from datetime import datetime, time
from django.db.models import Q, Sum
from django.db import transaction
from django.conf import settings
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from typing_extensions import deprecated

from config.utils import Utils
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from config.enum import TaskType, TaskStatus, TaskAction, TaskActionName

from authentications.views import JWTAuthentication

from users.models import UserDetails, GrantHistories
from systemsettings.models import SystemSettings
from application.models import Applications, Tasks
from application.serializers import TaskSerializer
from users.serializers import UserDetailsSerializer, GrantHistorySerializer


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
  permission_classes = []

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

      application_ids = Tasks.objects.filter(**where_params).order_by('application__start_date').values_list('application__id', flat=True)
      total_count = len(application_ids)
      application_obj = Applications.objects.filter(id__in=application_ids[int(ofset):(int(ofset) + int(limit))]).order_by('start_date')

      # ユーザ情報取得
      user_ids = set([obj.user.id for obj in application_obj])
      user_obj = UserDetails.objects.filter(user__in=user_ids)

      # 申請タイプ情報を取得する
      application_type_result = Utils.get_application_type(request.user, Utils.get_now_to_datetime())

      results = []
      for application in application_obj:
        application_user_details = user_obj.filter(user=application.user).values('last_name', 'first_name').first()
        task = Tasks.objects.filter(application=application.id, **where_params).values('id', 'action', 'comment').last()
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
          'totalTime': application.total_time,
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
  permission_classes = []

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
        application_task = Tasks.objects.select_for_update().get(application=application_id, status=TaskStatus['ACTIVE'].value, type=TaskType['APPLICATION'].value)
        approval_task_obj = Tasks.objects.select_for_update().filter(application=application_id, status=TaskStatus['ACTIVE'].value, type=TaskType['APPROVAL'].value)

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
          raise exceptions.APIException(approve_task_serializer.errors)

        if approve_task_req['action'] == TaskAction['APPROVAL'].value:
          # 承認操作の場合
          # 承認タスクがすべて「承認」状態の場合、承認完了処理を実行する
          if is_task_all_approval:
            # 年次有給休暇申請の場合、付与日数、残日数から承認完了が可能かチェックする
            # 承認不可の場合、例外をthrowする
            if application_task.application.type == settings.PAID_HOLIDAY_TYPE_VALUE:
              self.validApplicationComplete(application_task.application, date_now)

            # 申請タスク完了処理
            self.complete_application_task(application_id, date_now)
            # 承認タスククローズ処理
            self.close_application_task(approval_task_obj, task_id, comment, date_now)

            # 年次有給休暇申請の場合、取得日数に加算する
            # if application_task.application.type == settings.PAID_HOLIDAY_TYPE_VALUE:
              # self.recalculationForTotalDeleteDays(application_task.application, date_now)
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
            raise exceptions.APIException(application_task_serializer.errors)

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
                raise exceptions.APIException(other_approval_task_serializer.errors)

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
    task = Tasks.objects.select_for_update().get(application=application_id, type=TaskType['APPLICATION'].value, status=TaskStatus['ACTIVE'].value)
    task_req = {
      'action': TaskAction['COMPLETE'].value,
      'status': TaskStatus['CLOSED'].value,
    }
    serializer = TaskSerializer(task, data=task_req)
    if not serializer.is_valid():
      raise exceptions.APIException(serializer.errors)

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
        raise exceptions.APIException(serializer.errors)

      serializer.update_approval_task(task, task_req, date_now, self.request.user, task.id == approval_task_id)

    return


  # 付与日数、残日数から承認完了が可能かチェック
  def validApplicationComplete(self, application, date_now):
    user_details_obj = UserDetails.objects.get(user__id=application.user.id)
    # 時間単位の有給休暇取得の申請かどうか
    is_classification_time = application.classification == settings.APPLICATION_CLASSIFICATION_TIME_VALUE

    # 申請情報の取得日をもとに対象期間の付与情報を取得
    grant_history_obj = GrantHistories.objects.filter(user=user_details_obj.user.id, add_date__lte=application.start_date, extinction_date__gte=application.end_date).order_by('elapsed_month')
    # 対象期間の付与情報が存在しない場合、エラーとする
    if grant_history_obj.exists() is False:
      raise exceptions.ValidationError('申請者に付与情報が設定されていないため、ユーザ管理から付与日数を設定してください。')

    # 取得年に換算した付与対象期間の開始日を算出する
    reference_date_time = datetime.combine(user_details_obj.reference_date, time())
    elapsed_period = Utils.get_elapsed_period(reference_date_time, application.start_date)
    grant_current_period = Utils.get_grant_current_period(reference_date_time, elapsed_period[1])
    current_grant_history = grant_history_obj.filter(add_date=grant_current_period[0]).first()
    # 対象期間の付与情報が存在しない場合、エラーとする
    if current_grant_history is None:
      raise exceptions.ValidationError('付与情報が設定されていないため、ユーザ管理から付与日数を設定してください。')

    # 付与日数を合算
    add_days_sum = grant_history_obj.aggregate(sum=Sum("add_days"))
    total_add_days = 0 if add_days_sum['sum'] is None else add_days_sum['sum']

    total_delete_time = 0
    total_delete_time_hour_unit = 0
    for grant_history in grant_history_obj:
      # 対象期間の申請情報を取得する
      paid_holiday_application = Utils.get_paid_holiday_application(user_details_obj.user, grant_history.add_date, Utils.add_year(grant_history.add_date, 1), [TaskAction['COMPLETE'].value])
      total_delete_time += paid_holiday_application['total_delete_time'] + paid_holiday_application['total_delete_time_hour_unit']
      # 時間単位のチェック対象は今年度分のみとする
      if paid_holiday_application['start_date'] == current_grant_history.add_date:
        total_delete_time_hour_unit = paid_holiday_application['total_delete_time_hour_unit']

    # 時間単位の場合、時間単位の取得上限時間を超過してしまう場合、エラーとする
    if is_classification_time and total_delete_time_hour_unit + application.total_time > settings.APPLICATION_CLASSIFICATION_TIME_UPPER_LIMIT:
      raise exceptions.ValidationError('時間単位として取得可能な時間を超過するため、承認を完了できません。')

    # 取得可能時間を超過してしまう場合、エラーとする
    if application.total_time > total_add_days * 8 - total_delete_time:
      raise exceptions.ValidationError('残日数が不足しているため、承認を完了できません。')

    return
