import time
import jwt
import traceback
from django.conf import settings
from rest_framework import status
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from config.renderers import JSONRenderer
from config.responseRenderers import ResponseRenderers
from users.models import User, UserDetails
from config.utils import Utils

class NormalAuthentication(BaseAuthentication):
  def authenticate(self, request):
    user_id = request.data.get("user_id")
    password = request.data.get("password")
    user_obj = User.objects.filter(user_id=user_id).first()
    print(user_obj.password)
    print(Utils.getPasswordHash(password, user_id))
    if not user_obj or user_obj.password != Utils.getPasswordHash(password, user_id):
      raise exceptions.AuthenticationFailed('認証失敗')

    user_details_obj = UserDetails.objects.filter(user=user_obj.id).first()
    token = generate_jwt(user_obj, user_details_obj)

    user_info = {
      'id': user_obj.id,
      'userid': user_obj.user_id,
      'company_id': user_obj.company.id,
      'auth': user_details_obj.auth,
      'first_name': user_details_obj.first_name,
      'last_name': user_details_obj.last_name,
    }

    return ('jwt ' + token, user_info)

  def authenticate_header(self, request):
    pass

# ドキュメント: https://pyjwt.readthedocs.io/en/latest/usage.html?highlight=exp
def generate_jwt(user, user_details):

  # 有効期間を1時間に設定
  return jwt.encode(
    {
      "user_id": user.id,
      "company_id": user.company.id,
      "authority": user_details.auth,
      "exp": int(time.time()) + 60 * 60,
    },
    settings.JWT_SECRET_KEY,
    settings.JWT_ALGORITHMS
  )

class JWTAuthentication(BaseAuthentication):
  keyword = 'JWT'
  model = None

  def authenticate(self, request):
    auth = get_authorization_header(request).split()

    # 認証情報取得失敗 or プレフィックス不一致
    if not auth or auth[0].lower() != self.keyword.lower().encode():
      raise exceptions.AuthenticationFailed('認証情報取得失敗')

    if len(auth) == 1 or len(auth) > 2:
      raise exceptions.AuthenticationFailed('認証情報不正')

    try:
      jwt_token = auth[1]
      # decode時に有効期間が自動検証されるので自前検証不要
      jwt_info = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHMS)
      user_id = jwt_info.get("user_id")
      try:
        user = User.objects.get(id=user_id)
        user_details = UserDetails.objects.filter(user=user.id).first()
        user.is_authenticated = True

        # 権限チェック
        user.is_admin = True if user_details.auth == 0 else False

        return (user, jwt_token)
      except:
        raise exceptions.AuthenticationFailed('認証失敗')

    except jwt.ExpiredSignatureError:
      raise exceptions.AuthenticationFailed('有効期間超過')

  def authenticate_header(self, request):
    pass

class LoginAPIView(APIView):
  authentication_classes = [NormalAuthentication]

  def post(self, request, *args, **kwargs):
    # user_id = request.data.get("user_id")
    try:
      response = Response()
      response.status_code = status.HTTP_200_OK
      result = {
          'user': request.auth,
          'jwt': request.user.split()[1],
      }
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.AuthenticationFailed('Login Failure')
      response = Response()
      response.status_code = status.HTTP_401_UNAUTHORIZED
      response.data = ResponseRenderers.render({}, response.status_code, 'ログイン処理中にエラーが発生しました。')

    return response

"""_summary_

Raises:
    exceptions.AuthenticationFailed: _description_
    exceptions.AuthenticationFailed: _description_
    exceptions.AuthenticationFailed: _description_

Returns:
    _type_: _description_
"""
class LogoutAPIView(APIView):
  # authentication_classes = [NormalAuthentication]
  # authentication_classes = [JWTAuthentication]
  # permission_classes = [IsAuthenticated]

  def post(self, request, *args, **kwargs):
    try:
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.AuthenticationFailed('Logout Failure')
      response = Response()
      response.status_code = status.HTTP_401_UNAUTHORIZED
      response.data = ResponseRenderers.render({}, response.status_code, 'ログアウト処理中にエラーが発生しました。')

    return response


class LoginUserInfoRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      user_obj = User.objects.filter(id=request.user.id).first()
      user_details = UserDetails.objects.filter(user=user_obj.id).first()

      if(not user_obj or not user_details):
        raise exceptions.AuthenticationFailed('ユーザ情報取得失敗')

      response = Response()
      response.status_code = status.HTTP_200_OK
      result = {
        'id': user_obj.id,
        'userId': user_obj.user_id,
        'companyId': user_obj.company.id,
        'firstName': user_details.first_name,
        'lastName': user_details.last_name,
        'auth': user_details.auth,
        'referenceDate': user_details.reference_date,
        'workingDays': user_details.working_days,
        'totalDeleteDays': user_details.total_delete_days,
        'totalAddDays': user_details.total_add_days,
        'totalRemainingDays': user_details.total_remaining_days,
        'autoCalcRemainingDays': user_details.auto_calc_remaining_days,
        'totalCarryoverDays': user_details.total_carryover_days,
      }
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      # raise exceptions.AuthenticationFailed('ユーザ情報取得失敗')
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ログインユーザ情報取得中にエラーが発生しました。')

    return response
