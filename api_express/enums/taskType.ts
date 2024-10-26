type TaskType = {
  id: number,
  name: string,
  value: string,
};

const taskTypes: TaskType[] = [
  {
    id: 0,
    name: 'APPLICATION',
    value: '申請タスク',
  },
  {
    id: 1,
    name: 'APPROVAL',
    value: '承認タスク',
  }
];

const taskType = {
  getTaskTypeValueById(id: any) {
    let returnValue = '';
    taskTypes.forEach((type: any) => {
      if(type.id == id) {
        returnValue = type.value;
      };
    })
    return returnValue;
  },
  getTaskTypeIdByName(name: any) {
    let returnId = '';
    taskTypes.forEach((type: any) => {
      if(type.name === name) {
        returnId = type.id;
      };
    })
    return returnId;
  }
}
module.exports = taskType;
