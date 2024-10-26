import type { Response } from 'express';
import jsonwebtoken, { JwtPayload } from 'jsonwebtoken';
const authConfig = require('../auth/authConfig');

interface jsonwebtoken {
  companyId: string,
  userId: string,
  auth: string
}

/**
 * 基底サービス
 */
export default class BaseService {
  constructor() {
  }

  execute() {

  }

  /**
   * ログインユーザの会社ID取得
   * @param res 
   * @returns 
   */
  getLoginCompanyId(res: Response) {
    let jwtPayload: null | JwtPayload | string = jsonwebtoken.decode(res.locals.token, authConfig.jwt.secret);
    if(jwtPayload) {
      return jwtPayload.companyId;
    }
    return null;
  }

  /**
   * ログインユーザID取得
   * @param res 
   * @returns 
   */
  getLoginUserId(res: Response) {
    const jwtPayload: null | JwtPayload | string = jsonwebtoken.decode(res.locals.token, authConfig.jwt.secret);
    if(jwtPayload) {
      return jwtPayload.userId;
    }
    return null;
  }

    /**
   * 権限取得
   * @param res 
   * @returns 
   */
    getAuth(res: Response) {
      const jwtPayload: null | JwtPayload | string = jsonwebtoken.decode(res.locals.token, authConfig.jwt.secret);
      if(jwtPayload) {
        return jwtPayload.auth;
      }
      return null;
    }

  /**
   * 管理者かどうか取得
   * @param res 
   * @returns 
   */
  getIsAdmin(res: Response) {
    const jwtPayload: null | JwtPayload | string = jsonwebtoken.decode(res.locals.token, authConfig.jwt.secret);
    if(jwtPayload && jwtPayload.auth == '0') {
      return true;
    }
    return false;
  }

  /**
   * レスポンス設定
   * @param res 
   * @param results 
   * @param total 
   */
  setSuccessResponse(res: Response, results: any, total: any) {
    res.status(200);
    res.json({
      total: total ? total : 1,
      resultCode: res.statusCode,
      result: results ? results : [],
    });
  }
}