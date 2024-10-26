type Action = {
  id: number,
  name: string,
  value: string,
};

const actions: Action[] = [
  {
    id: 0,
    name: 'DRAFT',
    value: '下書き',
  },
  {
    id: 1,
    name: 'PANDING',
    value: '承認待ち',
  },
  {
    id: 2,
    name: 'APPROVAL',
    value: '承認',
  },
  {
    id: 3,
    name: 'COMPLETE',
    value: '完了',
  },
  {
    id: 4,
    name: 'REJECT',
    value: '却下',
  },
  {
    id: 5,
    name: 'CANCEL',
    value: '取消',
  },
  {
    id: 9,
    name: 'SYSTEM_CANCEL',
    value: 'システム取消',
  },
];

const action = {
  getActionValueById(id: any) {
    let returnValue = '';
    actions.forEach((type: any) => {
      if(type.id == id) {
        returnValue = type.value;
      };
    })
    return returnValue;
  },
  getActionNameById(id: any) {
    let returnName = '';
    actions.forEach((type: any) => {
      if(type.id == id) {
        returnName = type.name;
      };
    })
    return returnName;
  },
  getActionIdByName(name: any) {
    let returnId = '';
    actions.forEach((type: any) => {
      if(type.name === name) {
        returnId = type.id;
      };
    })
    return returnId;
  }
}
module.exports = action;
