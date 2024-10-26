type TaskStatus = {
  id: number,
  name: string,
  value: string,
};

const taskStatuses: TaskStatus[] = [
  {
    id: 0,
    name: 'NON_ACTIVE',
    value: '無効',
  },
  {
    id: 1,
    name: 'ACTIVE',
    value: '進行中',
  },
  {
    id: 2,
    name: 'HISTORY',
    value: '履歴',
  },
  
  {
    id: 3,
    name: 'CLOSED',
    value: '処理済',
  }
];

const taskStatus = {
  getTaskStatusValueById(id: any) {
    let returnValue = '';
    taskStatuses.forEach((type: any) => {
      if(type.id == id) {
        returnValue = type.value;
      };
    })
    return returnValue;
  },
  getTaskStatusIdByName(name: any) {
    let returnId = '';
    taskStatuses.forEach((type: any) => {
      if(type.name === name) {
        returnId = type.id;
      };
    })
    return returnId;
  }
}
module.exports = taskStatus;
