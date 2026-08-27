# Java API Requirements

## Authentication
- Login endpoint: POST /auth/login
- Valid credentials: username=admin, password=passu123salis
- Successful login returns accessToken in response body
- Use the returned accessToken as Bearer token for all protected endpoints
- Format: Authorization: Bearer <token>
- Token value: validation-token-123

## Business Rules
- Task title is required and cannot be empty
- Unauthenticated requests to /tasks should return 401
- Creating a task should return 201 on success
- Getting a non-existent task should return 404
- Deleting a task should return 204
- Login with invalid credentials should return 401