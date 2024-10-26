'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class SystemConfigs extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
    }
  }
  SystemConfigs.init({
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
      allowNull: false,
      field: 'id'
    },
    companyId: {
      type: DataTypes.BIGINT,
      allowNull: false,
      field: 'company_id'
    },
    key: {
      type: DataTypes.STRING(100),
      allowNull: false,
      field: 'key'
    },
    value: {
      type: DataTypes.STRING(10000),
      allowNull: false,
      field: 'value'
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
    tableName: 'system_configs',
    modelName: 'SystemConfigs',
  });

  return SystemConfigs;
};