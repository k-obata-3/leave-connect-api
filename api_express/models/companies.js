'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class Companies extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
    }
  }
  Companies.init({
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
      allowNull: false,
      field: 'id'
    },
    name: {
      type: DataTypes.STRING(100),
      allowNull: false,
      field: 'name'
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
    tableName: 'companies',
    modelName: 'Companies',
    version: true,
  });

  return Companies;
};