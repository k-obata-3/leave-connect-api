from django.conf import settings
from decimal import Decimal
import datetime
import hashlib


class Utils():

  def getApplicationHour(totalTime):
    if(totalTime == 8):
      return Decimal(1)
    elif(totalTime == 4):
      return Decimal(0.5)
    else:
      return Decimal(0.125 * totalTime)

  def getNow():
    return datetime.datetime.now()

  def getInitialPasswordHash(self, user_id):
    return self.getPasswordHash(settings.INITIAL_PASSWORD, user_id)

  def getPasswordHash(password, user_id):
    raw = password + settings.PASS_SECRET_SALT + user_id
    return hashlib.sha1(raw.encode()).hexdigest()
