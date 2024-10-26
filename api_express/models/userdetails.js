'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class UserDetails extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
      UserDetails.hasOne(models.Users, {
        sourceKey: 'userId',
        foreignKey: 'id',
        as: 'Users',
      });
    }
  }
  UserDetails.init({
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
      allowNull: false,
      field: 'id'
    },
    userId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'user_id'
    },
    firstName: {
      type: DataTypes.STRING(100),
      allowNull: false,
      field: 'first_name'
    },
    lastName: {
      type: DataTypes.STRING(100),
      allowNull: false,
      field: 'last_name'
    },
    auth: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'auth'
    },
    referenceDate: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'reference_date'
    },
    workingDays: {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0,
      field: 'working_days'
    },
    totalDeleteDays: {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0,
      field: 'total_delete_days'
    },
    totalAddDays: {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0,
      field: 'total_add_days'
    },
    totalRemainingDays: {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0,
      field: 'total_remaining_days'
    },
    autoCalcRemainingDays: {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0,
      field: 'auto_calc_remaining_days'
    },
    totalCarryoverDays: {
      type: DataTypes.FLOAT,
      allowNull: false,
      defaultValue: 0,
      field: 'total_carryover_days'
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
    tableName: 'user_details',
    modelName: 'UserDetails',
    version: true,
  });

  return UserDetails;
};