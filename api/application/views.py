import traceback
import urllib.parse
from datetime import datetime, time
from django.db.models import Q
from django.db import transaction
from django.conf import settings
from django.http import FileResponse
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView
from monthdelta import monthmod

from config.utils import Utils
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from config.enum import TaskType, TaskStatus, TaskStatusName, TaskAction, TaskActionName, WeekDayName
from application.pdfReport import PdfReport

from authentications.views import JWTAuthentication, IsAuthenticated

from users.models import UserDetails, GrantHistories
from systemsettings.models import SystemSettings
from application.models import Applications, Tasks

from application.serializers import ApplicationSerializer, TaskSerializer


"""
  通知情報取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class NotificationRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    try:
      application_task_obj = Tasks.objects.filter(operation_user=request.user.id, status=TaskStatus['ACTIVE'].value, type=TaskType['APPLICATION'].value)
      approval_task_obj = Tasks.objects.filter(operation_user=request.user.id, type=TaskType['APPROVAL'].value, action=TaskAction['PANDING'].value)

      # 対応が必要な申請の件数
      actionRequiredApplicationCount = application_task_obj.filter(action=TaskAction['REJECT'].value).count()
      # 承認待ちタスクの件数取得
      approvalTaskCount = approval_task_obj.count()
      # 申請中の件数
      activeApplicationCount = application_task_obj.filter(action=TaskAction['PANDING'].value).count()
      response = Response()
      response.status_code = status.HTTP_200_OK
      result = {
          "actionRequiredApplicationCount": actionRequiredApplicationCount,
          "approvalTaskCount": approvalTaskCount,
          "activeApplicationCount": activeApplicationCount
      }
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '通知情報の取得中にエラーが発生しました。')

    return response


"""
  月間の申請一覧取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationMonthListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    start = self.request.GET.get('start')
    end = self.request.GET.get('end')

    if not start:
      raise exceptions.APIException('Invalid Parameter:start')
    if not end:
      raise exceptions.APIException('Invalid Parameter:end')

    try:
      # 申請タイプ情報を取得する
      application_type_result = Utils.get_application_type(request.user, Utils.get_now_to_datetime())

      where_params = {
        'operation_user': request.user.id,
        'type': TaskType['APPLICATION'].value,
        'status__in': [TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value],
        'application__start_date__gte': start,
        'application__start_date__lte': end,
      }
      task_obj = Tasks.objects.filter(~Q(action=TaskAction['CANCEL'].value), ~Q(application__type=settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE), **where_params)

      results = []
      for task in task_obj:
        result = {
          'id': task.application.id,
          'applicationUserId': task.application.user.id,
          'type': task.application.type,
          'sType': Utils.get_application_type_name(application_type_result, task.application.type),
          'classification': task.application.classification,
          'sClassification': Utils.get_application_classification_name(application_type_result, task.application.classification, task.application.type),
          'action': task.action,
          'sAction': TaskActionName[TaskAction(task.action).name].value,
          'startDate': task.application.start_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sStartDate': task.application.start_date.strftime('%Y-%m-%d'),
          'sStartTime': task.application.start_date.strftime('%H:%M'),
          'endDate': task.application.end_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sEndDate': task.application.end_date.strftime('%Y-%m-%d'),
          'sEndTime': task.application.end_date.strftime('%H:%M'),
          'totalTime': task.application.total_time,
        }
        results.append(result)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '申請情報一覧の取得中にエラーが発生しました。')

    return response


