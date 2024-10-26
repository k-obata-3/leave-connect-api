import type { Request, Response, NextFunction } from 'express';
import BaseService from "./baseService";
import { Op } from 'sequelize';
import { NotFoundError, ValidationError } from '../errors';

const models = require("../models");
const utils = require("../utils");
const Action = require("../enums/action");
const TaskType = require("../enums/taskType");
const TaskStatus = require("../enums/taskStatus");

/**
 * ユーザ情報関連サービス
 */
export default class UserService extends BaseService {
  constructor() {
    super();
  }

  /**
   * ログインユーザ情報取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getLoginUserInfo(req: Request, res: Response, next: NextFunction) {
    this.getUserInfo(res, this.getLoginUserId(res)).then((result: any) => {
      this.setSuccessResponse(res, result, null);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * ユーザ情報取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getUserDetails(req: Request, res: Response, next: NextFunction) {
    const userId = res.locals.queryParams['id'] ? res.locals.queryParams['id'] : this.getLoginUserId(res);
    this.getUserInfo(res, userId).then((result: any) => {
      this.setSuccessResponse(res, result, null);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * ユーザ一覧取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getUserList(req: Request, res: Response, next: NextFunction) {
    this.getUserAll(res).then((results: any) => {
      let list: any = [];
      results.rows.forEach((result: any) => {
        list.push(this.createUserInfoObj(result));
      });

      this.setSuccessResponse(res, list, results.count);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * ユーザ名一覧取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getUserNameList(req: Request, res: Response, next: NextFunction) {
    this.getUserAll(res).then((results: any) => {
      let list: any = [];
      results.rows.forEach((result: any) => {
        list.push({
          id: result.id,
          fullName: result.UserDetails ? result.UserDetails.lastName + " " + result.UserDetails.firstName : null,
          auth: result.UserDetails ? result.UserDetails.auth : null,
        });
      });

      this.setSuccessResponse(res, list, results.count);
    }).catch((err: any) => {
      next(err);
    });
  }

  // ユーザ情報取得
  async getUserInfo(res: Response, id: string) {
    const result = await models.Users.findOne({
      include: [
        {
          model: models.UserDetails,
          as: 'UserDetails',
        }
      ],
      where: {
        id: id,
        companyId: this.getLoginCompanyId(res),
      },
    }).catch((err: any) => {
      throw err;
    });

    if(!result) {
      throw new NotFoundError('ユーザ情報が取得できませんでした。')
    }

    return this.createUserInfoObj(result);
  }


  // ユーザ情報一括取得
  async getUserAll(res: Response) {
    const offset = res.locals.queryParams['offset'] ? Number(res.locals.queryParams['offset']) : 0;
    const limit = res.locals.queryParams['limit'] ? Number(res.locals.queryParams['limit']): null;

    const results = await models.Users.findAndCountAll({
      include: [
        {
          model: models.UserDetails,
          as: 'UserDetails',
        }
      ],
      where: {
        companyId: this.getLoginCompanyId(res)
      },
      offset: offset,
      limit: limit
    }).catch((err: any) => {
      throw err;
    });

    if(!results) {
      throw new NotFoundError('ユーザ情報が取得できませんでした。')
    }

    return results;
  }

  // ユーザ情報オブジェクト作成
  createUserInfoObj(result: any) {
    let user = {
      id: result.id,
      userId: result.userId,
      companyId: result.companyId,
      firstName: null,
      lastName: null,
      auth: null,
      referenceDate: null,
      workingDays: 0,
      totalDeleteDays: 0,
      totalAddDays: 0,
      totalRemainingDays: 0,
      autoCalcRemainingDays: 0,
      totalCarryoverDays: 0,
    }

    const userDetails = result.UserDetails;
    if(userDetails) {
      user.firstName = userDetails.firstName;
      user.lastName = userDetails.lastName;
      user.auth = userDetails.auth;
      user.referenceDate = userDetails.referenceDate ? utils.getDateString(utils.getLocalDate(userDetails.referenceDate), '/') : null;
      user.workingDays = userDetails.workingDays;
      user.totalDeleteDays = userDetails.totalDeleteDays;
      user.totalAddDays = userDetails.totalAddDays;
      user.totalRemainingDays = Number(userDetails.totalAddDays) + Number(userDetails.totalCarryoverDays) - Number(userDetails.totalDeleteDays);
      user.autoCalcRemainingDays = userDetails.autoCalcRemainingDays;
      user.totalCarryoverDays = userDetails.totalCarryoverDays;
    }

    return user;
  }

  /**
   * ユーザ情報保存
   * @param req 
   * @param res 
   * @param next 
   */
  async saveUser(req: Request, res: Response, next: NextFunction) {
    let param = {
      lastName: res.locals.reqBody['lastName'],
      firstName: res.locals.reqBody['firstName'],
      referenceDate: utils.getUtcDate(res.locals.reqBody['referenceDate']),
      workingDays: res.locals.reqBody['workingDays'],
      totalDeleteDays: res.locals.reqBody['totalDeleteDays'],
      totalAddDays: res.locals.reqBody['totalAddDays'],
      totalRemainingDays: res.locals.reqBody['totalRemainingDays'],
      totalCarryoverDays: res.locals.reqBody['totalCarryoverDays'],
    }

    const updateUserInfo = async(t: any) => {
      await models.UserDetails.findOne({
        where: {
          userId: res.locals.reqBody['id'],
        }
      }, {transaction: t}).then(async(result: any) => {
        result.lastName = param.lastName;
        result.firstName = param.firstName;
        result.referenceDate = param.referenceDate;
        result.workingDays = param.workingDays;
        result.totalDeleteDays = param.totalDeleteDays;
        result.totalAddDays = param.totalAddDays;
        // result.totalRemainingDays = param.totalRemainingDays;
        result.totalCarryoverDays = param.totalCarryoverDays;
        await result.save({transaction: t});
      }).catch((err: any) => {
        throw err;
      });
    }

    const t = await models.sequelize.transaction();
    try {
      await updateUserInfo(t);
      t.commit();
      this.setSuccessResponse(res, null, null);
    } catch (err: any) {
      t.rollback();
      next(err);
    }
  }

