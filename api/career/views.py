import traceback
import glob
import os
from datetime import datetime, time
from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.conf import settings
from django.http import FileResponse
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView

from config.utils import Utils
from config.jsonEncoder import JsonEncoder
from config.responseRenderers import ResponseRenderers
from config.enum import CareerItemKey
from .excelReportWithOpenpyxl import ExcelReportWithOpenpyxl

from authentications.views import JWTAuthentication, IsAuthenticated

from users.models import User
from career.models import Career
from career.models import CareerItem
from career.models import CareerMaster
from users.models import User, UserDetails

from career.serializers import CareerSerializer, CareerItemSerializer, CareerMasterSerializer
import urllib.parse


"""
  保有スキル一覧取得

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class CareerUserListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    if not limit:
      raise exceptions.APIException('Invalid Parameter:limit')
    if not ofset:
      raise exceptions.APIException('Invalid Parameter:ofset')

    try:
      date_now = Utils.get_now_to_datetime()
      total_count = UserDetails.objects.filter(user__company=request.user.company).count()
      user_details_obj = UserDetails.objects.filter(user__company=request.user.company)[int(ofset):(int(ofset) + int(limit))]

      results = []
      for user_details in user_details_obj:
        career_item_obj = CareerItem.objects.filter(career__user=user_details.user, key__in=[CareerItemKey.LANGUAGE.value, CareerItemKey.FRAMEWORK.value, CareerItemKey.DATA_BASE.value]).order_by('key').values_list('value', flat=True)
        joining_date_time = datetime.combine(user_details.joining_date, time())
        affiliation_period = Utils.get_affiliation_period(joining_date_time, date_now)
        results.append({
          'userId': user_details.user.id,
          'fullName': user_details.last_name + " " + user_details.first_name,
          'joiningDate': user_details.joining_date.strftime(f'%Y/%m/%d'),
          'AffiliationPeriod': affiliation_period[1],
          'careerItem': list(set(career_item_obj))
        })

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.renderList(results, total_count, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = 'ユーザ一覧情報取得処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.renderList([], 0, response.status_code, error_message)
    
    return response


"""[経歴情報Dictionary取得]
    ユーザIDで経歴情報をDictionaryで取得
Returns:
    [Response]: [リクエストのレスポンス]