"""
  申請一覧取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    param_is_admin = self.request.GET.get('isAdmin')
    param_user_id = self.request.GET.get('userId')
    param_search_action = self.request.GET.get('searchAction')
    param_search_year = self.request.GET.get('searchYear')
    param_search_type = self.request.GET.get('searchType')
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.APIException('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.APIException('Invalid Parameter:ofset')
    
    try:
      # 申請管理からの参照かどうか
      is_admin = param_is_admin == 'true'

      # 申請タスクのみを取得
      where_params = {
        'application__user__company': request.user.company,
        'type': TaskType['APPLICATION'].value,
        'status__in': [TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value],
      }

      # 検索条件 申請者
      # 申請管理からの参照かつ管理者の場合、リクエストパラメータのユーザIDで絞り込み可能
      # 上記以外の場合、ログインユーザ自身の申請情のみを取得対象とする
      search_userId = param_user_id if request.user.is_admin and is_admin else request.user.id
      if search_userId:
        where_params['operation_user_id'] = search_userId

      # 検索条件 取得年
      if param_search_year and type(param_search_year) == str:
        where_params['application__start_date__gte'] = f'{param_search_year}-01-01 00:00:00' # type: ignore
        where_params['application__start_date__lte'] = f'{param_search_year}-12-31 23:59:59' # type: ignore

      # 検索条件 ステータス
      if param_search_action:
        where_params['action'] = param_search_action
      else:
        if is_admin:
          where_params['action__in'] = [TaskAction['PANDING'].value, TaskAction['COMPLETE'].value, TaskAction['REJECT'].value, TaskAction['CANCEL'].value]

      # 検索条件 申請種類
      if param_search_type:
        where_params['application__type'] = param_search_type

      # 申請タイプ情報を取得する
      application_type_result = Utils.get_application_type(request.user, Utils.get_now_to_datetime())

      total_count = Tasks.objects.filter(**where_params).count()
      task_obj = Tasks.objects.filter(**where_params).order_by('application__start_date')[int(ofset):(int(ofset) + int(limit))]

      results = []
      for task in task_obj:
        result = {
          'id': task.application.id,
          'applicationUserId': task.application.user.id,
          'type': task.application.type,
          'sType': Utils.get_application_type_name(application_type_result, task.application.type),
          'classification': task.application.classification,
          'sClassification': Utils.get_application_classification_name(application_type_result, task.application.classification, task.application.type),
          'applicationDate': None if task.action == TaskAction['DRAFT'].value else task.application.application_date,
          'sApplicationDate': None if task.action == TaskAction['DRAFT'].value else task.application.application_date.strftime('%Y/%m/%d'),
          'action': task.action,
          'sAction': TaskActionName[TaskAction(task.action).name].value,
          'startDate': task.application.start_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sStartDate': task.application.start_date.strftime('%Y/%m/%d'),
          'sStartTime': task.application.start_date.strftime('%H:%M'),
          'endDate': task.application.end_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sEndDate': task.application.end_date.strftime('%Y/%m/%d'),
          'sEndTime': task.application.end_date.strftime('%H:%M'),
          'totalTime': task.application.total_time,
          'comment': task.comment,
        }
        results.append(result)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.renderList(results, total_count, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.renderList([], 0, response.status_code, '申請情報一覧の取得中にエラーが発生しました。')

    return response


"""
  申請取得

