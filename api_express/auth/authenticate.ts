import type { Request, Response, NextFunction } from 'express';
// const jsonwebtoken = require('jsonwebtoken');
import jsonwebtoken from 'jsonwebtoken';
import { AuthError } from '../errors';
const authconfig = require('./authConfig');

declare module "express" { 
  export interface Request {
    jwtPayload: string| jsonwebtoken.JwtPayload
  }
}

module.exports = function authenticate(req: Request, res: Response, next: NextFunction) {
  try {
    const token: string = res.locals.token;
    const decoded: string | jsonwebtoken.JwtPayload = jsonwebtoken.verify(token, authconfig.jwt.secret);
    req.jwtPayload = decoded;
    next();
  } catch (e) {
    let errorMsg: string = '認証エラー';
    if (e instanceof jsonwebtoken.TokenExpiredError) {
      errorMsg = 'トークンの有効期限が切れています。';
    } else if (e instanceof jsonwebtoken.JsonWebTokenError) {
      errorMsg = 'トークンが不正です。';
    }

    throw new AuthError(errorMsg);
  }
};
