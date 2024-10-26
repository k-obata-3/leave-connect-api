type ApplicationType = {
  id: number,
  name: string,
  value: string,
};

const applicationTypes: ApplicationType[] = [
  {
    id: 0,
    name: 'PAID_HOLIDAY',
    value: '年次有給休暇申請',
  },
  {
    id: 1,
    name: 'NORMAL_HOLIDAY',
    value: '休暇申請',
  }
];

const applicationType = {
  getApplicationTypeValueById(id: any) {
    let returnValue = '';
    applicationTypes.forEach((type: any) => {
      if(type.id == id) {
        returnValue = type.value;
      };
    })
    return returnValue;
  },
  getApplicationTypeIdByName(name: any) {
    let returnId = '';
    applicationTypes.forEach((type: any) => {
      if(type.name === name) {
        returnId = type.id;
      };
    })
    return returnId;
  }
}
module.exports = applicationType;