"""
class CareerDicRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    user_id = self.request.GET.get('userId')

    try:
      career_obj = Career.objects.filter(user__company=request.user.company, user=user_id)
      career_item_obj = CareerItem.objects.filter(career__user = user_id)

      result = {
        'careerDic': ViewUtil.getCareerDic(career_obj, career_item_obj)
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '経歴情報取得処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)
    
    return response


"""
  経歴情報一覧取得

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class CareerListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    param_user_id = self.request.GET.get('userId')
    limit = self.request.GET.get('limit')
    ofset = self.request.GET.get('offset')

    try:
      where_params = {
        'user__company': request.user.company,
      }

      if param_user_id:
        where_params['user_id'] = param_user_id
      else:
        where_params['user_id'] = request.user.id

      total_count = Career.objects.filter(**where_params).count()
      career_obj = Career.objects.filter(**where_params).order_by("start_date")[int(ofset):(int(ofset) + int(limit))]

      results = []
      for career in career_obj:
        result = {
          'id': career.id,
          'userId': career.user.id,
          'projectName': career.project_name,
          'overview': career.overview,
          'startDate': career.start_date.strftime('%Y/%m/%d'),
          'endDate': career.end_date.strftime('%Y/%m/%d'),
        }
        results.append(result)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.renderList(results, total_count, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '経歴情報取得処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)
    
    return response


"""
  経歴情報取得

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class CareerRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    career_id = self.request.GET.get('careerId')

    if not career_id:
      raise exceptions.APIException('Invalid Parameter:careerId')

    try:
      career_obj = Career.objects.get(id=career_id, user__company_id=request.user.company.id, user_id=request.user.id)

      dic = {}
      for key_name in CareerItemKey.KEY_LIST.value:
        dic[key_name] = CareerItem.objects.filter(key=key_name, career_id=career_id).values_list('value', flat=True)

      result = {
        'career': {
          'id': career_obj.id,
          'userId': career_obj.user.id,
          'projectName': career_obj.project_name,
          'overview': career_obj.overview,
          'startDate': career_obj.start_date,
          'endDate': career_obj.end_date,
        },
        'careerItem': {
          CareerItemKey.MODEL.value: dic[CareerItemKey.MODEL.value],
          CareerItemKey.OS.value: dic[CareerItemKey.OS.value],
          CareerItemKey.DATA_BASE.value: dic[CareerItemKey.DATA_BASE.value],
          CareerItemKey.LANGUAGE.value: dic[CareerItemKey.LANGUAGE.value],
          CareerItemKey.FRAMEWORK.value: dic[CareerItemKey.FRAMEWORK.value],
          CareerItemKey.TOOL.value: dic[CareerItemKey.TOOL.value],
          CareerItemKey.INCHARGE.value: dic[CareerItemKey.INCHARGE.value],
          CareerItemKey.ROLE.value: dic[CareerItemKey.ROLE.value],
          CareerItemKey.OTHER.value: dic[CareerItemKey.OTHER.value][0] if any(dic[CareerItemKey.OTHER.value]) else None,
        },
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '経歴情報取得処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  経歴情報保存

Raises:
  exceptions.ValidationError: _description_
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class SaveCareerAPIView(CreateAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def create(self, request):
    user_id = request.data['user']
    career_id = request.data['careerId']

    try:
      with transaction.atomic():
        date_now = Utils.get_now_to_string()
        career_req = {
          'user_id': user_id if user_id else request.user.id,
          'project_name': request.data['projectName'],
          'overview': request.data['overview'] if request.data['overview'] else None,
          'start_date': request.data['startDate'].replace('/', '-') if request.data['startDate'] and request.data['startDate'] != '' else None,
          'end_date': request.data['endDate'].replace('/', '-') if request.data['endDate'] and request.data['endDate'] != '' else None,
        }

        if career_id:
          career_obj = Career.objects.select_for_update().get(id = career_id)
          update_serializer = CareerSerializer(career_obj, data=career_req)
          if not update_serializer.is_valid():
            raise exceptions.APIException(update_serializer.errors)

          update_serializer.update(career_obj, career_req, date_now, request.user)
        else:
          serializer = CareerSerializer(data=career_req)
          if not serializer.is_valid():
            raise exceptions.APIException(serializer.errors)

          new_career = serializer.save(career_req, date_now, request.user)

        for item_key in CareerItemKey.KEY_LIST.value:
          career_item = [career_item for career_item in request.data[item_key] if career_item != '']
          add_values = career_item

          if career_id:
            # DBに存在している値
            career_item_obj = CareerItem.objects.select_for_update().filter(career_id=career_id, key=item_key).values_list('value', flat=True)
            # リクエストデータの値 - DBに存在している値 = 新規追加データ
            add_values = list(set(career_item) - set(list(career_item_obj)))
            # DBに存在している値 - リクエストデータの値 = 削除対象データ
            del_values = list(set(list(career_item_obj)) - set(career_item))

            # 削除
            for val in del_values:
              del_data = CareerItem.objects.filter(career_id=career_id, key=item_key, value=val)
              del_data.delete()
          else:
            add_values = career_item

          if len(add_values) <= 0:
            continue

          for item_value in add_values:
            req = {
              'key': item_key,
              'value': item_value,
              'user': career_req['user_id'],
            }
            career_item_serializer = CareerItemSerializer(data=req)
            if not career_item_serializer.is_valid():
              raise exceptions.APIException(career_item_serializer.errors)

            career_item_serializer.save(req, career_id if career_id else new_career.id, date_now, request.user)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '経歴情報登録処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  経歴情報削除

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class CareerDestroyAPIView(DestroyAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def destroy(self, request):
    career_id = self.request.GET.get('careerId')

    try:
      career_obj = Career.objects.get(id = career_id)
      career_obj.delete()

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '経歴情報削除処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  経歴情報マスタ項目取得

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class CareerItemMasterListAPIView(ListAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    key = self.request.GET.get('key')

    try:
      where_params = {
        'company_id': request.user.company.id,
      }

      if key:
        where_params['key'] = key

      career_master_obj = CareerMaster.objects.filter(**where_params).order_by('id', 'key')
      master_result = []
      model_list = []
      os_list = []
      language_list = []
      framework_list = []
      database_list = []
      tool_list = []

      for item in career_master_obj:
        result = {
          'id': item.id,
          'key': item.key,
          'value': item.value,
        }

        if item.key == 'model':
          model_list.append(result)
        elif item.key == 'os':
          os_list.append(result)
        elif item.key == 'language':
          language_list.append(result)
        elif item.key == 'framework':
          framework_list.append(result)
        elif item.key == 'database':
          database_list.append(result)
        elif item.key == 'tool':
          tool_list.append(result)

      master_result = {
        'modelList': model_list,
        'osList': os_list,
        'languageList': language_list,
        'frameworkList': framework_list,
        'databaseList': database_list,
        'toolList': tool_list,
      }

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render(master_result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = 'マスタ項目情報取得処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  経歴情報マスタ項目登録

Raises:
  exceptions.APIException: _description_

Returns:
  _type_: _description_
"""
class SaveMasterCreateAPIView(CreateAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def create(self, request):
    req = {
      'id': request.data['id'],
      'key': request.data['key'],
      'value': request.data['value'],
      'company_id': request.user.company.id,
    }

    try:
      with transaction.atomic():
        date_now = Utils.get_now_to_string()
        if request.data['id'] is None:
          # 新規
          serializer = CareerMasterSerializer(data=req)
          if not serializer.is_valid():
            raise exceptions.APIException(serializer.errors)
          serializer.save(req, date_now, request.user)
        else:
          # 更新
          career_master_obj = CareerMaster.objects.select_for_update().get(company=request.user.company.id, id=request.data['id'])
          serializer = CareerMasterSerializer(career_master_obj, data=req)
          if not serializer.is_valid():
            raise exceptions.APIException(serializer.errors)
          serializer.update(career_master_obj, req, date_now, request.user)

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = 'マスタ項目情報登録処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail

      if e.args[0] == 1062:
        error_message = '登録済みのマスタ項目情報です。'
      elif e.args[0] == 1406:
        error_message = '登録可能な文字数を超過しています。'

      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  経歴情報マスタ項目削除

Raises:

Returns:
  _type_: _description_
"""
class CareerMasterDestroyAPIView(DestroyAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]


  def destroy(self, request):
    master_id = self.request.GET.get('id')

    try:
      master_master_obj = CareerMaster.objects.get(id=master_id, company=request.user.company.id)
      master_master_obj.delete()

      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = 'マスタ項目情報削除処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""
  スキルシート出力

Raises:

Returns:
  _type_: _description_
"""
class CareerOutputAPIView(APIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    param_user_id = self.request.GET.get('userId')

    try:
      if request.user.is_admin is False and str(request.user.id) != param_user_id:
        raise exceptions.APIException()

      where_params = {
        'user__company': request.user.company,
        'user_id': param_user_id
      }
      career_obj = Career.objects.filter(**where_params).order_by("start_date")
      user_details_obj = UserDetails.objects.get(**where_params)

      career_item_dic = {}
      for career in career_obj:
        dic = {}
        for key_name in CareerItemKey.KEY_LIST.value:
          values = list(CareerItem.objects.filter(key=key_name, career_id=career.id).values_list('value', flat=True))
          # カンマ区切りで結合
          dic[key_name] = ','.join(values)
        career_item_dic[str(career.id)] = dic

      # 前方一致で前回作成したファイルを削除
      for file in glob.glob(os.getcwd() + '/' + settings.CAREER_SHEET_OUTPUT_DIR_PATH + settings.CAREER_SHEET_PREFIX + user_details_obj.last_name + user_details_obj.first_name + '*'):
        os.remove(file)

      # os.makedirs(temp_dir_path, exist_ok=True)
      file_name = ExcelReportWithOpenpyxl.write(career_obj, career_item_dic, user_details_obj, settings.CAREER_SHEET_OUTPUT_DIR_PATH)
      quoted_filename = urllib.parse.quote(file_name)
      file = open('{0}/{1}'.format(settings.CAREER_SHEET_OUTPUT_DIR_PATH, file_name), 'rb')

      response = FileResponse(file)
      response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      response['Content-Disposition'] = 'attachment; filename="{}"'.format(quoted_filename)
      response['Access-Control-Expose-Headers'] = 'content-disposition'
      response.status_code = status.HTTP_200_OK
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      error_message = '経歴情報取得処理中にエラーが発生しました。'
      if type(e) == exceptions.ValidationError:
        error_message = e.detail
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, error_message)

    return response


"""[ViewUtility]
    viewクラス汎用処理
"""
class ViewUtil():
  def getCareerItemPointDic(key_name, dic, career_obj, career_item_obj, days):
    item = filter(lambda item: item.career.id == career_obj.id and item.key == key_name, career_item_obj)
    for i in item:
      db_dic_key = i.value
      dayInt = days.days
      point = 0
      if dayInt < 180:
        # 半年未満
        point = 1
      elif dayInt < 365:
        # 1年未満
        point = 2
      elif dayInt < 365 * 3:
        # 3年未満
        point = 3
      elif dayInt < 365 * 5:
        # 5年未満
        point = 4
      elif dayInt < 365 * 10:
        # 10年未満
        point = 5
      elif dayInt < 365 * 20:
        # 20年未満
        point = 6
      else:
        point = 7

      if db_dic_key in dic.keys():
        dic[db_dic_key] = dic[db_dic_key] + point
      else:
        dic[db_dic_key] = point
    return dic

  def getCareerItemDic(key_name, dic, career_obj, career_item_obj, days):
    item = filter(lambda item: item.career.id == career_obj.id and item.key == key_name, career_item_obj)
    for i in item:
      db_dic_key = i.value
      if db_dic_key in dic.keys():
        dic[db_dic_key] = dic[db_dic_key] + days
      else:
        dic[db_dic_key] = days
    return dic


  def getCareerDic(career_obj, career_item_obj):
    db_dic = {}
    lang_dic = {}
    framework_dic = {}
    tool_dic = {}
    for career in career_obj:
      if(career.start_date is None or career.end_date is None):
        continue
      period_Month = Utils.get_affiliation_period(Utils.sub_day(career.start_date, 1), career.end_date)
      db_dic = ViewUtil.getCareerItemDic(CareerItemKey.DATA_BASE.value, db_dic, career, career_item_obj, int(period_Month[1]))
      lang_dic = ViewUtil.getCareerItemDic(CareerItemKey.LANGUAGE.value, lang_dic, career, career_item_obj, int(period_Month[1]))
      framework_dic = ViewUtil.getCareerItemDic(CareerItemKey.FRAMEWORK.value, framework_dic, career, career_item_obj, int(period_Month[1]))
      tool_dic = ViewUtil.getCareerItemDic(CareerItemKey.TOOL.value, tool_dic, career, career_item_obj, int(period_Month[1]))

    for key, value in db_dic.items():
      db_dic[key] = value
    for key, value in lang_dic.items():
      lang_dic[key] = value
    for key, value in framework_dic.items():
      framework_dic[key] = value
    for key, value in tool_dic.items():
      tool_dic[key] = value


    # 期間（日）で降順ソート
    db_list = sorted(db_dic.items(), key = lambda item: item[1], reverse = True)
    db_dic.clear()
    db_dic.update(db_list)

    lang_list = sorted(lang_dic.items(), key = lambda item: item[1], reverse = True)
    lang_dic.clear()
    lang_dic.update(lang_list)

    framework_list = sorted(framework_dic.items(), key = lambda item: item[1], reverse = True)
    framework_dic.clear()
    framework_dic.update(framework_list)

    tool_list = sorted(tool_dic.items(), key = lambda item: item[1], reverse = True)
    tool_dic.clear()
    tool_dic.update(tool_list)

    return {
      'careerDb': db_dic,
      'careerLang': lang_dic,
      'careerFramework': framework_dic,
      'careerTool': tool_dic,
    }
