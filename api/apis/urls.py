from django.urls import path
from authentications.views import LoginAPIView, LogoutAPIView, LoginUserInfoRetrieveAPIView
from application.views import NotificationRetrieveAPIView, ApplicationMonthListAPIView, ApplicationListAPIView, ApplicationRetrieveAPIView, ApplicationAPIView, ApplicationDestroyAPIView, ApplicationCancelAPIView
from approval.views import ApproveListAPIView, ApproveAPIView
from systemsettings.views import SystemConfigsRetrieveAPIView, SystemConfigsDestroyAPIView, ApprovalGroupListAPIView, ApprovalGroupAPIView, ApplicationTypeListAPIView
from users.views import UserListAPIView, UserDetailsRetrieveAPIView, UserNameListAPIView, UpdateUserAPIView, GetGrantDaysRetrieveAPIView, UpdateGrantDaysAPIView, ChangePasswordAPIView
from career.views import CareerListAPIView, CareerRetrieveAPIView, CareerDicRetrieveAPIView, SaveCareerAPIView, CareerDestroyAPIView, CareerItemMasterListAPIView, SaveMasterCreateAPIView, CareerMasterDestroyAPIView, CareerUserListAPIView, CareerOutputAPIView

urlpatterns = [
  # ログイン
  path(r'login', LoginAPIView.as_view()),
  # ログアウト
  path(r'logout', LogoutAPIView.as_view()),
  # ログインユーザ情報取得
  path(r'loginUserInfo', LoginUserInfoRetrieveAPIView.as_view()),
  # 通知情報取得
  path(r'notification', NotificationRetrieveAPIView.as_view()),
  # 月間の申請一覧取得
  path(r'application/month', ApplicationMonthListAPIView.as_view()),
  # 申請一覧取得
  path(r'application/list', ApplicationListAPIView.as_view()),
  # 申請取得
  path(r'application', ApplicationRetrieveAPIView.as_view()),
  # 申請
  path(r'application/save', ApplicationAPIView.as_view()),
  # 申請情報削除
  path(r'application/delete', ApplicationDestroyAPIView.as_view()),
  # 申請情報取消（管理者権限あり）
  path(r'application/cancel', ApplicationCancelAPIView.as_view()),
  # 承認一覧取得
  path(r'approval/task/list', ApproveListAPIView.as_view()),
  # 承認
  path(r'approval/approve', ApproveAPIView.as_view()),
  # システム設定情報取得
  path(r'systemConfigs', SystemConfigsRetrieveAPIView.as_view()),
  # システム設定情報削除（管理者権限あり）
  path(r'systemConfig/delete', SystemConfigsDestroyAPIView.as_view()),
  # 承認グループ一覧取得
  path(r'systemConfig/approvalGroup/list', ApprovalGroupListAPIView.as_view()),
  # 承認グループ登録/更新（管理者権限あり）
  path(r'systemConfig/approvalGroup/save', ApprovalGroupAPIView.as_view()),
  # 申請タイプ設定取得
  path(r'systemConfig/applicationType/list', ApplicationTypeListAPIView.as_view()),
  # ユーザ一覧取得
  path(r'user/list', UserListAPIView.as_view()),
  # ユーザ情報取得
  path(r'userDetails', UserDetailsRetrieveAPIView.as_view()),
  # ユーザ名一覧取得
  path(r'userName/list', UserNameListAPIView.as_view()),
  # ユーザ情報更新（管理者権限あり）
  path(r'user/save', UpdateUserAPIView.as_view()),
  # 付与日数取得（管理者権限あり）
  path(r'user/grantDays', GetGrantDaysRetrieveAPIView.as_view()),
  # 付与日数更新（管理者権限あり）
  path(r'user/updateGrantDays', UpdateGrantDaysAPIView.as_view()),
  # パスワード変更
  path(r'changePassword', ChangePasswordAPIView.as_view()),
  # 経歴情報一覧取得
  path(r'career/list', CareerListAPIView.as_view()),
  # 経歴情報取得
  path(r'career', CareerRetrieveAPIView.as_view()),
  # 経歴情報保存
  path(r'career/save', SaveCareerAPIView.as_view()),
  # 経歴情報保存
  path(r'career/delete', CareerDestroyAPIView.as_view()),
  # 経歴情報マスタ項目取得
  path(r'career/itemMaster', CareerItemMasterListAPIView.as_view()),
  # 経歴情報マスタ項目登録（管理者権限あり）
  path(r'career/itemMaster/save', SaveMasterCreateAPIView.as_view()),
  # 経歴情報マスタ項目削除（管理者権限あり）
  path(r'career/itemMaster/delete', CareerMasterDestroyAPIView.as_view()),
  # 保有スキル一覧取得
  path(r'career/user/list', CareerUserListAPIView.as_view()),
  # 経歴情報Dictionary取得
  path(r'career/dictionary', CareerDicRetrieveAPIView.as_view()),
  # スキルシート出力
  path(r'career/outputSkillSheet', CareerOutputAPIView.as_view()),

]