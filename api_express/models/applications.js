'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class Applications extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
      Applications.hasMany(models.Tasks, {
        sourceKey: 'id',
        foreignKey: 'applicationId',
        as: 'Tasks'
      }),
      Applications.hasOne(models.UserDetails, {
        sourceKey: 'applicationUserId',
        foreignKey: 'userId',
        as: 'UserDetails'
      }),
      Applications.hasOne(models.Users, {
        sourceKey: 'applicationUserId',
        foreignKey: 'id',
        as: 'Users',
      });
    }
  }
  Applications.init({
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
      allowNull: false,
      field: 'id'
    },
    applicationUserId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'application_user_id'
    },
    type: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'type'
    },
    classification: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'classification'
    },
    applicationDate: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'application_date'
    },
    startDate: {
      type: DataTypes.DATE,
      allowNull: false,
      field: 'start_date'
    },
    endDate: {
      type: DataTypes.DATE,
      allowNull: false,
      field: 'end_date'
    },
    totalTime: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'total_time'
    },
    approvalGroupId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'approval_group_id'
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
    tableName: 'applications',
    modelName: 'Applications',
    version: true,
  });

  return Applications;
};