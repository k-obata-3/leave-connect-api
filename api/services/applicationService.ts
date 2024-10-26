import type { Request, Response, NextFunction } from 'express';
import BaseService from "./baseService";
import ApplicationModel from "../interface/applicationModel";
import { Op } from 'sequelize';
import { Task } from '../types/task';
import { ValidationError, NotFoundError } from '../errors';
import { Application } from '../types/application';

const models = require("../models");
const utils = require("../utils");
const ApplicationType = require("../enums/applicationType");
const Action = require("../enums/action");
const TaskType = require("../enums/taskType");
const TaskStatus = require("../enums/taskStatus");
const ApplicationClassification = require("../enums/applicationClassification");

/**
 * 申請関連サービス
 */
export default class ApplicationService extends BaseService {
  constructor() {
    super();
  }

  /**
   * 申請取得
   * 管理者：すべての申請情報が取得可能
   * 管理者以外：自身が申請した申請情報もしくは、自身が承認者に設定されている申請情報のみが取得可能
   * @param req 
   * @param res 
   * @param next 
   */
  async getApplication(req: Request, res: Response, next: NextFunction) {
    const id: string = res.locals.queryParams['id'];
    let responseResult: Application = {};
    let tasks: Task[] = [];

    try {
      await models.Applications.findOne({
        include: [
          {
            model: models.Tasks,
            as: 'Tasks',
            where: {
              status: {
                [Op.ne]: [TaskStatus.getTaskStatusIdByName('NON_ACTIVE')]
              },
            },
            include: [
              {
                model: models.UserDetails,
                as: 'UserDetails',
              },
            ]
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
          },
        ],
        where: {
          id: id
        }
      }).then((result: any) => {
        if(!result) {
          throw new NotFoundError('申請情報の取得に失敗しました。');
        }

        // 操作日時、タスクIDの昇順で並び替え
        tasks = result.Tasks.sort((a: any, b: any) => {
          if (a.operationDate < b.operationDate) return -1;
          if (a.operationDate > b.operationDate) return 1;
          if (a.id < b.id) return -1;
          if (a.id > b.id) return 1;
          return 0;
        });
        responseResult.id = result.id;
        responseResult.applicationUserId = result.applicationUserId;
        responseResult.type = result.type;
        responseResult.sType = ApplicationType.getApplicationTypeValueById(result.type);
        responseResult.classification = result.classification;
        responseResult.sClassification = ApplicationClassification.getClassificationValueById(result.classification);
        responseResult.applicationDate = result.applicationDate;
        responseResult.sApplicationDate = utils.getDateString(utils.getUtcDate(result.applicationDate), '/');
        responseResult.startDate = result.startDate;
        responseResult.sStartDate = utils.getDateString(utils.getUtcDate(result.startDate), '/');
        responseResult.sStartTime = utils.getTimeString(utils.getUtcDate(result.startDate));
        responseResult.endDate = result.endDate;
        responseResult.sEndDate = utils.getDateString(utils.getUtcDate(result.endDate), '/');
        responseResult.sEndTime = utils.getTimeString(utils.getUtcDate(result.endDate));
        responseResult.totalTime = result.totalTime;
        responseResult.approvalGroupId = result.approvalGroupId;
        responseResult.applicationUserName = result.UserDetails?.lastName + " " + result.UserDetails?.firstName;
      }).catch((err: any) => {
        throw err;
      });

      // ログインユーザが承認者に設定されている有効な承認タスク取得
      const availableApprovalTtask = tasks?.find((task: any) =>
        task.operationUserId == this.getLoginUserId(res) &&
        task.type === TaskType.getTaskTypeIdByName('APPROVAL') &&
        (task.status == TaskStatus.getTaskStatusIdByName('ACTIVE') ||
          task.status == TaskStatus.getTaskStatusIdByName('CLOSED') ||
          task.status == TaskStatus.getTaskStatusIdByName('HISTORY'))
      );

      // 参照権限がない申請情報を取得しようとした場合、エラーとする
      if(!this.getIsAdmin(res) && !availableApprovalTtask && responseResult?.applicationUserId != this.getLoginUserId(res)) {
        throw new ValidationError('申請情報の取得に失敗しました。');
      }

      // 申請タスク取得
      const applicationTask = tasks?.find((task: any) =>
        task.type === TaskType.getTaskTypeIdByName('APPLICATION') &&
        (task.status == TaskStatus.getTaskStatusIdByName('ACTIVE') || task.status == TaskStatus.getTaskStatusIdByName('CLOSED')));
      if(applicationTask) {
        responseResult.action = applicationTask.action;
        responseResult.sAction = applicationTask.action != null ? Action.getActionValueById(applicationTask.action) : null,
        responseResult.comment = applicationTask.comment;
      }

      // 承認タスク取得
      const approvalTtasks = tasks ? tasks.filter((task: any) => task.id != applicationTask?.id) : [];
      if(approvalTtasks) {
        const approvalTtaskResult: Task[] = [];
        for (let index = 0; index < approvalTtasks.length; index++) {
          const task = approvalTtasks[index];
          const operationDate = `${utils.getDateString(task.operationDate, '/')} ${utils.getTimeString(task.operationDate)}`
          let result: any = {
            id: task.id,
            action: task.action,
            sAction: task.type === TaskType.getTaskTypeIdByName('APPROVAL') ? Action.getActionValueById(task.action) : '申請',
            type: task.type,
            comment: task.comment,
            status: task.status,
            sStatus: TaskStatus.getTaskStatusValueById(task.status),
            userName: task.UserDetails ? task.UserDetails.lastName + " " + task.UserDetails.firstName : null,
            operationDate: task.action != Action.getActionIdByName('PANDING') ? operationDate : null,
          }

          approvalTtaskResult.push(result);
        }

        responseResult.approvalTtasks = approvalTtaskResult;
      }

      this.setSuccessResponse(res, responseResult, null);
    } catch(err: any) {
      next(err)
    }
  }