Raises:
  exceptions.ValidationError: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    application_id = self.request.GET.get('applicationId')
    task_id = self.request.GET.get('taskId')
    is_Admin_flow = True if self.request.GET.get('isAdminFlow') == 'true' else False

    try:
      if not application_id:
        raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # 申請管理からの参照、かつログインユーザが管理者権限ではない場合、エラー
      if is_Admin_flow and request.user.is_admin is False:
        raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # 申請タスクを取得(有効または、処理済みを対象とする)
      # 必ず1件のみが取得される想定
      target_application_task = Tasks.objects.get(type=TaskType['APPLICATION'].value, application__id=application_id, status__in=[TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value])

      # タスクIDが存在する場合、タスクIDとログインユーザIDからログインユーザに紐づく承認タスクを取得
      target_approval_task = None
      if task_id:
        target_approval_task = Tasks.objects.get(id=task_id, application_id=application_id, operation_user=request.user)
      else:
        # ログインユーザが管理者権限ではないかつ、日数調整の申請情報を参照の場合、エラー
        if request.user.is_admin is False and (target_application_task.application.user != request.user or target_application_task.application.type == settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE):
          raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # 申請情報に紐づく無効ではない全タスクを取得
      tasks = Tasks.objects.filter(~Q(status=TaskStatus['NON_ACTIVE'].value), application__id=application_id).order_by('operation_date', 'id')

      # 会社に紐づく全ユーザのユーザ情報取得
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company.id).values('id', 'last_name', 'first_name')
      # 申請者のユーザ情報取得
      application_user_details = user_details_obj.filter(id=target_application_task.application.user.id).first()
      # 承認タスク一覧を取得する
      # 再申請の場合は、過去の申請タスクも取得対象に含む
      approval_tasks = ApplicationRetrieveAPIView.get_approval_tasks(tasks, target_application_task, user_details_obj)
      # 承認グループを取得する
      approval_group = ApplicationRetrieveAPIView.get_approval_group(target_application_task.application.approval_group_id, user_details_obj)
      # 申請タイプ情報を取得する
      application_type_result = Utils.get_application_type(request.user, Utils.get_now_to_datetime())

      # 編集/申請可能と見做すアクションか
      # 申請タスクの状態が「下書き」「差戻」
      is_available_edit_action = target_application_task.action in [TaskAction['DRAFT'].value, TaskAction['REJECT'].value]
      # 編集/申請可能か
      # 申請管理からの参照ではない、かつ申請者自身がログインユーザである、かつ編集/申請可能な申請タスク
      is_Edit = not is_Admin_flow and target_application_task.operation_user.id == request.user.id and is_available_edit_action
      # 「下書き」状態の場合、保存可能
      is_save_draft = target_application_task.action == TaskAction['DRAFT'].value
      # 編集可能、かつ「差戻」状態以外の場合、承認グループの変更可能
      is_edit_approval_group = is_Edit and target_application_task.action != TaskAction['REJECT'].value
      # 承認対象タスクが存在している、かつ承認タスクの状態が承認待ちの場合、承認可能
      is_approval = target_approval_task and target_approval_task.action == TaskAction['PANDING'].value
      # 編集可能、または(申請管理からの参照、かつ申請タスクの状態が「完了」「取消」以外)の場合、削除可能
      is_delete = is_Edit or (is_Admin_flow and target_application_task.action != TaskAction['COMPLETE'].value and target_application_task.action != TaskAction['CANCEL'].value)
      # 申請管理からの参照、かつ申請タスクの状態が「完了」の場合、取消可能
      is_cancel = is_Admin_flow and target_application_task.action == TaskAction['COMPLETE'].value
      result = {
        'application': {
          'id': target_application_task.application.id,
          'applicationUserId': target_application_task.application.user.id,
          'type': target_application_task.application.type,
          'sType': Utils.get_application_type_name(application_type_result, target_application_task.application.type),
          'classification': target_application_task.application.classification,
          'sClassification': Utils.get_application_classification_name(application_type_result, target_application_task.application.classification, target_application_task.application.type),
          'applicationDate': target_application_task.application.application_date,
          'sApplicationDate': target_application_task.application.application_date.strftime('%Y/%m/%d'),
          'startDate': target_application_task.application.start_date,
          'sStartDate': target_application_task.application.start_date.strftime('%Y/%m/%d'),
          'sStartTime': target_application_task.application.start_date.strftime('%H:%M'),
          'endDate': target_application_task.application.end_date,
          'sEndDate': target_application_task.application.end_date.strftime('%Y/%m/%d'),
          'sEndTime': target_application_task.application.end_date.strftime('%H:%M'),
          'totalTime': target_application_task.application.total_time,
          'approvalGroupId': target_application_task.application.approval_group_id,
          'approvalGroupName': approval_group['group_name'],
          'approvers' : approval_group['approvers'],
          'applicationUserName': application_user_details['last_name'] + " " + application_user_details['first_name'],
          'action': target_application_task.action,
          'sAction': TaskActionName[TaskAction(target_application_task.action).name].value,
          'comment': target_application_task.comment,
          'remarks': target_application_task.application.remarks,
        },
        'approvalTtasks': approval_tasks,
        'availableOperation': {
          'isEdit': is_Edit,
          'isSave': is_save_draft,
          'isEditApprovalGroup': is_edit_approval_group,
          'isApproval': is_approval,
          'isDelete': is_delete,
          'isCancel': is_cancel,
        }
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '申請情報の取得中にエラーが発生しました。')

    return response

  def get_approval_tasks(tasks: list[Tasks], target_application_task: Tasks, user_details_obj: UserDetails):
    approval_tasks = []
    for task in tasks:
      if task.id == target_application_task.id:
        continue

      operation_user_details = user_details_obj.filter(id=task.operation_user.id).first()
      approval_task = {
        'id': task.id,
        'action': task.action,
        'sAction': TaskActionName[TaskAction(task.action).name].value if task.type == TaskType['APPROVAL'].value else '申請',
        'type': task.type,
        'comment': task.comment,
        'status': task.status,
        'sStatus': TaskStatusName[TaskStatus(task.status).name].value,
        'userName': operation_user_details['last_name'] + " " + operation_user_details['first_name'],
        'operationDate': task.operation_date.strftime('%Y/%m/%d %H:%M:%S') if task.action != TaskAction['PANDING'].value else None,
      }
      approval_tasks.append(approval_task)

    return approval_tasks

  def get_approval_group(approval_group_id: int, user_details_obj):
    group = {
      'group_name': None,
      'approvers': [],
    }
    approval_group_obj = SystemSettings.objects.filter(id=approval_group_id, key='approvalGroup').first()
    print(approval_group_obj)
    if not approval_group_obj:
      return group

    approvers = []
    approval_group = JsonEncoder.toJson(approval_group_obj.value)
    group['group_name'] = approval_group['groupName']
    user_ids = [approval_group['approver1'], approval_group['approver2'], approval_group['approver3'], approval_group['approver4'], approval_group['approver5']]
    for user_id in user_ids:
      if user_id:
        user = user_details_obj.filter(id=user_id).first()
        approvers.append({
          'id': user_id,
          'name': user['last_name'] + " " + user['first_name'] if user else None,
        })
    group['approvers'] = approvers

    return group


