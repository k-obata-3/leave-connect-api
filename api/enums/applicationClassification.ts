type ApplicationClassification = {
  id: number,
  name: string,
  value: string,
};

const applicationClassifications: ApplicationClassification[] = [
  {
    id: 0,
    name: 'ALL_DAYS',
    value: '全日',
  },
  {
    id: 1,
    name: 'HALF_DAYS_AM',
    value: 'AM半休',
  },
  {
    id: 2,
    name: 'HALF_DAYS_PM',
    value: 'PM半休',
  },
  {
    id: 3,
    name: 'TIME',
    value: '時間単位',
  },
];

const applicationClassification = {
  getClassificationValueById(id: any) {
    let returnValue = '';
    applicationClassifications.forEach((type: any) => {
      if(type.id == id) {
        returnValue = type.value;
      };
    })
    return returnValue;
  },
  getClassificationIdByName(name: any) {
    let returnId = '';
    applicationClassifications.forEach((type: any) => {
      if(type.name === name) {
        returnId = type.id;
      };
    })
    return returnId;
  }
}
module.exports = applicationClassification;
