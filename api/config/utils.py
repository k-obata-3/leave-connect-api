from django.conf import settings
from decimal import Decimal
import datetime
import hashlib
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod


class Utils():
  t_delta = datetime.timedelta(hours=9)
  JST = datetime.timezone(t_delta, 'JST')

  def get_application_hour(totalTime):
    if(totalTime == 8):
      return Decimal(1)
    elif(totalTime == 4):
      return Decimal(0.5)
    else:
      return Decimal(0.125 * totalTime)

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

  # 経過年数取得(初日を含まない)
  def get_service_years(dt1, dt2):
    mmod = monthmod(dt1, dt2)
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