"""
  申請

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def post(self, request):
    if not 'startDate' in request.data:
      raise exceptions.APIException('Invalid Parameter:startDate')
    if not 'endDate' in request.data:
      raise exceptions.APIException('Invalid Parameter:endDate')
    if not 'type' in request.data:
      raise exceptions.APIException('Invalid Parameter:type')
    if not 'classification' in request.data:
      raise exceptions.APIException('Invalid Parameter:classification')
    if not 'totalTime' in request.data:
      raise exceptions.APIException('Invalid Parameter:totalTime')
    if not 'comment' in request.data:
      raise exceptions.APIException('Invalid Parameter:comment')
    if not 'approvalGroupId' in request.data:
      raise exceptions.APIException('Invalid Parameter:approvalGroupId')
    if not 'action' in request.data:
      raise exceptions.APIException('Invalid Parameter:action')
    if not 'remarks' in request.data:
      raise exceptions.APIException('Invalid Parameter:remarks')

    application_id = request.data['id'] if 'id' in request.data else None
    start_date = request.data['startDate'].replace('/', '-')
    end_date = request.data['endDate'].replace('/', '-')
    start_date_time = start_date
    end_date_time = end_date

    try:
      date_now = Utils.get_now_to_string()
      application_req = {
        'id': application_id,
        'user': request.user.id,
        'type': int(request.data['type']),
        'classification': int(request.data['classification']),
        'application_date': date_now,
        'start_date': start_date_time,
        'end_date': end_date_time,
        'total_time': request.data['totalTime'],
        'approval_group_id': request.data['approvalGroupId'],
        'remarks': request.data['remarks'],
      }

      application_task_req = {
        'operation_user_id': request.user.id,
        'action': request.data['action'],
        'comment': request.data['comment'],
        'status': TaskStatus['ACTIVE'].value,
        'operation_date': date_now,
      }

      with transaction.atomic():
        where_params = {
          'operation_user': request.user,
          'application__user__company': request.user.company,
          'type': TaskType['APPLICATION'].value,
          'application__type': application_req['type'],
          'application__classification': application_req['classification'],
          'action__in': [TaskAction['DRAFT'].value, TaskAction['PANDING'].value, TaskAction['COMPLETE'].value, TaskAction['REJECT'].value],
          'status__in': [TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value],
          'application__start_date__gte': f'{start_date} 00:00:00', # type: ignore
          'application__start_date__lte': f'{end_date} 23:59:59', # type: ignore
        }
        same_day_application = Tasks.objects.filter(**where_params).first()
        if same_day_application and same_day_application.application.id != application_id:
          raise exceptions.ValidationError('重複申請です。(指定の取得日に申請種類、区分が同一の申請情報が存在します。）')

        application = None
        if not application_id is None:
          application = Applications.objects.select_for_update().get(pk=application_id, user__company=request.user.company)

        application_serializer = ApplicationSerializer(application_req, data=application_req)
        application_task_serializer = TaskSerializer(application_task_req, data=application_task_req)

        # 申請情報の登録/更新
        new_application = None
        if application_serializer.is_valid():
          if application is None:
           new_application = application_serializer.save(application_req, date_now, request.user)
          else:
            is_update_application_date = application_task_req['action'] == str(TaskAction['PANDING'].value)
            new_application = application_serializer.update(application, application_req, date_now, request.user, is_update_application_date)
        else:
          raise exceptions.APIException(application_serializer.errors)

        application_task = Tasks.objects.select_for_update().filter(application=application_id, type=TaskType['APPLICATION'].value, action__in=[TaskAction['DRAFT'].value, TaskAction['REJECT'].value], status=TaskStatus['ACTIVE'].value).first()
        if not application_task_serializer.is_valid():
          raise exceptions.APIException(application_task_serializer.errors)

        # 申請タスクの登録/更新
        if not application_task or application_task.action == TaskAction['REJECT'].value:
          application_task_serializer.save_application_task(application_task_req, date_now, new_application, request.user)
        elif application_task.action == TaskAction['DRAFT'].value:
          application_task_serializer.update_application_task(application_task, application_task_req, date_now, request.user, True)

        if application_task_req['action'] == str(TaskAction['PANDING'].value):
          # 「申請」操作の場合
          # 「差戻」状態の申請タスクが存在する場合、再申請と見做して前回申請分のタスクをクローズ
          if application_task and application_task.action == TaskAction['REJECT'].value:
            # 前回申請分の差戻状態の申請タスクをクローズする
            self.close_reject_application_task(application_task, date_now)
            # 前回申請分の承認タスクをクローズする
            self.close_old_approval_task(application.id, date_now)

          # 承認者の承認タスク作成
          self.create_approval_task(new_application.id, request.user.id, application_req['approval_group_id'], date_now)

      result = {}
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '申請処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


  # 前回申請分の差戻状態の申請タスクをクローズする
  # ステータスを「HISTORY」に更新
  def close_reject_application_task(self, application_reject_task, date_now):
    task_req = {
      'action': application_reject_task.action,
      'status': TaskStatus['HISTORY'].value,
    }
    serializer = TaskSerializer(application_reject_task, data=task_req)
    if not serializer.is_valid():
      raise exceptions.APIException(serializer.errors)

    serializer.update_application_task(application_reject_task, task_req, date_now, self.request.user, False)
    return

  # 前回申請分の承認タスクをクローズする
  # ステータスを「HISTORY」に更新
  def close_old_approval_task(self, application_id, date_now):
    tasks = Tasks.objects.select_for_update().filter(application=application_id, type=TaskType['APPROVAL'].value, status=TaskStatus['ACTIVE'].value)
    task_req = {
      'status': TaskStatus['HISTORY'].value,
    }
    for task in tasks:
      serializer = TaskSerializer(task, data=task_req)
      if not serializer.is_valid():
        raise exceptions.APIException(serializer.errors)

      serializer.update_approval_task(task, task_req, date_now, self.request.user, False)
    return

  # 承認タスク作成
  def create_approval_task(self, application_id, application_user_id, approval_group_id, date_now):
    system_configs_obj = SystemSettings.objects.get(pk= approval_group_id)
    value = JsonEncoder.toJson(system_configs_obj.value)
    approver_ids = [value['approver1'], value['approver2'], value['approver3'], value['approver4'], value['approver5']]
    for approver_id in approver_ids:
      if not approver_id or approver_id == str(application_user_id):
        continue

      task_req = {
        'application_id': application_id,
        'operation_user_id': approver_id,
        'action': TaskAction['PANDING'].value,
        'status': TaskStatus['ACTIVE'].value,
        'operation_date': date_now,
      }
      serializer = TaskSerializer(task_req, data=task_req)
      if not serializer.is_valid():
        raise exceptions.APIException(serializer.errors)

      serializer.save_approval_task(task_req, date_now, self.request.user)
    return


"""
  申請情報削除

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationDestroyAPIView(DestroyAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def destroy(self, request):
    id = self.request.GET.get('id')
    try:
      with transaction.atomic():
        application_obj = Applications.objects.select_for_update().get(pk=id)
        application_obj.delete()

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
  申請情報取消

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationCancelAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'applicationId' in request.data:
      raise exceptions.APIException('Invalid Parameter:applicationId')

    if not 'comment' in request.data:
      raise exceptions.APIException('Invalid Parameter:comment')

    application_id = request.data['applicationId']
    comment = request.data['comment']

    try:
      with transaction.atomic():
        application_obj = Applications.objects.select_for_update().get(pk=application_id)
        # ステータスが「完了」状態の申請タスクを取得
        application_task_obj = Tasks.objects.select_for_update().get(application_id=application_obj.id, type=TaskType['APPLICATION'].value, action=TaskAction['COMPLETE'].value)

        date_now = Utils.get_now_to_string()
        # 申請タスクを取消
        task_req = {
          'application_id': application_task_obj.application.id,
          'operation_user_id': application_task_obj.operation_user.id,
          'action': TaskAction['CANCEL'].value,
          'status': application_task_obj.status,
          'operation_date': date_now,
        }
        serializer = TaskSerializer(task_req, data=task_req)
        if not serializer.is_valid():
          raise exceptions.APIException(serializer.errors)

        serializer.update_application_task(application_task_obj, task_req, date_now, self.request.user, False)

        # 取消タスクを作成
        cancel_task_req = {
          'application_id': application_task_obj.application.id,
          'operation_user_id': self.request.user.id,
          'action': TaskAction['CANCEL'].value,
          'comment': comment,
          'status': TaskStatus['CLOSED'].value,
          'operation_date': date_now,
        }

        cancel_task_serializer = TaskSerializer(cancel_task_req, data=cancel_task_req)
        if not cancel_task_serializer.is_valid():
          raise exceptions.APIException(cancel_task_serializer.errors)

        cancel_task_serializer.save_approval_task(cancel_task_req, date_now, self.request.user)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '取消処理中にエラーが発生しました。')

    return response


