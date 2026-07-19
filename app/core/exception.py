class FullProjectException(Exception):
    pass

class NotFoundError(FullProjectException):
    pass

class AlreadyExistsError(FullProjectException):
    pass

class MaximumLimitReachedError(FullProjectException):
    pass

class NotAuthorizedError(FullProjectException):
    pass

class InvalidDateError(FullProjectException):
    pass

class MemberNotInListError(FullProjectException):
    pass

class NotCreatedError(FullProjectException):
    pass

class UpdateFailedError(FullProjectException):
    pass

class MinimumClreanceError(FullProjectException):
    pass

class EnteredWrongPasswordError(FullProjectException):
    pass

class UnauthorizedEntryError(FullProjectException):
    pass

class InvalidTokenError(FullProjectException):
    pass