import type { Request, Response, NextFunction } from 'express';
import BaseService from "./baseService";
import { Op } from 'sequelize';

const models = require("../models");
const utils = require("../utils");
const action = require("../enums/action");
const applicationType = require("../enums/ApplicationType");
const TaskType = require("../enums/taskType");
const TaskStatus = require("../enums/taskStatus");
const applicationClassification = require("../enums/ApplicationClassification");

/**
 * 承認関連サービス
 */
export default class ApprovalService extends BaseService {
  constructor() {
    super();
  }

  /**
   * 承認タスク一覧取得
   * @param req 
   * @param res 
   * @param next 
   */
  async getApprovalTaskList(req: Request, res: Response, next: NextFunction) {
    // 承認タスクのみを取得
    const whereParams: any = {
      operationUserId: this.getLoginUserId(res),
      type: TaskType.getTaskTypeIdByName('APPROVAL'),
      action: {
        [Op.or]: [
          [action.getActionIdByName('PANDING')],
          [action.getActionIdByName('APPROVAL')],
          [action.getActionIdByName('REJECT')],
        ],
      },
      status: {
        [Op.or]: [
          TaskStatus.getTaskStatusIdByName('ACTIVE'),
          TaskStatus.getTaskStatusIdByName('CLOSED'),
          TaskStatus.getTaskStatusIdByName('HISTORY'),
        ]
      }
    };

    if(res.locals.queryParams['searchAction']) {
      whereParams['action'] = res.locals.queryParams['searchAction'];
    }

    const applicationWhereParams: any = {
    };

    if(res.locals.queryParams['searchUserId']) {
      applicationWhereParams['applicationUserId'] = res.locals.queryParams['searchUserId'];
    }

    const getApplicationList = async(next: NextFunction) => {
      return await models.Applications.findAndCountAll({
        include: [
          {
            model: models.Tasks,
            as: 'Tasks',
            where: whereParams,
          },
          {
            model: models.UserDetails,
            as: 'UserDetails',
          },
          {
            model: models.Users,
            as: 'Users',
            where: {
              companyId: this.getLoginCompanyId(res)
            },
          }
        ],
        where: applicationWhereParams,
        offset: Number(res.locals.queryParams['offset']),
        limit: Number(res.locals.queryParams['limit']),
      }).then((results: any) => {
        return results;
      }).catch((err: any) => {
        next(err)
      });
    };

    const applicationList: any = await getApplicationList(next);

    const list: any = [];
    applicationList.rows.forEach((result: any) => {
      const tasks = result.Tasks.reverse();
      let approval: any = {
        id: tasks[0].id,
        applicationId: result.id,
        type: result.type,
        sType: applicationType.getApplicationTypeValueById(result.type),
        classification: result.classification,
        sClassification: applicationClassification.getClassificationValueById(result.classification),
        sApplicationDate: utils.getDateString(utils.getUtcDate(result.applicationDate), '/'),
        sStartDate: utils.getDateString(utils.getUtcDate(result.startDate), '/'),
        sEndDate: utils.getDateString(utils.getUtcDate(result.endDate), '/'),
        sStartTime: utils.getTimeString(utils.getUtcDate(result.startDate)),
        sEndTime: utils.getTimeString(utils.getUtcDate(result.endDate)),
        action: tasks[0].action,
        sAction: action.getActionValueById(tasks[0].action),
        comment: tasks[0].comment,
        applicationUserName: result.UserDetails ? result.UserDetails.lastName + " " +result.UserDetails.firstName : null,
      }
      list.push(approval);
    });

    this.setSuccessResponse(res, list, applicationList.count);
  }

