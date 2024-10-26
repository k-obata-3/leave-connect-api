'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class Tasks extends Model {
    static associate(models) {
      Tasks.hasOne(models.Applications, {
        sourceKey: 'applicationId',
        foreignKey: 'id',
        as: 'Applications'
      }),
      Tasks.hasOne(models.UserDetails, {
        sourceKey: 'operationUserId',
        foreignKey: 'userId',
        as: 'UserDetails'
      }),
      Tasks.hasOne(models.Users, {
        sourceKey: 'operationUserId',
        foreignKey: 'id',
        as: 'Users',
      });
    }
  }
  Tasks.init({
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
      allowNull: false,
      field: 'id'
    },
    applicationId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'application_id'
    },
    operationUserId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'operation_user_id'
    },
    action: {
      type: DataTypes.BIGINT,
      allowNull: true,
      field: 'action'
    },
    type: {
      type: DataTypes.BIGINT,
      allowNull: false,
      defaultValue: 0,
      field: 'type'
    },
    comment: {
      type: DataTypes.STRING(1000),
      allowNull: true,
      field: 'comment'
    },
    status: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'status'
    },
    operationDate: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'operation_date'
    },
    created: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'created'
    },
    updated: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW,
      field: 'updated'
    },
    version: {
      type: DataTypes.BIGINT,
      allowNull: false,
      defaultValue: 1,
      field: 'version'
    }
  }, {
    sequelize,
    tableName: 'tasks',
    modelName: 'Tasks',
    version: true,
  });

  return Tasks;
};