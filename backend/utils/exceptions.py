class AppError(Exception):
    status_code = 500
    error = "Internal Server Error"
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ValidationError(AppError): status_code, error = 422, "Validation Error"
class AuthenticationError(AppError): status_code, error = 401, "Unauthorized"
class AuthorizationError(AppError): status_code, error = 403, "Forbidden"
class ResourceNotFoundError(AppError): status_code, error = 404, "Not Found"
class DuplicateRecordError(AppError): status_code, error = 409, "Conflict"
class DatabaseError(AppError): status_code, error = 500, "Database Error"
class FileUploadError(AppError): status_code, error = 400, "File Upload Error"
class BusinessLogicError(AppError): status_code, error = 400, "Business Logic Error"
class InternalServerError(AppError): status_code, error = 500, "Internal Server Error"
