from django.conf import settings
from decimal import Decimal
import datetime
import hashlib
import math
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod

from django.db.models import Q, Sum

from config.jsonEncoder import JsonEncoder
from config.enum import TaskType, TaskStatus, TaskAction, TaskActionName, WeekDayName
from users.models import UserDetails, GrantHistories
from systemsettings.models import SystemSettings
from application.models import Tasks


class Utils():
  t_delta = datetime.timedelta(hours=9)
  JST = datetime.timezone(t_delta, 'JST')

  def convert_application_hours_to_days(total_time: int):
    return Decimal(0.125 * total_time)

  def getNow():
    return datetime.datetime.now()

  def get_initial_password_hash(self, user):
    if user is None:
      return ''

    return self.get_password_hash(settings.INITIAL_PASSWORD, user)

  def get_password_hash(password, user):
    if password is None or user is None:
      return ''

    raw = password + settings.PASS_SECRET_SALT + str(user.company.id) + str(user.id)
    return hashlib.sha1(raw.encode()).hexdigest()

  # 経過期間取得(初日を含まない)
  def get_elapsed_period(dt1, dt2):
    mmod = monthmod(dt1, dt2)
    # 未来日の場合、負の値となるため経過期間は0として返却
    if mmod[0].months//12 < 0:
      return (0, 0, 0)

    return (mmod[0].months//12, mmod[0].months, mmod[0].months%12)

  def add_year(dt, year):
    return dt + relativedelta(years=+year)
  
  def sub_year(dt, year):
    return dt + relativedelta(years=-year)

  def add_month(dt, month):
    return dt + relativedelta(months=+month)

  def sub_month(dt, month):
    return dt + relativedelta(months=-month)

  def add_day(dt, day):
    return dt + relativedelta(days=+day)

  def sub_day(dt, day):
    return dt + relativedelta(days=-day)

  def get_now_to_datetime():
    date_now = datetime.datetime.now(Utils.JST)
    return datetime.datetime(date_now.year, date_now.month, date_now.day)

  def get_now_to_string():
    return datetime.datetime.now(Utils.JST).strftime('%Y-%m-%d %H:%M:%S')

  def get_application_type(user, datetime_now):
    application_type_result = [
      Utils.get_application_type_paid(),
      Utils.get_application_type_regulate(),
    ]
    start_str = datetime_now.strftime('%Y-%m-%d')
    end_str = datetime_now.strftime('%Y-%m-%d')
    start_end_exp = Q(Q(start_date__isnull=True, end_date__isnull=True) | Q(start_date__gte=f'{start_str} 00:00:00', end_date__lte=f'{end_str} 23:59:59'))
    application_type_obj = SystemSettings.objects.filter(start_end_exp, company=user.company, key='applicationType')
    for application_type in application_type_obj:
      application_type_result.append(JsonEncoder.toJson(application_type.value))

    return application_type_result

  def get_application_type_paid():
    return {
      "type": "PAID",
      "name": "年次有給休暇申請",
      "value": settings.PAID_HOLIDAY_TYPE_VALUE,
      "format": "time",
      "initialValue": {
        "classification": settings.APPLICATION_CLASSIFICATION_ALL_DAYS_VALUE,
        "totalTime": 8
      },
      "classifications": [
        {
          "key": "ALL_DAYS",
          "name": "全日",
          "value": settings.APPLICATION_CLASSIFICATION_ALL_DAYS_VALUE,
          "min": 8,
          "max": 8
        },
        {
          "key": "HALF_DAYS_AM",
          "name": "AM半休",
          "value": 1,
          "min": 4,
          "max":4
        },
        {
          "key": "HALF_DAYS_PM",
          "name": "PM半休",
          "value": 2,
          "min": 4,
          "max": 4
        },
        {
          "key": "TIME",
          "name": "時間単位",
          "value": settings.APPLICATION_CLASSIFICATION_TIME_VALUE,
          "min": 1,
          "max": 7
        }
      ]
    }

  def get_application_type_regulate():
    return {
      "type": "REGULATE",
      "name": "日数調整",
      "value": settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE,
      "format": "time",
      "initialValue": {
        "classification": settings.APPLICATION_CLASSIFICATION_ALL_DAYS_VALUE,
        "totalTime": 8
      },
      "classifications": [
        {
          "key": "ALL_DAYS",
          "name": "全日",
          "value": settings.APPLICATION_CLASSIFICATION_ALL_DAYS_VALUE,
          "min": 8,
          "max": 8
        },
        {
          "key": "TIME",
          "name": "時間単位",
          "value": settings.APPLICATION_CLASSIFICATION_TIME_VALUE,
          "min": 1,
          "max": 7
        }
      ]
    }

  def get_application_type_value(application_types, key):
    if not application_types:
      return ''

    for application_type in application_types:
      if set(application_type) < {'type', 'name', 'format', 'initialValue', 'classifications'}:
        continue
      if application_type['type'] == key:
        return application_type['value']

    return ''

  def get_application_type_name(application_types, val):
    if not application_types:
      return ''
    
    for application_type in application_types:
      if set(application_type) < {'type', 'name', 'format', 'initialValue', 'classifications'}:
        continue
      if application_type['value'] == val:
        return application_type['name']

    return ''

  def get_application_type_format(application_types, val):
    if not application_types:
      return ''
    
    for application_type in application_types:
      if set(application_type) < {'type', 'name', 'format', 'initialValue', 'classifications'}:
        continue
      if application_type['value'] == val:
        return application_type['format']

    return ''

  def get_application_classification_value(application_types, key, application_type_val):
    if not application_types:
      return ''

    for at in application_types:
      if set(at) < {'type', 'name', 'format', 'initialValue', 'classifications'}:
        continue
      if at['value'] == application_type_val:
        for ac in at['classifications']:
          if set(ac) < {'key', 'name', 'value', 'min', 'max'}:
            continue
          if ac['key'] == key:
            return ac['value']

    return ''

  def get_application_classification_name(application_types, val, application_type_val):
    if not application_types:
      return ''

    for at in application_types:
      if set(at) < {'type', 'name', 'format', 'initialValue', 'classifications'}:
        continue
      if at['value'] == application_type_val:
        for ac in at['classifications']:
          if set(ac) < {'key', 'name', 'value', 'min', 'max'}:
            continue
          if ac['value'] == val:
            return ac['name']

    return ''

  def get_age(date_of_birth):
    date_now = Utils.getNow()
    this_birthday = datetime.datetime(date_now.year, date_of_birth.month, date_of_birth.day)
    age = date_now.year - date_of_birth.year
    if(date_now < this_birthday):
      return str(age -1)

    return str(age)

  def get_total_add_days(grant_history_obj):
    if grant_history_obj.exists() is False:
      return 0

    add_days_sum = grant_history_obj.aggregate(sum=Sum("add_days"))
    total_add_days = 0 if add_days_sum['sum'] is None else add_days_sum['sum']
    return total_add_days

  def get_total_remaining_days(grant_history_obj, total_add_days: int):
    if grant_history_obj.exists() is False:
      return total_add_days

    # 消化合計時間(時間単位分を除いた合計時間)を合算
    total_delete_time_sum = grant_history_obj.aggregate(sum=Sum("total_delete_time"))
    total_delete_time = 0 if total_delete_time_sum['sum'] is None else total_delete_time_sum['sum']
    # 消化合計時間(時間単位分)を合算
    total_delete_time_hour_unit_sum = grant_history_obj.aggregate(sum=Sum("total_delete_time_hour_unit"))
    total_delete_time_hour_unit = 0 if total_delete_time_hour_unit_sum['sum'] is None else total_delete_time_hour_unit_sum['sum']
    # 消化時間を日換算
    total = total_delete_time + total_delete_time_hour_unit
    total_delete_days = total / 8 if total > 0 else 0

    return total_add_days - total_delete_days

  def get_grant_current_period(reference_date: datetime, total_month: int):
    # total_month = 基準日から現在日付までの通算月数
    # 通算月数を12(ヶ月)で割った値の小数点以下切り捨てした値を係数として、現在年に換算した付与対象期間の開始日、終了日を算出する
    YEAR_MONTH = 12
    coef = math.floor(total_month//YEAR_MONTH)
    period_start = Utils.add_month(reference_date, coef * YEAR_MONTH)
    period_end = Utils.sub_day(Utils.add_month(period_start, YEAR_MONTH), 1)

    return (period_start, period_end)

  # 付与対象の全期間情報を配列で取得
  def get_grant_period(user_details_obj: UserDetails, datetime_now: datetime):
    # 付与ルールを取得する
    start_str = datetime_now.strftime('%Y-%m-%d')
    end_str = datetime_now.strftime('%Y-%m-%d')
    start_end_exp = Q(Q(start_date__isnull=True, end_date__isnull=True) | Q(start_date__gte=f'{start_str} 00:00:00', end_date__lte=f'{end_str} 23:59:59'))
    system_setting_obj = SystemSettings.objects.get(start_end_exp, company=user_details_obj.user.company_id, key='grantRule')
    grantRule = JsonEncoder.toJson(system_setting_obj.value)

    reference_date_time = datetime.datetime(user_details_obj.reference_date.year, user_details_obj.reference_date.month, user_details_obj.reference_date.day)
    mmod = monthmod(reference_date_time, datetime_now)
    months = mmod[0].months

    if mmod[0].months == 0 and datetime_now >= reference_date_time:
      months = 1

    elapsed_period = (months + 12 - 1) // 12
    grant_periods = []
    grant_rule_index = 0
    grant_rule_add_days = 0
    for i in range(elapsed_period):
      elapsed_month = 12 * i + 6
      for index, month in enumerate(grantRule['sectionMonth']):
        if elapsed_month == int(month):
          grant_rule_index = index
        elif elapsed_month > int(month):
          grant_rule_index = index

      # 通算月数と所定労働日数から規定付与日数を算出する
      for working in grantRule['workingDays']:
        if user_details_obj.working_days == working['day']:
          grant_rule_add_days = working['grantDays'][grant_rule_index]
          break

      grant_history_obj = GrantHistories.objects.filter(user=user_details_obj.user.id, elapsed_month=elapsed_month)
      is_granted = False
      start_date = Utils.add_year(reference_date_time, i)
      end_date = Utils.sub_day(Utils.add_year(start_date, 1), 1)
      extinction_date = Utils.sub_day(Utils.add_year(start_date, settings.APPLICATION_CARRYOVER_DEADLINE), 1)
      is_valid = extinction_date >= datetime_now
      if grant_history_obj.exists():
        is_granted = True

      grant_periods.append({
        'months': elapsed_month,                        # 通算月数
        'grant_rule_add_days': grant_rule_add_days,     # 付与日数
        'start_date': start_date,                       # 対象期間(開始日)
        'end_date': end_date,                           # 対象期間(終了日)
        'is_granted': is_granted,                       # 付与済みか否か
        'is_valid': is_valid,                           # 有効か否か
      })

    return grant_periods

  """
    有給休暇申請情報を取得
    start_date <= 申請日 < end_date

  """
  def get_paid_holiday_application(user, start_date, end_date, actions=[TaskAction['PANDING'].value, TaskAction['REJECT'].value, TaskAction['COMPLETE'].value]):
    # 申請タイプ情報を取得する
    application_type_result = Utils.get_application_type(user, Utils.get_now_to_datetime())

    where_params = {
      'application__user_id': user.id,
      'type': TaskType['APPLICATION'].value,
      'application__type__in': [settings.PAID_HOLIDAY_TYPE_VALUE, settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE],
      'action__in': actions,
      'status__in': [TaskStatus['ACTIVE'].value, TaskStatus['CLOSED'].value],
      'application__start_date__gte': start_date,
      'application__end_date__lt': end_date,
    }

    application_task_obj = Tasks.objects.filter(**where_params).order_by('application__start_date')
    result = {
      'acquisition_results': [],
      'start_date': start_date,
      'end_date': end_date,
      'total_delete_days': 0,
      'total_delete_time': 0,
      'total_delete_time_hour_unit': 0,
    }
    total_delete_time = 0
    total_delete_time_hour_unit = 0
    for task in application_task_obj:
      # 承認完了の申請情報のみ取得実績として計上する
      if task.action == TaskAction['COMPLETE'].value:
        if task.application.classification == settings.APPLICATION_CLASSIFICATION_TIME_VALUE:
          # 消化合計時間(時間単位分)
          total_delete_time_hour_unit += task.application.total_time
        else:
          # 消化合計時間(時間単位分を除いた合計時間)
          total_delete_time += task.application.total_time

      application_data = {
        'application_id': task.application.id,
        'acquisition_date': task.application.start_date.strftime('%Y/%m/%d'),
        'type': task.application.type,
        'type_name': Utils.get_application_type_name(application_type_result, task.application.type),
        'weekday': WeekDayName.SHORT_NAME.value[task.application.start_date.weekday()],
        'total_time': task.application.total_time,
        'action': task.action,
        'action_name': TaskActionName[TaskAction(task.action).name].value,
        'classification': task.application.classification,
        'classification_name': Utils.get_application_classification_name(application_type_result, task.application.classification, task.application.type),
      }

      result['acquisition_results'].append(application_data)

    result['total_delete_days'] = total_delete_time // 8 if total_delete_time % 8 == 0 else total_delete_time / 8
    result['total_delete_time'] = total_delete_time
    result['total_delete_time_hour_unit'] = total_delete_time_hour_unit

    return result
