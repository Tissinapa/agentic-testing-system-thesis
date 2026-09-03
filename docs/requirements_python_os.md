# FastAPI Full Stack Template Requirements

## Authentication
- Login endpoint: POST /api/v1/login/access-token
- Use form data (not JSON): fields are username and password
- Default credentials: username=admin@example.com, password=changethis
- Successful login returns access_token in response body
- Token type: bearer
- Format: Authorization: Bearer <access_token>
- Token value: use the returned access_token from login response

## API Structure
- Base URL: http://localhost
- All API endpoints prefixed with /api/v1
- Items and users endpoints require authentication
- Health check at /api/v1/utils/health-check/ returns boolean true
- Signup may be disabled by default

## Notes
- Login uses form-encoded data not JSON body
- Some endpoints require superuser privileges