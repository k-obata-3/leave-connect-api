import type { Request, Response, NextFunction } from 'express';
import BaseService from "./baseService";

const models = require("../models");
const utils = require("../utils");

/**
 * システム設定関連サービス
 */
export default class SystemSettingService extends BaseService {
  constructor() {
    super();
  }

  /**
   * システム設定情報取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getSystemConfigs(req: Request, res: Response, next: NextFunction) {
    await models.SystemConfigs.findAndCountAll({
      where: {
        companyId: this.getLoginCompanyId(res),
        key: res.locals.queryParams['key'],
      },
    }).then((results: any) => {
      this.setSuccessResponse(res, results.rows, results.count);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * システム設定情報削除
   * @param req 
   * @param res 
   * @param next 
   */
  deleteSystemConfig(req: Request, res: Response, next: NextFunction) {
    const id = res.locals.queryParams['id']
    models.SystemConfigs.destroy({
      where: {
        id: id,
      }
    }).then(() => {
      this.setSuccessResponse(res, null, null);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * 承認グループ一覧取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getApprovalGroupList(req: Request, res: Response, next: NextFunction) {
    let approvalGroupResponse: any = [];
    let userResponse: any = [];
    let users: any = [];
    let list: any = [];
    try {
      await models.SystemConfigs.findAndCountAll({
        where: {
          companyId: this.getLoginCompanyId(res),
          key: "approvalGroup",
        }
      }).then((results: any) => {
        approvalGroupResponse = results;
      })

      await models.Users.findAll({
        include: [
          {
            model: models.UserDetails,
            as: 'UserDetails',
          }
        ],
        where: {
          companyId: this.getLoginCompanyId(res),
        },
      }).then((results: any) => {
        userResponse = results;
      })

      for (let i = 0; i < userResponse.length; i++) {
        const userDetail = userResponse[i].UserDetails;
        const user = {
          id: userDetail.userId,
          name: `${userDetail.lastName} ${userDetail.firstName}`,
        }
        users.push(user);
      }

      for (let i = 0; i < approvalGroupResponse.rows.length; i++) {
        const row = approvalGroupResponse.rows[i];
        const approvalGroup = JSON.parse(row.value);
        const userIds = [approvalGroup.approver1, approvalGroup.approver2, approvalGroup.approver3, approvalGroup.approver4, approvalGroup.approver5];
        let approvers: any = []
        for (let i = 0; i < userIds.length; i++) {
          const user = users.find((u: any) => u.id == userIds[i]);
          if(user) {
            approvers.push(user);
          } else {
            approvers.push({
              id: Number(userIds[i]),
              name: null,
            });
          }
        }
  
        list.push({
          groupId: row.id,
          groupName: approvalGroup.groupName,
          approver: approvers,
        });
      }

      this.setSuccessResponse(res, list, approvalGroupResponse.count);
    } catch(err: any) {
      next(err);
    }
  }

  /**
   * 承認グループ保存
   * @param req 
   * @param res 
   * @param next 
   */
  async saveApprovalGroup(req: Request, res: Response, next: NextFunction) {
    const id = res.locals.reqBody['id'];
    const groupName = res.locals.reqBody['groupName'];
    const approval = res.locals.reqBody['approval'];

    const valueObject = {
      "groupName": groupName,
      "approver1": approval[0] ? approval[0] : "",
      "approver2": approval[1] ? approval[1]: "",
      "approver3": approval[2] ? approval[2] : "",
      "approver4": approval[3] ? approval[3] : "",
      "approver5": approval[4] ? approval[4] : "",
    }

    try {
      await models.SystemConfigs.findOne({
        where: {
          id: id,
          companyId: this.getLoginCompanyId(res),
        }
      }).then((result: any) => {
        if(result) {
          result.value = JSON.stringify(valueObject);
          result.save().then(() => {
            this.setSuccessResponse(res, null, null);
          }).catch((err: any) => {
            next(err);
          });
        } else {
          const req = {
            companyId: this.getLoginCompanyId(res),
            key: "approvalGroup",
            value: JSON.stringify(valueObject),
          }

          models.SystemConfigs.create(req).then(() => {
            this.setSuccessResponse(res, null, null);
          }).catch((err: any) => {
            next(err);
          });
        }
      })
    } catch(err: any) {
      next(err);
    }
  }

}
module.exports = SystemSettingService;