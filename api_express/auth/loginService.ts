import type { Response, NextFunction } from 'express';
import crypto, { BinaryLike } from 'crypto';
const models = require("../models");
// const jsonwebtoken = require('jsonwebtoken');
import jsonwebtoken from 'jsonwebtoken';
import { AuthError } from '../errors';
const authConfig = require('./authConfig');

export default class LoginService {
  constructor() {
  }

  // ログイン
  login(res: Response, next: NextFunction) {
    models.Users.findOne({
      include: [
        {
          model: models.UserDetails,
          as: 'UserDetails',
        }
      ],
      where: {
        userId: res.locals.reqBody['user_id'],
      }
    }).then((result: any) => {
      if(!result) {
        // パスワード照合の処理時間を考慮したダミー処理
        this.encrypt('test', 'test');
        throw new AuthError('認証失敗');
      }

      const encryptedPassword = this.encrypt(res.locals.reqBody['password'], result.userId);
      console.log(encryptedPassword.encryptedText);
      if(result.password !== encryptedPassword.encryptedText) {
        throw new AuthError('認証失敗');
      }

      const payload = {
        companyId: result.companyId,
        userId: result.id,
        auth: result.UserDetails.auth
      };

      const info = {
        companyId: result.companyId,
        userId: result.id,
        auth: result.UserDetails.auth,
        firstName: result.UserDetails.firstName,
        lastName: result.UserDetails.lastName,
      };

      const token = jsonwebtoken.sign(payload, authConfig.jwt.secret, authConfig.jwt.options);
      const userInfo = jsonwebtoken.sign(info, authConfig.jwt.secret, authConfig.jwt.options);
      const body = {
        userInfo: userInfo,
        resultCode: 200,
      };

      // res.cookie('jwt_token', token, { httpOnly: true, sameSite: 'none', secure: true });

      // ローカル環境の場合
      res.cookie('jwt_token', token);

      res.status(200).json(body);
    }).catch((err: any) => {
      next(err);
    });
  }

  // getPasswordHash(pass: string){
  //   const secretPass: string = `${pass}${authConfig.secretPepper}`;
  //   return crypto.createHash('sha256').update(secretPass, 'utf8').digest('hex');
  // }

  // 鍵を作成
  generateKey(pass: string) {
    return crypto.scryptSync(pass, authConfig.secretPepper, 32);
  }

  // 初期化ベクトルを生成
  generateIv(str: string) {
    const buffer = Buffer.alloc(16);
    buffer.write(str);
    return buffer;
  }

  // 暗号化
  encrypt(text: string, ivStr: string) {
    const key = this.generateKey(text);
    const iv = this.generateIv(ivStr);
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    let encryptedText = cipher.update(text, 'utf8', 'hex');
    encryptedText += cipher.final('hex');
    return { iv, encryptedText };
  }
}
module.exports = LoginService;