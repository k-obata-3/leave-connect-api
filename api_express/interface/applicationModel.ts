export default interface ApplicationModel {
  id: number
  applicationUserId: number,
  type: number,
  classification: number,
  applicationDate: Date,
  startDate: Date,
  endDate: Date,
  approvalGroupId: number,
}