import express from 'express';
import type { Request, Response, NextFunction } from 'express';
import LoginService from "./auth/loginService";
import UserService from "./services/userService";
import ApplicationService from "./services/applicationService";
import ApprovalService from "./services/approvalService";
import SystemSettingService from './services/systemSettingService';

const cookieParser = require('cookie-parser');
const app = express();
const authenticate = require('./auth/authenticate');
const port = process.env.PORT || 3001;

const bodyParser = require('body-parser')
const loginService = new LoginService();
const userService = new UserService();
const applicationService = new ApplicationService();
const approvalService = new ApprovalService();
const systemSettingService = new SystemSettingService();

app.use(bodyParser.urlencoded({extended: true}));
app.use(bodyParser.json());
app.use(cookieParser());

// 全てのリクエストに対して前処理
app.use( '/*', (req: Request, res: any, next: any) => {
  // res.header('Access-Control-Allow-Origin', 'http://localhost:3000');
  res.header('Access-Control-Allow-Origin', 'http://192.168.0.253:3000');
  res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE');
  res.header('Access-Control-Allow-Credentials', 'true');
  res.header(
    'Access-Control-Allow-Headers',
    'X-XSRF-TOKEN, Content-Type, Authorization, access_token, access-control-allow-credentials, access-control-allow-headers, access-control-allow-methods, access-control-allow-origin'
  )

  console.log(req.originalUrl)
  res.locals.queryParams = req.query;
  res.locals.reqBody = req.body;
  res.locals.token = req.cookies.jwt_token;

  next();
});

app.get('/grantRule', (req: any, res: any, next: any) => {
  res.status(200);
  res.json({
    total: 1,
    resultCode: res.statusCode,
    result: require('./grantRule.json'),
  });
})

// ログイン
app.post("/login", (req: any, res: any, next: any) => {
  loginService.login(res, next);
});

// ログアウト
app.post("/logout", (req: any, res: any, next: any) => {
  res.clearCookie("jwt_token");
  res.status(200);
  res.json({
    total: 1,
    resultCode: res.statusCode,
    result: {},
  });
});

// ログインユーザ情報取得
app.get("/loginUserInfo", authenticate, (req: any, res: any, next: any) => {
  userService.getLoginUserInfo(req, res, next);
});

// ユーザ取得
app.get("/userDetails", authenticate, (req: any, res: any, next: any) => {
  userService.getUserDetails(req, res, next);
});

// ユーザ情報保存
app.post(`/user/save`, authenticate, (req: any, res: any, next: any) => {
  userService.saveUser(req, res, next);
});

// 付与日数更新
app.post(`/user/updateGrantDays`, authenticate, (req: any, res: any, next: any) => {
  userService.updateGrantDays(req, res, next);
});

// ユーザ一覧取得
app.get("/user/list", authenticate, (req: any, res: any, next: any) => {
  userService.getUserList(req, res, next);
});

// ユーザ名一覧取得
app.get("/userName/list", authenticate, (req: any, res: any, next: any) => {
  userService.getUserNameList(req, res, next);
});

// 申請取得
app.get("/application", authenticate, (req: any, res: any, next: any) => {
  applicationService.getApplication(req, res, next);
});

// 申請一覧取得
app.get("/application/list", authenticate, (req: any, res: any, next: any) => {
  applicationService.getApplicationList(req, res, next);
});

// 月間の申請一覧取得
app.get("/application/month", authenticate, (req: any, res: any, next: any) => {
  applicationService.getApplicationListByMonth(req, res, next);
});

// 通知情報取得
app.get("/notification", authenticate, (req: any, res: any, next: any) => {
  userService.getNotification(req, res, next);
});

// 申請
app.post(`/application/save`, authenticate, (req: any, res: any, next: any) => {
  applicationService.saveApplication(req, res, next);
});

// 申請削除
app.delete(`/application/delete`, authenticate, (req: any, res: any, next: any) => {
  applicationService.deleteApplication(req, res, next);
});

// 申請取消
app.post(`/application/cancel`, authenticate, (req: any, res: any, next: any) => {
  applicationService.cancelApplication(req, res, next);
});

// 承認タスク一覧取得
app.get("/approval/task/list", authenticate, (req: any, res: any, next: any) => {
  approvalService.getApprovalTaskList(req, res, next);
});

// 承認
app.post(`/approval/approve`, authenticate, (req: any, res: any, next: any) => {
  approvalService.approve(req, res, next);
});

// システム設定情報取得
app.get(`/systemConfigs`, authenticate, (req: any, res: any, next: any) => {
  systemSettingService.getSystemConfigs(req, res, next);
});

// システム設定情報削除
app.delete(`/systemConfig/delete`, authenticate, (req: any, res: any, next: any) => {
  systemSettingService.deleteSystemConfig(req, res, next);
});

// 承認グループ一覧取得
app.get(`/systemConfig/approvalGroup`, authenticate, (req: any, res: any, next: any) => {
  systemSettingService.getApprovalGroupList(req, res, next);
});

// 承認グループ保存
app.post(`/systemConfig/save/approvalGroup`, authenticate, (req: any, res: any, next: any) => {
  systemSettingService.saveApprovalGroup(req, res, next);
});

// エラー処理
app.use((err: any, req: any, res: any, next: any) => {
  if(err) {
    let date = (new Date).toLocaleDateString('ja-JP');
    let time = (new Date).toLocaleTimeString('ja-JP');
    let logHeder = `ERROR ${date} ${time}`;
    console.log("---------- ERROR ----------");
    console.log(err.message);
    // console.log(err);
    // console.log(error.parent);
    // console.log(`${logHeder} ${error.parent.sqlMessage}`);
  }

  if(err.name === 'ValidationError') {
    res.status(400)
    res.json({
      resultCode: res.status,
      result: {
        message: err.message,
      },
    });
  } else if (err.name === 'AuthError') {
    res.status(401)
    res.json({
      resultCode: res.status,
      result: {
        message: '認証に失敗しました。',
      },
    });
  } else if (err.name === 'NotFoundError') {
    res.status(404)
    res.json({
      resultCode: res.status,
      result: {
        message: err.message,
      },
    });
  } else {
    res.status(500)
    res.json({
      resultCode: res.status,
      result: {
        message: 'サーバーエラーが発生しました。管理者にお問合せください。',
      },
    });
  }
})

app.listen(port, () => {
  console.log(`listening on *:${port}`);
})