  /**
   * 承認
   * @param req 
   * @param res 
   * @param next 
   */
  async approve(req: Request, res: Response, next: NextFunction) {
    let param = {
      applicationId: res.locals.reqBody['application_id'],
      taskId: res.locals.reqBody['task_id'],
      comment: res.locals.reqBody['comment'],
      action: res.locals.reqBody['action'],
    }

    const t = await models.sequelize.transaction();
    await models.Tasks.findAll({
      include: [
        {
          model: models.Applications,
          as: 'Applications',
        },
        {
          model: models.Users,
          as: 'Users',
          where: {
            companyId: this.getLoginCompanyId(res)
          },
        },
      ],
      where: {
        applicationId: param.applicationId,
        status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
      }
    }, {transaction: t}).then(async(results: any) => {
      let applicationTask = null;
      let approvalTask = null;
      let approvalTasks = [];
      let isTaskAllApproval = true;
      for (let i = 0; i < results.length; i++) {
        if(results[i].type == TaskType.getTaskTypeIdByName('APPLICATION')) {
          // 申請タスク
          applicationTask = results[i];
        } else {
          // 承認タスク
          if(results[i].id == param.taskId) {
            approvalTask = results[i];
          } else {
            approvalTasks.push(results[i]);
            // 承認タスクがすべて「承認」状態かを判定
            if(results[i].action != action.getActionIdByName('APPROVAL')) {
              isTaskAllApproval = false;
            }
          }
        }
      }

      if(param.action == action.getActionIdByName('APPROVAL')) {
        // 承認操作の場合

        // 承認タスクがすべて「承認」状態の場合、承認完了処理を実行する
        if(isTaskAllApproval) {
          await this.completeApproval(applicationTask, approvalTask, approvalTasks, param, t);
        } else {
          approvalTask.action = param.action;
          approvalTask.comment = param.comment ? param.comment : null;
          approvalTask.operationDate = utils.getLocalCurrentDate();
          await approvalTask.save({transaction: t});
        }
      }else if(param.action == action.getActionIdByName('REJECT')) {
        // 却下操作の場合
        approvalTask.action = param.action;
        approvalTask.comment = param.comment ? param.comment : null;
        approvalTask.operationDate = utils.getLocalCurrentDate();
        await approvalTask.save({transaction: t});

        //　申請タスクも「却下」状態に変更する
        applicationTask.action = param.action;
        await applicationTask.save({transaction: t});

        for (let i = 0; i < approvalTasks.length; i++) {
          if(approvalTasks[i].action == action.getActionIdByName('PANDING')) {
            // 却下した場合、申請に紐づく「承認待ち」状態の承認タスクのアクションは「システム取消」に変更する
            approvalTasks[i].action = action.getActionIdByName('SYSTEM_CANCEL');
            approvalTasks[i].status = TaskStatus.getTaskStatusIdByName('NON_ACTIVE');
            await approvalTasks[i].save({transaction: t});
          }
        }
      }

      t.commit();
      this.setSuccessResponse(res, null, null);
    }).catch(async(err: any) => {
      t.rollback();
      next(err);
    });
  }

  // 承認完了処理
  async completeApproval(applicationTask: any, approvalTask: any, approvalTasks: any, param: any, t: any) {
    // 申請タスク更新
    // 申請タスクのアクションを「完了」、ステータスを「処理済」に変更する
    applicationTask.action = action.getActionIdByName('COMPLETE');
    applicationTask.status = TaskStatus.getTaskStatusIdByName('CLOSED');
    await applicationTask.save({transaction: t})
    // 承認タスク更新
    approvalTask.action = param.action;
    approvalTask.comment = param.comment ? param.comment : null;
    approvalTask.status = TaskStatus.getTaskStatusIdByName('CLOSED');
    approvalTask.operationDate = utils.getLocalCurrentDate();
    await approvalTask.save({transaction: t});
    // その他の承認タスクのステータスを「処理済」に変更する
    for (let i = 0; i < approvalTasks.length; i++) {
      approvalTasks[i].status = TaskStatus.getTaskStatusIdByName('CLOSED');
      await approvalTasks[i].save({transaction: t});
    }

    const resultHour = utils.getApplicationHour(applicationTask.Applications.totalTime);
    // console.log(resultHour);

    await models.UserDetails.findOne({
      where: {
        userId: applicationTask.operationUserId,
      },
    }, {transaction: t}).then(async(result: any) => {
      if(result) {
        if(result.autoCalcRemainingDays < resultHour) {
          throw Error('時間超過エラー');
        }
        result.autoCalcRemainingDays -= resultHour;
        result.totalDeleteDays += resultHour;
        await result.save({transaction: t});
      }
    }).catch(async(err: any) => {
      throw err;
    });
  }
}
module.exports = ApprovalService;