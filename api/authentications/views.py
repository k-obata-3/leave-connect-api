import time
import jwt
import traceback
from django.conf import settings
from rest_framework import status
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView

from config.utils import Utils
from config.responseRenderers import ResponseRenderers

from users.models import User, UserDetails


"""
  パスワード認証

Raises:
  exceptions.AuthenticationFailed: _description_

Returns:
  _type_: _description_
"""
class NormalAuthentication(BaseAuthentication):
  def authenticate(self, request):
    user_id = request.data.get("user_id")
    password = request.data.get("password")

    try:
      user_obj = User.objects.filter(user_id=user_id, status=settings.USER_EFFECTIVE_STATUS).first()
      if user_obj is None:
        raise exceptions.NotAuthenticated('認証失敗')

      print(Utils.get_password_hash(password, user_obj))
      if not user_obj or user_obj.password != Utils.get_password_hash(password, user_obj):
        raise exceptions.NotAuthenticated('認証失敗')

      user_details_obj = UserDetails.objects.get(user=user_obj.id)
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
    except Exception as e:
      raise e

  def authenticate_header(self, request):
    if request.user.is_anonymous:
      # 'WWW-Authenticate'を返却することで、401となる
      return 'WWW-Authenticate'

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


"""
  JWT認証

Raises:
  exceptions.AuthenticationFailed: _description_

Returns:
  _type_: _description_
"""
class JWTAuthentication(BaseAuthentication):
  keyword = 'JWT'
  model = None

  def authenticate(self, request):
    auth = get_authorization_header(request).split()

    # 認証情報取得失敗 or プレフィックス不一致
    if not auth or auth[0].lower() != self.keyword.lower().encode():
      raise exceptions.NotAuthenticated('認証情報取得失敗')

    if len(auth) == 1 or len(auth) > 2:
      raise exceptions.NotAuthenticated('認証情報不正')

    try:
      jwt_token = auth[1]
      # decode時に有効期間が自動検証されるので自前検証不要
      jwt_info = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHMS)
      user_id = jwt_info.get("user_id")
      try:
        user = User.objects.get(id=user_id, status=settings.USER_EFFECTIVE_STATUS)
        user_details = UserDetails.objects.get(user=user.id)
        user.is_authenticated = True

        # 権限チェック
        user.is_admin = True if user_details.auth == 0 else False

        return (user, jwt_token)
      except:
        raise exceptions.NotAuthenticated('認証失敗')

    except jwt.ExpiredSignatureError:
      raise exceptions.NotAuthenticated('有効期間超過')

  def authenticate_header(self, request):
    if request.user.is_anonymous:
      # 'WWW-Authenticate'を返却することで、401となる
      return 'WWW-Authenticate'



class IsAuthenticated(BasePermission):
  def has_permission(self, request, view):
    return bool(request.user and request.user.is_admin)

"""
  ログイン

Raises:
  exceptions.AuthenticationFailed: _description_

Returns:
  _type_: _description_
"""
class LoginAPIView(APIView):
  authentication_classes = [NormalAuthentication]

  def post(self, request, *args, **kwargs):
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
      response = Response()
      response.status_code = status.HTTP_401_UNAUTHORIZED
      response.data = ResponseRenderers.render({}, response.status_code, 'ログイン処理中にエラーが発生しました。')

    return response


"""
  ログアウト

Raises:
  exceptions.AuthenticationFailed: _description_

Returns:
  _type_: _description_
"""
class LogoutAPIView(APIView):

  def post(self, request, *args, **kwargs):
    try:
      response = Response()
      response.status_code = status.HTTP_200_OK
      response.data = ResponseRenderers.render({}, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_401_UNAUTHORIZED
      response.data = ResponseRenderers.render({}, response.status_code, 'ログアウト処理中にエラーが発生しました。')

    return response


"""
  ログインユーザ情報取得

Raises:
  exceptions.AuthenticationFailed: _description_

Returns:
  _type_: _description_
"""
class LoginUserInfoRetrieveAPIView(RetrieveAPIView):
  authentication_classes = [JWTAuthentication]
  permission_classes = []

  def get(self, request):
    try:
      user_obj = User.objects.get(id=request.user.id, status=settings.USER_EFFECTIVE_STATUS)
      user_details = UserDetails.objects.get(user=user_obj.id)

      if(not user_obj or not user_details):
        raise exceptions.NotAuthenticated('ユーザ情報取得失敗')

      response = Response()
      response.status_code = status.HTTP_200_OK
      result = {
        'id': user_obj.id,
        'userId': user_obj.user_id,
        'companyId': user_obj.company.id,
        'firstName': user_details.first_name,
        'lastName': user_details.last_name,
        'firstNameKana': user_details.first_name_kana,
        'lastNameKana': user_details.last_name_kana,
        'dateOfBirth': user_details.date_of_birth,
        'auth': user_details.auth,
        'joiningDate': user_details.joining_date,
        'referenceDate': user_details.reference_date,
        'workingDays': user_details.working_days,
        'totalDeleteDays': user_details.total_delete_days,
        'totalAddDays': user_details.total_add_days,
        # 残日数 = (繰越日数 + 付与日数) - 取得日数
        'totalRemainingDays': (user_details.total_carryover_days + user_details.total_add_days) - user_details.total_delete_days,
        'totalCarryoverDays': user_details.total_carryover_days,
      }
      response.data = ResponseRenderers.render(result, response.status_code, None)
    except Exception as e:
      print('【ERROR】:' + traceback.format_exc())
      response = Response()
      response.status_code = status.HTTP_400_BAD_REQUEST
      response.data = ResponseRenderers.render({}, response.status_code, 'ログインユーザ情報取得中にエラーが発生しました。')

    return response
