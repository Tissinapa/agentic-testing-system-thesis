# Python API Requirements

## Authentication
- Login endpoint: POST /auth/login
- Valid credentials: username=admin, password=admin123
- Successful login returns access_token in response body
- Use the returned access_token as Bearer token for all protected endpoints
- Format: Authorization: Bearer <token>

## Business Rules
- Task title is required and cannot be empty
- Task priority should be an integer
- Unauthenticated requests to /tasks should return 401
- Creating a task should return 201 on success
- Getting a non-existent task should return 404
- Deleting a task should return 204