  /**
   * 付与日数更新
   * @param req 
   * @param res 
   * @param next 
   */
  async updateGrantDays(req: Request, res: Response, next: NextFunction) {
    let param = {
      lastName: res.locals.reqBody['lastName'],
      firstName: res.locals.reqBody['firstName'],
      referenceDate: utils.getLocalDate(res.locals.reqBody['referenceDate']),
      workingDays: res.locals.reqBody['workingDays'],
      totalDeleteDays: res.locals.reqBody['totalDeleteDays'],
      totalAddDays: res.locals.reqBody['totalAddDays'],
      totalRemainingDays: res.locals.reqBody['totalRemainingDays'],
      totalCarryoverDays: res.locals.reqBody['totalCarryoverDays'],
    }

    const userId = res.locals.reqBody['id'];
console.log(userId);
    this.getUserInfo(res, userId).then((result: any) => {
      const referenceDate: Date = utils.getLocalDate(result.referenceDate);
      const elapsedYears: number = utils.getElapsedYears(referenceDate);
      const elapsedMonths: number = utils.getElapsedMonths(referenceDate);
      referenceDate.setFullYear(referenceDate.getFullYear() + elapsedYears);
console.log(referenceDate);
console.log(elapsedYears);
console.log(elapsedMonths);
      if(referenceDate > utils.getLocalCurrentDate()){
        next(new ValidationError("付与日更新は不要です。"));
        return;
      }


      // システム設定情報からデータを取得する

      // 上記で求めたelapsedMonthsとシステム取得したデータのsectionMonth、workingDaysから付与日数を取得する。
      // 【課題】二重に付与をどのように制御するか。。。


      this.setSuccessResponse(res, result, null);
    }).catch((err: any) => {
      next(err);
    });


  }

  /**
   * 通知情報取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getNotification(req: Request, res: Response, next: NextFunction) {
    await models.Tasks.findAll({
      where: {
        operationUserId: this.getLoginUserId(res),
        [Op.or]: [
          {
              type: TaskType.getTaskTypeIdByName('APPLICATION'),
              action: {
                [Op.or]: [
                  [Action.getActionIdByName('PANDING')],
                  [Action.getActionIdByName('REJECT')],
                ]
              }
          },
          {
              type: TaskType.getTaskTypeIdByName('APPROVAL'),
              action: Action.getActionIdByName('PANDING'),
          }
        ],
        status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
      },
    }).then((results: any) => {
      // 対応が必要な申請の件数
      let actionRequiredApplicationCount = results.filter((result: any) =>
        result.type === TaskType.getTaskTypeIdByName('APPLICATION') && result.action === Action.getActionIdByName('REJECT'));
      // 承認待ちタスクの件数取得
      let approvalTaskCount = results.filter((result: any) =>
        result.type === TaskType.getTaskTypeIdByName('APPROVAL') && result.action === Action.getActionIdByName('PANDING'));
      // 申請中の件数
      let activeApplicationCount = results.filter((result: any) =>
        result.type === TaskType.getTaskTypeIdByName('APPLICATION')　&& result.action === Action.getActionIdByName('PANDING'));

      const responseResult = {
        "actionRequiredApplicationCount": actionRequiredApplicationCount.length,
        "approvalTaskCount": approvalTaskCount.length,
        "activeApplicationCount": activeApplicationCount.length
      }

      this.setSuccessResponse(res, responseResult, null);
    }).catch((err: any) => {
      next(err)
    });
  }

}
module.exports = UserService;