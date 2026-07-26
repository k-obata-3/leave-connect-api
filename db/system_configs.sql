insert into system_configs(id,company_id,`key`,`value`,created,updated,version) values 
 (1,1,'grantRule','{"sectionMonth": ["6", "18", "30", "42", "54", "66", "78"],"workingDays": [{"day": 1,"grantDays": ["1", "2", "2", "2", "3", "3", "3" ]},{"day": 2,"grantDays": ["3", "4", "4", "5", "6", "6", "7" ]},{"day": 3,"grantDays": ["5", "6", "6", "8", "9", "10", "11" ]},{"day": 4,"grantDays": ["7", "8", "9", "10", "12", "13", "15" ]},{"day": 5,"grantDays": ["10", "11", "12", "14", "16", "18", "20" ]}]}',TIMESTAMP '2024-09-15 00:00:00.000',TIMESTAMP '2024-09-15 00:00:00.000',1)
,(2,1,'approvalGroup','{"groupName": "承認グループA","approver1": "1","approver2": "2","approver3": "4","approver4": "5","approver5": "6"}',TIMESTAMP '2024-10-19 00:00:00.000',TIMESTAMP '2024-10-19 22:04:06.000',1)
,(3,1,'approvalGroup','{"groupName": "承認グループB","approver1": "1","approver2": "2","approver3": "4","approver4": "","approver5": ""}',TIMESTAMP '2024-10-19 00:00:00.000',TIMESTAMP '2024-10-19 22:04:07.000',1)
,(4,1,'approvalGroup','{"groupName":"TEST","approver1":"2","approver2":"3","approver3":"","approver4":"","approver5":""}',TIMESTAMP '2024-10-20 14:04:29.000',TIMESTAMP '2024-10-20 14:04:29.000',1)
;
