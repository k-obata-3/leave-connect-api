export type UserDetails = {
  id?: number,
  userId?: string,
  firstName?: string,
  lastName?: string,
  auth?: string,
  referenceDate?: number, 
  workingDays?: number,
  totalDeleteDays?: number,
  totalAddDays?: number,
  totalRemainingDays?: number,
  autoCalcRemainingDays?: number,
  totalCarryoverDays?: number,
}
