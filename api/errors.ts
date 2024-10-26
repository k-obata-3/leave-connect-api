export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

export class NotFoundError extends Error {
  constructor(message?: string) {
    super(message);
    this.name = "NotFoundError";
  }
}

export class ServerError extends Error {
  constructor(message?: string) {
    super(message);
    this.name = "ServerError";
  }
}

export class AuthError extends Error {
  constructor(message?: string) {
    super(message);
    this.name = "AuthError";
  }
}