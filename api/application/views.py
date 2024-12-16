import traceback
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from config.renderers import JSONRenderer
from config.jsonEncoder import JsonEncoder
from config.enum import TaskType, TaskTypeName, TaskStatus, TaskStatusName, TaskAction, TaskActionName, ApplicationClassification, ApplicationClassificationName, ApplicationType, ApplicationTypeName
from config.responseRenderers import ResponseRenderers
from authentications.views import JWTAuthentication
from application.serializers import ApplicationSerializer, TaskSerializer
from users.serializers import UserDetailsSerializer
from django.db.models import Q
from application.models import Application, Task
from users.models import UserDetails
from systemsettings.models import SystemConfigs
from django.db import transaction
from datetime import datetime, timedelta, timezone
from config.utils import Utils
# from datetime import datetime
# from zoneinfo import ZoneInfo
# import time
import json
# from django.http.response import JsonResponse


class NotificationRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      application_task_obj = Task.objects.filter(operation_user=request.user.id, status=TaskStatus['ACTIVE'].value, type=TaskType['APPLICATION'].value, action__in=[TaskAction['PANDING'].value, TaskAction['REJECT'].value]).all()
      approval_task_obj = Task.objects.filter(operation_user=request.user.id, status=1, type=1, action=1).all()

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
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '通知情報の取得中にエラーが発生しました。')
    

    return response

"""
  月間の申請一覧取得
Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_
  exceptions.APIException: _description_
  exceptions.NotFound: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationMonthListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]
  # renderer_classes = (JSONRenderer)
  serializer_class = TaskSerializer
  queryset = Task.objects.all()

  def get(self, request):
    start = self.request.GET.get('start')
    end = self.request.GET.get('end')

    if not start:
      raise exceptions.ValidationError('Invalid Parameter:start')
    if not end:
      raise exceptions.ValidationError('Invalid Parameter:end')

    try:
      task_obj = self.queryset.filter(~Q(action=5), operation_user=request.user.id, type=0, status=1, application__start_date__gte=start, application__start_date__lte=end).all()
      results = []
      for task in task_obj:
        result = {
          'id': task.application.id,
          'applicationUserId': task.application.user.id,
          'type': task.application.type,
          'sType': ApplicationTypeName[ApplicationType(task.application.type).name].value,
          'classification': task.application.classification,
          'sClassification': ApplicationClassificationName[ApplicationClassification(task.application.classification).name].value,
          'action': task.action,
          'sAction': TaskActionName[TaskAction(task.action).name].value,
          'startDate': task.application.start_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sStartDate': task.application.start_date.strftime('%Y-%m-%d'),
          'sStartTime': task.application.start_date.strftime('%H:%M'),
          'endDate': task.application.end_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sEndDate': task.application.end_date.strftime('%Y-%m-%d'),
          'sEndTime': task.application.end_date.strftime('%H:%M'),
        }
        results.append(result)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(results, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # response = Response()
      # response.status_code = e.args[1]
      # response.data = e.args[0]
      # return response
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '申請情報一覧の取得中にエラーが発生しました。')

    return response


"""
  申請一覧取得