"""
  有給休暇取得情報集計

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class AggregateApplicationAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    user_id = self.request.GET.get('userId')
    if not user_id:
      raise exceptions.APIException('Invalid Parameter:userId')

    try:
      # ユーザ詳細情報を取得する
      user_details_obj = UserDetails.objects.get(user_id=user_id)

      # 付与対象の全期間情報を配列で取得
      result_periods = []
      for period in reversed(Utils.get_grant_period(user_details_obj, Utils.get_now_to_datetime())):
        acquisition_results = []
        paid_holiday_application = Utils.get_paid_holiday_application(user_details_obj.user, period['start_date'], Utils.add_year(period['start_date'], 1))
        for acquisition_result in paid_holiday_application['acquisition_results']:
          acquisition_results.append({
            'applicationId': acquisition_result['application_id'],
            'applicationType': acquisition_result['type'],
            'applicationTypeName': acquisition_result['type_name'],
            'acquisitionDate': acquisition_result['acquisition_date'],
            'weekday': acquisition_result['weekday'],
            'totalTime': acquisition_result['total_time'],
            'action': acquisition_result['action'],
            'actionName': acquisition_result['action_name'],
            'classification': acquisition_result['classification'],
            'classificationName': acquisition_result['classification_name'],
          })

        result_periods.append({
          'startDate': period['start_date'].strftime(f'%Y/%m/%d'),
          'endDate': period['end_date'].strftime(f'%Y/%m/%d'),
          'months': period['months'],
          'grantRuleAddDays': period['grant_rule_add_days'],
          'currentYearTotalDeleteDays': paid_holiday_application['total_delete_days'],
          'currentYearTotalDeleteTime': paid_holiday_application['total_delete_time'],
          'currentYearTotalDeleteTimeHourUnit': paid_holiday_application['total_delete_time_hour_unit'],
          'isGranted': period['is_granted'],
          'isValid': period['is_valid'],
          'acquisitionResults': acquisition_results,
        })

      result = {
        'periods': result_periods,
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '集計処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  有給休暇取得実績出力

Raises:
  exceptions.ValidationError: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class OutputAggregateAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    req_user_id = request.data['userId'] if 'userId' in request.data and request.data['userId'] != '' else request.user.id
    req_months = request.data['months'] if 'months' in request.data and request.data['months'] != '' else None

    try:
      datetime_now = Utils.get_now_to_datetime()
      # ユーザ詳細情報を取得する
      user_details_obj = UserDetails.objects.get(user_id=req_user_id)

      start_str = datetime_now.strftime('%Y-%m-%d')
      end_str = datetime_now.strftime('%Y-%m-%d')
      start_end_exp = Q(Q(start_date__isnull=True, end_date__isnull=True) | Q(start_date__gte=f'{start_str} 00:00:00', end_date__lte=f'{end_str} 23:59:59'))
      # 付与ルールを取得する
      system_setting_obj = SystemSettings.objects.get(start_end_exp, company=request.user.company, key='grantRule')
      grantRule = JsonEncoder.toJson(system_setting_obj.value)

      reference_date_time = datetime.combine(user_details_obj.reference_date, time())
      mmod = monthmod(reference_date_time, datetime_now)
      months = mmod[0].months

      if mmod[0].months == 0 and datetime_now >= reference_date_time:
        months = 1

      # 経過月数から該当付与ルールのインデックスを取得する
      elapsed_period = (months + 12 - 1) // 12
      user_name = user_details_obj.last_name + " " + user_details_obj.first_name
      output_data = {
        "user_details": {
          'name': user_name,
          'joining_date': user_details_obj.joining_date.strftime(f'%Y/%m/%d')
        },
        "data" :[],
      }

      grant_rule_index = 0
      grant_rule_add_days = 0
      for i in range(elapsed_period):
        elapsed_month = 12 * i + 6
        # 対象期間が指定されている場合、対象期間以外はスキップ
        if req_months is not None and elapsed_month != int(req_months):
          continue

        for index, month in enumerate(grantRule['sectionMonth']):
          if elapsed_month == int(month):
            grant_rule_index = index
          elif elapsed_month > int(month):
            grant_rule_index = index

        # 通算月数から規定付与日数を算出する
        for working in grantRule['workingDays']:
          if user_details_obj.working_days == working['day']:
            grant_rule_add_days = working['grantDays'][grant_rule_index]
            break

        sDate = Utils.add_year(reference_date_time, i)
        eDate = Utils.sub_day(Utils.add_year(sDate, 1), 1)
        paid_holiday_application = Utils.get_paid_holiday_application(user_details_obj.user, sDate, Utils.add_year(sDate, 1), [TaskAction['COMPLETE'].value])
        output_data['data'].append({
          'index': i + 1,
          'elapsed_month': elapsed_month,
          'period': {
            'start_date': sDate.strftime('%Y/%m/%d'),
            'end_date': eDate.strftime('%Y/%m/%d'),
          },
          'grant_rule_add_days': grant_rule_add_days,
          'current_year_total_delete_days': paid_holiday_application['total_delete_days'],
          'current_year_total_delete_time': paid_holiday_application['total_delete_time'],
          'current_year_total_delete_time_hour_unit': paid_holiday_application['total_delete_time_hour_unit'],
          'acquisition_results': paid_holiday_application['acquisition_results'],
        })

      # PdfReport.make_test('{0}/{1}'.format(settings.PDF_OUTPUT_DIR_PATH, "test2.pdf"))
      file_name = '{0}/年次有給休暇取得管理台帳_{1}{2}_{3}.pdf'.format(settings.PDF_OUTPUT_DIR_PATH, user_details_obj.last_name, user_details_obj.first_name, datetime_now.strftime("%Y%m%d"))
      response = FileResponse()
      response.status_code = status.HTTP_200_OK
      # if len(output_data):
      PdfReport.make(output_data, file_name, datetime_now)

      quoted_filename = urllib.parse.quote(file_name)
      file = open(file_name, 'rb')
      response = FileResponse(file)
      response['Content-Type'] = 'application/pdf'
      response['Content-Disposition'] = 'attachment; filename="{}"'.format(quoted_filename)
      response['Access-Control-Expose-Headers'] = 'content-disposition'
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '集計処理中にエラーが発生しました。')

    return response


"""
  日数調整

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationRegulateDaysAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'userId' in request.data:
      raise exceptions.APIException('Invalid Parameter:userId')
    if not 'regulateDate' in request.data:
      raise exceptions.APIException('Invalid Parameter:regulateDate')
    if not 'timeHourUnitTotalTime' in request.data:
      raise exceptions.APIException('Invalid Parameter:timeHourUnitTotalTime')
    if not 'otherTotalTime' in request.data:
      raise exceptions.APIException('Invalid Parameter:otherTotalTime')

    try:
      with transaction.atomic():
        user_id = request.data['userId']
        regulate_date = request.data['regulateDate'].replace('/', '-')
        other_total_time = request.data['otherTotalTime']
        time_hour_unit_total_time = request.data['timeHourUnitTotalTime']
        print(user_id)
        print(regulate_date)
        print(time_hour_unit_total_time)
        print(other_total_time)

        date_now = Utils.get_now_to_string()
        other_application_req = {
          'user': request.user.id,
          'type': settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE,
          'classification': settings.APPLICATION_CLASSIFICATION_ALL_DAYS_VALUE,
          'application_date': date_now,
          'start_date': regulate_date,
          'end_date': regulate_date,
          'total_time': int(other_total_time) * 8,
          'approval_group_id': 0,
          'remarks': '',
        }

        time_hour_unit_application_req = {
          'user': request.user.id,
          'type': settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE,
          'classification': settings.APPLICATION_CLASSIFICATION_TIME_VALUE,
          'application_date': date_now,
          'start_date': regulate_date,
          'end_date': regulate_date,
          'total_time': int(time_hour_unit_total_time),
          'approval_group_id': 0,
          'remarks': '',
        }

        if int(other_total_time) != 0:
          ApplicationRegulateDaysAPIView.save(request.user, other_application_req, date_now)
        if int(time_hour_unit_total_time) != 0:
          ApplicationRegulateDaysAPIView.save(request.user, time_hour_unit_application_req, date_now)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '日数処理中にエラーが発生しました。')

    return response

  def save(user, application_req, date_now):
    application_task_req = {
      'operation_user_id': user.id,
      'action': TaskAction['COMPLETE'].value,
      'comment': '日数調整',
      'status': TaskStatus['CLOSED'].value,
      'operation_date': date_now,
    }

    application_serializer = ApplicationSerializer(application_req, data=application_req)
    application_task_serializer = TaskSerializer(application_task_req, data=application_task_req)

    if not application_serializer.is_valid():
      raise exceptions.APIException(application_serializer.errors)
    if not application_task_serializer.is_valid():
      raise exceptions.APIException(application_task_serializer.errors)

    # 申請情報の登録
    new_application = application_serializer.save(application_req, date_now, user)
    # 申請タスクの登録
    application_task_serializer.save_application_task(application_task_req, date_now, new_application, user)

    return