  /**
   * 申請一覧取得
   * @param req 
   * @param res 
   * @param next 
   */
  getApplicationList(req: Request, res: Response, next: NextFunction) {
    // 申請タスクのみを取得
    const whereParams: any = {
      type: TaskType.getTaskTypeIdByName('APPLICATION'),
      status: {
        [Op.or]: [
          TaskStatus.getTaskStatusIdByName('ACTIVE'),
          TaskStatus.getTaskStatusIdByName('CLOSED'),
        ]
      }
    };

    // 申請管理からの参照かどうか
    const isAdmin = res.locals.queryParams.isAdmin == 'true';

    // 検索条件 申請者
    // 申請管理からの参照かつ管理者の場合、リクエストパラメータのユーザIDで絞り込み可能
    // 上記以外の場合、ログインユーザ自身の申請情のみを取得対象とする
    const searchUserId = this.getIsAdmin(res) && isAdmin ? res.locals.queryParams.userId : this.getLoginUserId(res);
    if(searchUserId) {
      whereParams.operationUserId = searchUserId;
    }

    // 検索条件 状況
    if(res.locals.queryParams.searchAction) {
      whereParams.action = res.locals.queryParams.searchAction;
    } else {
      if(isAdmin) {
        whereParams.action = {
          [Op.ne]: [Action.getActionIdByName('DRAFT')],
        }
      }
    }

    const applicationWhereParams: any = {};

    // 検索条件 申請年
    const searchYear = res.locals.queryParams.searchYear;
    if(searchYear) {
      applicationWhereParams.startDate = {
        [Op.and]: {
          [Op.gte]: `${searchYear}-01-01`,
          [Op.lte]: `${searchYear}-12-31`,
        }
      }
    }

    const responseResult: any = [];
    models.Tasks.findAndCountAll({
      include: [
        {
          model: models.Applications,
          as: 'Applications',
          where: applicationWhereParams,
        },
        {
          model: models.Users,
          as: 'Users',
          where: {
            companyId: this.getLoginCompanyId(res)
          },
        },
      ],
      where: whereParams,
      offset: Number(res.locals.queryParams['offset']),
      limit: Number(res.locals.queryParams['limit'])
    }).then((results: any) => {
      results.rows.forEach((result: any) => {
        const applications: ApplicationModel = result.Applications;
        if(applications) {
          const item = {
            id: result.applicationId,
            applicationUserId: result.operationUserId,
            type: applications.type,
            sType: ApplicationType.getApplicationTypeValueById(applications.type),
            classification: applications.classification,
            sClassification: ApplicationClassification.getClassificationValueById(applications.classification),
            applicationDate: applications.applicationDate,
            sApplicationDate: utils.getDateString(utils.getUtcDate(applications.applicationDate), '/'),
            startDate: applications.startDate,
            sStartDate: utils.getDateString(utils.getUtcDate(applications.startDate), '/'),
            sStartTime: utils.getTimeString(utils.getUtcDate(applications.startDate)),
            endDate: applications.endDate,
            sEndDate: utils.getDateString(utils.getUtcDate(applications.endDate), '/'),
            sEndTime: utils.getTimeString(utils.getUtcDate(applications.endDate)),
            action: result.action,
            sAction: result.action != null ? Action.getActionValueById(result.action) : null,
            approvalGroupId: applications.approvalGroupId,
            comment: result.comment,
          } as Application;

          responseResult.push(item);
        }
      });
      this.setSuccessResponse(res, responseResult, results.count);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * 月間の申請一覧取得
   * @param req 
   * @param res 
   * @param next 
   */
  getApplicationListByMonth(req: Request, res: Response, next: NextFunction) {
    // const id: string = res.locals.queryParams['id']
    const start: string = res.locals.queryParams['start']
    const end: string = res.locals.queryParams['end']

    const responseResult: any = [];
    models.Applications.findAll({
      include: [
        {
          model: models.Tasks,
          as: 'Tasks',
          where: {
            type: TaskType.getTaskTypeIdByName('APPLICATION'),
            status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
            action: {
              [Op.ne]: [Action.getActionIdByName('CANCEL')],
            },
          }
        },
      ],
      where: {
        applicationUserId: this.getLoginUserId(res),
        startDate: {
          [Op.and]: {
            [Op.gte]: start,
            [Op.lte]: end,
          }
        }
      }
    }).then((result: any) => {
      if(result) {
        result.forEach((row: any) => {
          let item = {
            id: row.id,
            applicationUserId: row.applicationUserId,
            sType: ApplicationType.getApplicationTypeValueById(row.type),
            sClassification: ApplicationClassification.getClassificationValueById(row.classification),
            startDate: row.startDate,
            sStartDate: utils.getDateString(utils.getUtcDate(row.startDate), '-'),
            sStartTime: utils.getTimeString(utils.getUtcDate(row.startDate)),
            endDate: row.endDate,
            sEndDate: utils.getDateString(utils.getUtcDate(row.endDate), '-'),
            sEndTime: utils.getTimeString(utils.getUtcDate(row.endDate)),
          } as Application;

          if(row.Tasks) {
            item.action = row.Tasks[0].action;
            item.sAction = Action.getActionValueById(row.Tasks[0].action);
          }
  
          responseResult.push(item);
        })
      }

      this.setSuccessResponse(res, responseResult, null);
    }).catch((err: any) => {
      next(err);
    });
  }

  /**
   * 申請
   * @param req 
   * @param res 
   * @param next 
   * @returns 
   */
  async saveApplication(req: Request, res: Response, next: NextFunction) {
    const startDate: Date = utils.getUtcDate(`${res.locals.reqBody['startEndDate']} ${res.locals.reqBody['startTime']}`);
    const endDate: Date = utils.getUtcDate(`${res.locals.reqBody['startEndDate']} ${res.locals.reqBody['endTime']}`);
    const applicationId = res.locals.reqBody['id'];

    if(startDate >= endDate) {
      next(new ValidationError("取得時間の大小関係が不正です。"));
      return;
    }

    // 開始時間と終了時間の差分を取得
    const timeDiff: number = endDate.getTime() - startDate.getTime();
    const hoursDiff: number = Math.ceil(timeDiff / (60 * 60 * 1000));

    // 差分が9時間（休憩時間含む）を超えている場合は、1日の所定労働時間を超過しているためエラーとする
    if(hoursDiff > 9) {
      next(new ValidationError("取得時間が不正です。※取得時間は1日の所定労働時間を超えないように入力してください。"));
      return;
    }

    const classification = res.locals.reqBody['classification'];
    const isAllDays = hoursDiff == 9;
    const isHalfDaysAm = startDate.getHours() < 12 && (startDate.getHours() + 4 === endDate.getHours() || startDate.getHours() + 5 === endDate.getHours());
    const isHalfDaysPm = startDate.getHours() >= 12 && endDate.getHours() - 4 === startDate.getHours();

    if(classification != ApplicationClassification.getClassificationIdByName('ALL_DAYS') && isAllDays) {
      next(new ValidationError("区分が不正です。※取得時間が区分「全日」の条件を満たしています。"));
      return;
    }

    if(classification == ApplicationClassification.getClassificationIdByName('ALL_DAYS') && !isAllDays) {
      next(new ValidationError("取得時間が不正です。※取得時間が区分「全日」の条件を満たしていません。"));
      return;
    }

    if(classification == ApplicationClassification.getClassificationIdByName('HALF_DAYS_AM') && !isHalfDaysAm) {
      next(new ValidationError("取得時間が不正です。※取得時間が区分「AM半休」の条件を満たしていません。"));
      return;
    }

    if(classification == ApplicationClassification.getClassificationIdByName('HALF_DAYS_PM') && !isHalfDaysPm) {
      next(new ValidationError("取得時間が不正です。※取得時間が区分「PM半休」の条件を満たしていません。"));
      return;
    }

    const startEndDate = (res.locals.reqBody['startEndDate']).replaceAll('/', '-');
    const sameDayApplication = await models.Applications.findOne({
      include: [
        {
          model: models.Tasks,
          as: 'Tasks',
          where: {
            type: TaskType.getTaskTypeIdByName('APPLICATION'),
            status: {
              [Op.or]: [
                TaskStatus.getTaskStatusIdByName('ACTIVE'),
                TaskStatus.getTaskStatusIdByName('CLOSED'),
              ]
            }
          }
        },
      ],
      where: {
        applicationUserId: this.getLoginUserId(res),
        classification: classification,
        startDate: {
          [Op.and]: {
            [Op.gte]: `${startEndDate} 00:00:00`,
            [Op.lte]: `${startEndDate} 23:59:59`,
          }
        }
      }
    }).catch((err: any) => {
      throw err;
    })

    if (sameDayApplication && sameDayApplication.id != applicationId) {
      next(new ValidationError("取得日および区分が同じ申請情報が登録済みです。"));
      return;
    }

    const param = {
      applicationUserId: this.getLoginUserId(res),
      type: res.locals.reqBody['type'],
      classification: res.locals.reqBody['classification'],
      startDate: startDate,
      endDate: endDate,
      totalTime: res.locals.reqBody['totalTime'],
      comment: res.locals.reqBody['comment'],
      action: res.locals.reqBody['action'],
      approvalGroupId: res.locals.reqBody['approvalGroupId'],
    };

    const approverIds = await models.SystemConfigs.findOne({
      where: {
        id: param.approvalGroupId,
        companyId: this.getLoginCompanyId(res),
      }
    }).then((res: any) => {
      const approvalGroup = JSON.parse(res.value);
      return [approvalGroup.approver1, approvalGroup.approver2, approvalGroup.approver3, approvalGroup.approver4, approvalGroup.approver5].filter(val => val);
    }).catch((err: any) => {
      throw err;
    })

    const t = await models.sequelize.transaction();
    if(applicationId) {
      models.Applications.findOne({
        where: {
          id: applicationId,
        }
      }, {transaction: t}).then(async(result: any) => {
        result.type = param.type;
        result.classification = param.classification
        result.startDate = param.startDate;
        result.endDate = param.endDate;
        result.totalTime = param.totalTime;
        result.comment = param.comment;
        result.approvalGroupId = param.approvalGroupId;
        result.save({transaction: t});

        await this.upsertTasks(res, param, result, approverIds, t);
        await t.commit();
        this.setSuccessResponse(res, result, null);
      }).catch(async(err: any) => {
        await t.rollback();
        next(err);
      });
    } else {
      await models.Applications.create(param, {transaction: t}).then(async(result: any) => {
        await this.upsertTasks(res, param, result, approverIds, t);
        await t.commit();
        this.setSuccessResponse(res, result, null);
      }).catch(async(err: any) => {
        await t.rollback();
        next(err);
      });
    }
  }

  // タスクの更新
  async upsertTasks(res: Response, param: any, result: any, approverIds: string[], t: any) {
    // 申請者の申請タスク更新
    await this.upsertApplicationTask(result.id, param.applicationUserId, param.action, param.comment, t);

    // 申請の場合、承認タスクの更新を行う
    if(param.action == Action.getActionIdByName('PANDING')) {
      // 前回申請分の却下状態の申請タスクをクローズする
      await this.closeRejectApplicationTask(result.id, t);

      // 前回申請分の承認タスクをクローズする
      await this.closeOldApprovalTask(result.id, t);

      // 承認者の承認タスク作成
      for (let i = 0; i < approverIds.length; i++) {
        if(approverIds[i] != this.getLoginUserId(res)) {
          await this.createApprovalTask(result.id, approverIds[i], Action.getActionIdByName('PANDING'), TaskStatus.getTaskStatusIdByName('ACTIVE'), null, t);
        }
      }
    }
  }

  // 前回申請分の却下状態の申請タスクをクローズする
  // ステータスを「HISTORY」に更新
  async closeRejectApplicationTask(id: string, t: any) {
    await models.Tasks.findOne({
      where: {
        applicationId: id,
        type: TaskType.getTaskTypeIdByName('APPLICATION'),
        status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
        action:Action.getActionIdByName('REJECT'),
      }
    }, {transaction: t}).then(async(result: any) => {
      if(result) {
        result.status = TaskStatus.getTaskStatusIdByName('HISTORY');
        await result.save({transaction: t});
      }
    }).catch(async(err: any) => {
      throw err;
    });
  }

  // 前回申請分の承認タスクをクローズする
  // ステータスを「HISTORY」に更新
  async closeOldApprovalTask(id: string, t: any) {
    await models.Tasks.findAll({
      where: {
        applicationId: id,
        type: TaskType.getTaskTypeIdByName('APPROVAL'),
        status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
      }
    }, {transaction: t}).then(async(results: any) => {
      for (let i = 0; i < results.length; i++) {
        results[i].status = TaskStatus.getTaskStatusIdByName('HISTORY');
        await results[i].save({transaction: t});
      }
    }).catch(async(err: any) => {
      throw err;
    });
  }

  // 承認タスク作成
  async createApprovalTask(id: string, userId: string, operationAction: string, status: string, comment: string | null, t: any) {
    await models.Tasks.create({
      applicationId: id,
      operationUserId: userId,
      type: TaskType.getTaskTypeIdByName('APPROVAL'),
      action: operationAction,
      comment: comment,
      status: status,
    }, {transaction: t}).catch(async(err: any) => {
      throw err;
    });
  }

  // 申請タスク取得
  async getApplicationTask(id: string, userId: string, t: any) {
    await models.Tasks.findOne({
      where: {
        applicationId: id,
        operationUserId: userId,
        type: TaskType.getTaskTypeIdByName('APPLICATION'),
        status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
      }
    }, {transaction: t}).then(async(result: any) => {
      return result;
    }, {transaction: t}).catch(async(err: any) => {
      throw err;
    });
  }

  // 申請タスク作成
  async createApplicationTask(id: string, userId: string, operationAction: string, comment: string | null, t: any) {
    await models.Tasks.create({
      applicationId: id,
      operationUserId: userId,
      type: TaskType.getTaskTypeIdByName('APPLICATION'),
      action: operationAction,
      comment: comment ? comment : null,
      status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
    }, {transaction: t}).catch(async(err: any) => {
      throw err;
    });
  }

  // 申請タスク更新
  async upsertApplicationTask(id: string, userId: string, operationAction: string, comment: string | null, t: any) {
    await models.Tasks.findOne({
      where: {
        applicationId: id,
        operationUserId: userId,
        type: TaskType.getTaskTypeIdByName('APPLICATION'),
        action: {
          [Op.ne]: Action.getActionIdByName('REJECT'),
        },
        status: TaskStatus.getTaskStatusIdByName('ACTIVE'),
      }
    }, {transaction: t}).then(async(result: any) => {
      if(result) {
        result.comment = comment ? comment : null;
        result.action = operationAction;

        result.operationDate = utils.getLocalCurrentDate();
        await result.save({transaction: t});
      } else {
        await this.createApplicationTask(id, userId, operationAction, comment, t);
      }
    }).catch(async(err: any) => {
      throw err;
    });
  }

  /**
   * 申請削除
   * @param req 
   * @param res 
   * @param next 
   */
  async deleteApplication(req: Request, res: Response, next: NextFunction) {
    const id = res.locals.queryParams['id'];

    const t = await models.sequelize.transaction();
    const deleteApprovalTask = async() => {
      await models.Tasks.destroy({
        where: {
          applicationId: id,
        },
        transaction: t
      });
    }

    const deleteApplication = async() => {
      await models.Applications.destroy({
        where: {
          id: id,
          applicationUserId: this.getLoginUserId(res),
        },
        transaction: t
      });
    }

    try {
      await deleteApprovalTask();
      await deleteApplication();
      await t.commit();
      this.setSuccessResponse(res, null, null);
    } catch(err) {
      await t.rollback();
      next(err);
    }
  }

  /**
   * 申請取消
   * @param req 
   * @param res 
   * @param next 
   */
  async cancelApplication(req: Request, res: Response, next: NextFunction) {
    const applicationId = res.locals.reqBody['applicationId'];
    const comment = res.locals.reqBody['comment'];

    // 自動計算残日数を再計算する
    // 承認時に減算した分を自動計算残日数に加算する
    const updateAutoCalcRemainingDays = async(application: any, t: any) => {
      const resultHour = utils.getApplicationHour(application.totalTime);
      application.UserDetails.autoCalcRemainingDays += resultHour;
      application.UserDetails.totalDeleteDays -= resultHour;
      await application.UserDetails.save({transaction: t});
    }

    const t = await models.sequelize.transaction();
    try {
      await models.Applications.findOne({
        include: [
          {
            model: models.Tasks,
            as: 'Tasks',
            where: {
              status: {
                [Op.or]: [
                  TaskStatus.getTaskStatusIdByName('ACTIVE'),
                  TaskStatus.getTaskStatusIdByName('CLOSED')
                ]
              },
            },
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
          },
        ],
        where: {
          id: applicationId
        }
      }, {transaction: t}).then(async(result: any) => {
        if(!result) {
          throw Error('申請情報取得失敗');
        }

        for (let i = 0; i < result.Tasks.length; i++) {
          const task = result.Tasks[i];
          if(task.type == TaskType.getTaskTypeIdByName('APPLICATION')) {
            // 申請が完了していた場合、自動計算残日数を再計算する
            if(task.action == Action.getActionIdByName('COMPLETE')) {
              await updateAutoCalcRemainingDays(result, t);
            }

            // 申請タスクを取消する
            task.action = Action.getActionIdByName('CANCEL');
            task.status = TaskStatus.getTaskStatusIdByName('CLOSED');
            await task.save({transaction: t});
          } else {
            // 「進行中」状態の承認タスクを処理済に変更する
            if(task.status == TaskStatus.getTaskStatusIdByName('ACTIVE')) {
              if(task.action === Action.getActionIdByName('PANDING')) {
                // 取消した場合、申請に紐づく「承認待ち」状態の承認タスクのアクションは「システム取消」に変更する
                task.action = Action.getActionIdByName('SYSTEM_CANCEL');
                task.status = TaskStatus.getTaskStatusIdByName('NON_ACTIVE');
              } else {
                task.status = TaskStatus.getTaskStatusIdByName('CLOSED');
              }
              await task.save({transaction: t});
            }
          }
        }

        // 取消タスク作成
        await this.createApprovalTask(applicationId, this.getLoginUserId(res), Action.getActionIdByName('CANCEL'), TaskStatus.getTaskStatusIdByName('CLOSED'), comment, t);
      }).catch(async(err: any) => {
        throw err;
      });

      t.commit();
      this.setSuccessResponse(res, null, null);
    } catch(err: any) {
      t.rollback();
      next(err);
    }
  }

}
module.exports = ApplicationService;