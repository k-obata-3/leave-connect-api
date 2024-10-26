import { UserDetails } from "../types/userDetails";

export type Task = {
  id?: number,
  action?: number,
  sAction?: string,
  type?: string,
  status?: string,
  sStatus?: string,
  comment?: string,
  userName?: string,
  operationDate?: Date,
  UserDetails?: UserDetails,
}
