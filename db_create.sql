--------------------------------------------------------------------------------
-- leave_connect_db
--------------------------------------------------------------------------------

-- 会社テーブル
CREATE TABLE companies (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID'
  , name VARCHAR(100) NOT NULL COMMENT '会社名'
  , created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
  , updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
  , version BIGINT DEFAULT 1 NOT NULL COMMENT 'バージョン'
  , PRIMARY KEY (id)
)
  COMMENT='会社';

-- ユーザーテーブル
CREATE TABLE users (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID'
  , company_id BIGINT NOT NULL COMMENT '会社ID'
  , user_id VARCHAR(100) NOT NULL COMMENT 'ユーザーID'
  , password VARCHAR(100) NOT NULL COMMENT 'パスワード'
  , created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
  , updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
  , version BIGINT DEFAULT 1 NOT NULL COMMENT 'バージョン'
  , PRIMARY KEY (id)
  , FOREIGN KEY(company_id) REFERENCES companies(id)
  , UNIQUE uq_user (user_id)
)
  COMMENT='ユーザー';

-- ユーザー詳細テーブル
CREATE TABLE user_details (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID'
  , user_id BIGINT NOT NULL COMMENT 'ユーザーID'
  , first_name VARCHAR(100) NOT NULL COMMENT '名'
  , last_name VARCHAR(100) NOT NULL COMMENT '姓'
  , auth BIGINT DEFAULT 0 NOT NULL COMMENT '権限'
  , reference_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '基準日'
  , working_days FLOAT DEFAULT 0 NOT NULL COMMENT '週労働日数'
  , total_delete_days FLOAT DEFAULT 0 NOT NULL COMMENT '消化日数'
  , total_add_days FLOAT DEFAULT 0 NOT NULL COMMENT '付与日数'
  , total_remaining_days FLOAT DEFAULT 0 NOT NULL COMMENT '残日数'
  , auto_calc_remaining_days FLOAT DEFAULT 0 NOT NULL COMMENT '自動計算残日数'
  , total_carryover_days FLOAT DEFAULT 0 NOT NULL COMMENT '繰越日数'
  , created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
  , updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
  , version BIGINT DEFAULT 1 NOT NULL COMMENT 'バージョン'
  , PRIMARY KEY (id)
  , FOREIGN KEY(user_id) REFERENCES users(`id`)
)
  COMMENT='ユーザー詳細';

-- 申請テーブル
CREATE TABLE applications (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID'
  , application_user_id BIGINT NOT NULL COMMENT '申請ユーザーID'
  , type BIGINT NOT NULL COMMENT '申請タイプ'
  , classification BIGINT NOT NULL COMMENT '区分'
  , application_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申請日時'
  , start_date DATETIME NOT NULL COMMENT '開始日時'
  , end_date DATETIME NOT NULL COMMENT '終了日時'
  , total_time BIGINT NOT NULL COMMENT '合計時間'
  , approval_group_id BIGINT NOT NULL COMMENT '承認グループID'
  , created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
  , updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
  , version BIGINT DEFAULT 1 NOT NULL COMMENT 'バージョン'
  , PRIMARY KEY (id)
)
  COMMENT='申請';

-- タスクテーブル
CREATE TABLE tasks (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID'
  , application_id BIGINT NOT NULL COMMENT '申請ID'
  , operation_user_id BIGINT NOT NULL COMMENT 'ユーザーID'
  , action BIGINT COMMENT '操作'
  , type BIGINT NOT NULL COMMENT '種類'
  , comment VARCHAR(1000) COMMENT 'コメント'
  , status BIGINT NOT NULL COMMENT 'ステータス'
  , operation_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作日時'
  , created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
  , updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
  , version BIGINT DEFAULT 1 NOT NULL COMMENT 'バージョン'
  , PRIMARY KEY (id)
  , FOREIGN KEY(application_id) REFERENCES applications(`id`)
)
  COMMENT='タスク';

-- システム設定テーブル
CREATE TABLE system_configs (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID'
  , company_id BIGINT NOT NULL COMMENT '会社ID'
  , `key` VARCHAR(100) NOT NULL COMMENT 'キー'
  , `value` VARCHAR(10000) NOT NULL COMMENT '値'
  , created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
  , updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
  , version BIGINT DEFAULT 1 NOT NULL COMMENT 'バージョン'
  , PRIMARY KEY (id)
  , FOREIGN KEY(company_id) REFERENCES companies(id)
)
  COMMENT='システム設定';


DROP TABLE tasks;
DROP TABLE applications;
DROP TABLE user_details;
DROP TABLE users;
DROP TABLE system_configs;
DROP TABLE companies;
