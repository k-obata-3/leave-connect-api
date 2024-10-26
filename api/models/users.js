'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class Users extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
      Users.hasOne(models.UserDetails, {
        sourceKey: 'id',
        foreignKey: 'userId',
        as: 'UserDetails',
      });
    }
  }
  Users.init({
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
    userId: {
      type: DataTypes.STRING(100),
      allowNull: false,
      unique: true,
      field: 'user_id'
    },
    password: {
      type: DataTypes.STRING(100),
      allowNull: false,
      field: 'password'
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
    tableName: 'users',
    modelName: 'Users',
    version: true,
  });

  return Users;
};