Raises:
  exceptions.APIException: _description_
  exceptions.NotFound: _description_
  exceptions.NotFound: _description_
  exceptions.APIException: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class ApplicationListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]
  serializer_class = TaskSerializer
  queryset = Task.objects.all()

  def get(self, request):
    param_is_admin = self.request.GET.get('isAdmin')
    param_user_id = self.request.GET.get('userId')
    param_search_action = self.request.GET.get('searchAction')
    param_search_year = self.request.GET.get('searchYear')
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.ValidationError('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.ValidationError('Invalid Parameter:ofset')
    
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

      # 検索条件 申請年
      if param_search_year and type(param_search_year) == str:
        where_params['application__start_date__gte'] = f'{param_search_year}-01-01 00:00:00' # type: ignore
        where_params['application__start_date__lte'] = f'{param_search_year}-12-31 23:59:59' # type: ignore

      # 検索条件 状況
      if param_search_action:
        where_params['action'] = param_search_action
      else:
        if is_admin:
          where_params['action__in'] = [TaskAction['PANDING'].value, TaskAction['COMPLETE'].value, TaskAction['REJECT'].value, TaskAction['CANCEL'].value]

      total_count = self.queryset.filter(**where_params).count()
      task_obj = self.queryset.filter(**where_params).all()[int(ofset):(int(ofset) + int(limit))]
      results = []
      for task in task_obj:
        result = {
          'id': task.application.id,
          'applicationUserId': task.application.user.id,
          'type': task.application.type,
          'sType': ApplicationTypeName[ApplicationType(task.application.type).name].value,
          'classification': task.application.classification,
          'sClassification': ApplicationClassificationName[ApplicationClassification(task.application.classification).name].value,
          'applicationDate': task.application.application_date,
          'sApplicationDate': task.application.application_date.strftime('%Y/%m/%d'),
          'action': task.action,
          'sAction': TaskActionName[TaskAction(task.action).name].value,
          'startDate': task.application.start_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sStartDate': task.application.start_date.strftime('%Y/%m/%d'),
          'sStartTime': task.application.start_date.strftime('%H:%M'),
          'endDate': task.application.end_date.strftime('%Y-%m-%d %H:%M:%S'),
          'sEndDate': task.application.end_date.strftime('%Y/%m/%d'),
          'sEndTime': task.application.end_date.strftime('%H:%M'),
          'comment': task.comment,
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
      response.data = ResponseRenderers.renderList([], 0, response.status_code, '申請情報一覧の取得中にエラーが発生しました。')

    return response


class ApplicationRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    application_id = self.request.GET.get('applicationId')
    task_id = self.request.GET.get('taskId')
    is_Admin_flow = True if self.request.GET.get('isAdminFlow') == 'true' else False

    try:
      # 申請管理からの参照、かつログインユーザが管理者権限ではない場合、エラー
      if is_Admin_flow and not request.user.is_admin:
        raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # タスクIDが存在する場合、そのタスクがログインユーザに割り振られているかチェック、割り振られていない場合はエラー
      target_approval_task = None
      if task_id:
        target_approval_task = Task.objects.get(id=task_id, application_id=application_id, operation_user=request.user)
        if not target_approval_task:
          raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # ログインユーザが承認者に設定されている有効な承認タスク取得
      # available_approval_task = task_obj.filter(operation_user=request.user, type=TaskType['APPROVAL'].value, status__in=[TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value, TaskStatus['HISTORY'].value]).first()

      # 参照権限がない申請情報を取得しようとした場合、エラーとする
      # if(not request.user.is_admin and not available_approval_task and application_obj.user.id != request.user.id):
        # raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # 申請情報を取得
      application_obj = Application.objects.get(pk=application_id, user__company=request.user.company)
      if not application_obj:
        raise exceptions.NotFound('申請情報の取得に失敗しました。')

      # 申請情報に紐づく無効ではない全タスクを取得
      task_obj = Task.objects.filter(~Q(status=TaskStatus['NON_ACTIVE'].value), application__id=application_id).all().order_by('operation_date', 'id')

      # 会社に紐づく全ユーザのユーザ情報取得
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company.id).values('id', 'last_name', 'first_name').all()

      # 申請タスク取得(有効または、処理済みを対象とする)
      application_task = task_obj.get(type=TaskType['APPLICATION'].value, status__in=[TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value])
      application_user_details = user_details_obj.filter(id=application_obj.user.id).first()

      approval_tasks = []
      for task in task_obj.filter(~Q(id=application_task.id)).all():
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

      # 承認グループの承認者名取得
      approval_group_obj = SystemConfigs.objects.all().filter(id=application_obj.approval_group_id).first()
      approval_group_name = None
      approvers = []
      if approval_group_obj:
        approval_group = json.loads(approval_group_obj.value)
        approval_group_name = approval_group['groupName']
        user_ids = [approval_group['approver1'], approval_group['approver2'], approval_group['approver3'], approval_group['approver4'], approval_group['approver5']]
        for user_id in user_ids:
          if user_id:
            user = user_details_obj.filter(id=user_id).first()
            approvers.append({
              'id': user_id,
              'name': user['last_name'] + " " + user['first_name'] if user else None,
            })

      # 申請管理からの参照ではない、かつ申請者自身がログインユーザである、かつ申請タスクの状態が「下書き」「差戻」の場合、編集/申請可能
      is_Edit = not is_Admin_flow and application_task.operation_user.id == request.user.id and (application_task.action == TaskAction['DRAFT'].value or application_task.action == TaskAction['REJECT'].value)
      # 「下書き」状態の場合、保存可能
      is_save_draft = application_task.action == TaskAction['DRAFT'].value
      # 編集可能、かつ「差戻」状態以外の場合、承認グループの変更可能
      is_edit_approval_group = is_Edit and application_task.action != TaskAction['REJECT'].value
      # 承認対象タスクが存在している、かつ承認タスクの状態が承認待ちの場合、承認可能
      is_approval = target_approval_task and target_approval_task.action == TaskAction['PANDING'].value
      # 編集可能、または(申請管理からの参照、かつ申請タスクの状態が「完了」「取消」以外)の場合、削除可能
      is_delete = is_Edit or (is_Admin_flow and application_task.action != TaskAction['COMPLETE'].value and application_task.action != TaskAction['CANCEL'].value)
      # 申請管理からの参照、かつ申請タスクの状態が「完了」の場合、取消可能
      is_cancel = is_Admin_flow and application_task.action == TaskAction['COMPLETE'].value
      result = {
        'application': {
          'id': application_obj.id,
          'applicationUserId': application_obj.user.id,
          'type': application_obj.type,
          'sType': ApplicationTypeName[ApplicationType(application_obj.type).name].value,
          'classification': application_obj.classification,
          'sClassification': ApplicationClassificationName[ApplicationClassification(application_obj.classification).name].value,
          'applicationDate': application_obj.application_date,
          'sApplicationDate': application_obj.application_date.strftime('%Y/%m/%d'),
          'startDate': application_obj.start_date,
          'sStartDate': application_obj.start_date.strftime('%Y/%m/%d'),
          'sStartTime': application_obj.start_date.strftime('%H:%M'),
          'endDate': application_obj.end_date,
          'sEndDate': application_obj.end_date.strftime('%Y/%m/%d'),
          'sEndTime': application_obj.end_date.strftime('%H:%M'),
          'totalTime': application_obj.total_time,
          'approvalGroupId': application_obj.approval_group_id,
          'approvalGroupName': approval_group_name,
          'approvers' : approvers,
          'applicationUserName': application_user_details['last_name'] + " " + application_user_details['first_name'],
          'action': application_task.action,
          'sAction': TaskActionName[TaskAction(application_task.action).name].value,
          'comment': application_task.comment,
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
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '申請情報の取得中にエラーが発生しました。')

    return response


class ApplicationAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'startEndDate' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:startEndDate')
    if not 'startTime' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:startTime')
    if not 'endTime' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:endTime')
    if not 'type' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:type')
    if not 'classification' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:classification')
    if not 'totalTime' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:totalTime')
    if not 'comment' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:comment')
    if not 'approvalGroupId' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:approvalGroupId')
    if not 'action' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:action')

    application_id = request.data['id'] if 'id' in request.data else None
    start_end_date = request.data['startEndDate'].replace('/', '-')
    start_date = start_end_date + ' ' + request.data['startTime']
    end_date = start_end_date + ' ' + request.data['endTime']

    t_delta = timedelta(hours=9)
    JST = timezone(t_delta, 'JST')
    date_now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    try:
      # 開始時間と終了時間の差分を取得
      start_date_obj = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
      end_date_obj = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
      time_diff = end_date_obj - start_date_obj
      max_working_seconds = 60 * 60 * 9

      # 差分が9時間（休憩時間含む）を超えている場合は、1日の所定労働時間を超過しているためエラーとする
      if(time_diff.seconds > max_working_seconds):
        raise exceptions.ValidationError('取得時間が不正です。※取得時間は1日の所定労働時間を超えないように入力してください。')

      classification = str(request.data['classification'])
      is_all_days = time_diff.seconds == max_working_seconds
      is_half_days_am = start_date_obj.hour < 12 and (start_date_obj.hour + 4 == end_date_obj.hour or start_date_obj.hour + 5 == end_date_obj.hour)
      is_half_days_pm = start_date_obj.hour >= 12 and start_date_obj.hour + 4 == end_date_obj.hour
      if classification != str(ApplicationClassification['ALL_DAYS'].value) and is_all_days:
        raise exceptions.ValidationError('区分が不正です。※取得時間が区分「全日」の条件を満たしています。')

      if classification == str(ApplicationClassification['ALL_DAYS'].value) and not is_all_days:
        raise exceptions.ValidationError('取得時間が不正です。※取得時間が区分「全日」の条件を満たしていません。')

      if classification == str(ApplicationClassification['HALF_DAYS_AM'].value) and not is_half_days_am:
        raise exceptions.ValidationError('取得時間が不正です。※取得時間が区分「AM半休」の条件を満たしていません。')

      if classification == str(ApplicationClassification['HALF_DAYS_PM'].value) and not is_half_days_pm:
        raise exceptions.ValidationError('取得時間が不正です。※取得時間が区分「PM半休」の条件を満たしていません。')

      application_req = {
        'id': application_id,
        'user': request.user.id,
        'type': request.data['type'],
        'classification': request.data['classification'],
        'application_date': date_now,
        'start_date': start_date,
        'end_date': end_date,
        'total_time': request.data['totalTime'],
        'approval_group_id': request.data['approvalGroupId'],
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
          'application__classification': application_req['classification'],
          'action__in': [TaskAction['DRAFT'].value, TaskAction['PANDING'].value, TaskAction['COMPLETE'].value, TaskAction['REJECT'].value],
          'status__in': [TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value],
          'application__start_date__gte': f'{start_end_date} 00:00:00', # type: ignore
          'application__start_date__lte': f'{start_end_date} 23:59:59', # type: ignore
        }
        same_day_application = Task.objects.filter(**where_params).first()
        if same_day_application and same_day_application.application.id != application_id:
          raise exceptions.ValidationError('取得日および区分が同じ申請情報が登録済みです。')

        application = None
        if not application_id is None:
          application = Application.objects.select_for_update().get(pk=application_id, user__company=request.user.company)

        application_serializer = ApplicationSerializer(application_req, data=application_req)
        application_task_serializer = TaskSerializer(application_task_req, data=application_task_req)

        # 申請情報の登録/更新
        new_application = None
        if application_serializer.is_valid():
          if application is None:
           new_application = application_serializer.save(application_req, date_now, request.user)
          else:
            is_update_application_date = application_task_req['action'] == str(TaskAction['PANDING'].value)
            new_application = application_serializer.update(application, application_req, date_now, is_update_application_date)
        else:
          print('【ERROR】:' + application_serializer.error_messages['invalid'])

        application_task = Task.objects.select_for_update().filter(application=application_id, type=TaskType['APPLICATION'].value, action__in=[TaskAction['DRAFT'].value, TaskAction['REJECT'].value], status=TaskStatus['ACTIVE'].value).first()
        if not application_task_serializer.is_valid():
          print('【ERROR】:' + application_task_serializer.error_messages['invalid'])
          raise exceptions.APIException('エラーが発生しました。')

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
      print('【ERROR】:' + serializer.error_messages['invalid'])
      raise exceptions.APIException('エラーが発生しました。')

    serializer.update_application_task(application_reject_task, task_req, date_now, self.request.user, False)
    return

  # 前回申請分の承認タスクをクローズする
  # ステータスを「HISTORY」に更新
  def close_old_approval_task(self, application_id, date_now):
    tasks = Task.objects.select_for_update().filter(application=application_id, type=TaskType['APPROVAL'].value, status=TaskStatus['ACTIVE'].value).all()
    task_req = {
      'status': TaskStatus['HISTORY'].value,
    }
    for task in tasks:
      serializer = TaskSerializer(task, data=task_req)
      if not serializer.is_valid():
        print('【ERROR】:' + serializer.error_messages['invalid'])
        raise exceptions.APIException('エラーが発生しました。')

      serializer.update_approval_task(task, task_req, date_now, self.request.user, False)
    return
  
  # 承認タスク作成
  def create_approval_task(self, application_id, application_user_id, approval_group_id, date_now):
    system_configs_obj = SystemConfigs.objects.get(pk= approval_group_id)
    value = json.loads(system_configs_obj.value)
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
        print('【ERROR】:' + serializer.error_messages['invalid'])
        raise exceptions.APIException('エラーが発生しました。')

      serializer.save_approval_task(task_req, date_now, self.request.user)
    return

# 申請情報削除
class ApplicationDestroyAPIView(DestroyAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def destroy(self, request):
    id = self.request.GET.get('id')
    try:
      with transaction.atomic():
        application_obj = Application.objects.select_for_update().get(pk=id)
        application_task_obj = Task.objects.select_for_update().get(application_id=application_obj.id, type=TaskType['APPLICATION'].value, action__in=[TaskAction['DRAFT'].value, TaskAction['PANDING'].value, TaskAction['REJECT'].value], status=TaskStatus['ACTIVE'].value)

        if not application_task_obj:
          raise exceptions.APIException('削除に失敗しました。')

        application_obj.delete()

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

# 申請情報取消
class ApplicationCancelAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def post(self, request):
    if not 'applicationId' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:applicationId')

    if not 'comment' in request.data:
      raise exceptions.ValidationError('Invalid Parameter:comment')

    application_id = request.data['applicationId']
    comment = request.data['comment']

    try:
      with transaction.atomic():
        application_obj = Application.objects.select_for_update().get(pk=application_id)
        # ステータスが「完了」状態の申請タスクを取得
        application_task_obj = Task.objects.select_for_update().get(application_id=application_obj.id, type=TaskType['APPLICATION'].value, action=TaskAction['COMPLETE'].value)

        if not application_task_obj:
          raise exceptions.APIException('取消に失敗しました。')

        t_delta = timedelta(hours=9)
        JST = timezone(t_delta, 'JST')
        date_now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

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
          print('【ERROR】:' + serializer.error_messages['invalid'])
          raise exceptions.APIException('エラーが発生しました。')

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
          print('【ERROR】:' + cancel_task_serializer.error_messages['invalid'])
          raise exceptions.APIException('エラーが発生しました。')

        cancel_task_serializer.save_approval_task(cancel_task_req, date_now, self.request.user)

        # 年次有給休暇申請の場合、取得日数から減算する
        if application_obj.type == ApplicationType['PAID_HOLIDAY'].value:
          self.recalculationForTotalDeleteDays(application_obj, date_now)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.APIException('エラーが発生しました。')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, '取消処理中にエラーが発生しました。')

    return response

  # 取得日数に加算する
  def recalculationForTotalDeleteDays(self, application, date_now):
    user_details_obj = UserDetails.objects.select_for_update().get(user__id=application.user.id)
    result_hours = Utils.getApplicationHour(application.total_time)

    req = {
      'auto_calc_remaining_days': user_details_obj.auto_calc_remaining_days + result_hours,
      'total_delete_days': user_details_obj.total_delete_days - result_hours
    }
    print(req)
    serializer = UserDetailsSerializer(user_details_obj, data=req)
    if not serializer.is_valid():
      print('【ERROR】:' + serializer.error_messages['invalid'])
      raise exceptions.APIException('エラーが発生しました。')

    serializer.update(user_details_obj, req, date_now, self.request.user)

    return
