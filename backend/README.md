# Colohouse Backend (Django REST API)

Django + Django REST Framework + JWT (SimpleJWT) + PostgreSQL.

## What is done (Sprint 1, part 1)

- Sign up with email + password
- Log in with JWT (access + refresh tokens)
- Refresh an expired access token
- Get the logged-in user
- Users visible in the Django admin

Coming next: profile fields (phone, university, campus, picture), lifestyle preferences, delete account.

## Project structure

```
backend/
├── manage.py
├── requirements.txt
├── Colohouse/        # the Django project (settings.py, urls.py)
└── accounts/         # the app: User model, serializers, views, urls, tests
```

## Run the backend on your PC

**1. Install packages (once)**
```powershell
cd backend
python -m venv my_env
my_env\Scripts\activate
pip install -r requirements.txt
```

**2. Create the PostgreSQL user and database (once)**

PostgreSQL must be installed. Run this and enter your `postgres` password:
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -c "CREATE USER colohouse WITH PASSWORD 'colohouse' CREATEDB;" -c "CREATE DATABASE colohouse OWNER colohouse;"
```
(Or in pgAdmin: create role `colohouse` / password `colohouse` with "Create databases", then a database `colohouse` owned by it.)

**3. Create the tables and start the server**
```powershell
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
```

Run the tests with `python manage.py test accounts`.

## Base URL for the Flutter app

| Where the app runs | Base URL |
|---|---|
| Android emulator | `http://10.0.2.2:8000` |
| Real phone (same Wi-Fi) | `http://<PC IP>:8000`, start the server with `python manage.py runserver 0.0.0.0:8000` and add the IP to `ALLOWED_HOSTS` in `Colohouse/settings.py` |
| Chrome (`flutter run -d chrome`) | Not supported yet (CORS is not enabled), use the emulator |

## API

All requests and responses are JSON. Send the header `Content-Type: application/json`.

### Sign up
`POST /api/auth/register/`
```json
{ "email": "student@colohouse.com", "first_name": "Student", "last_name": "Test", "password": "StrongPass123!" }
```
- `201` → `{ "id": 1, "email": "student@colohouse.com", "first_name": "Student", "last_name": "Test" }`
- `400` → errors per field, show them under the inputs:
  `{ "email": ["user with this email already exists."], "password": ["This password is too short..."] }`

### Log in
`POST /api/auth/login/`
```json
{ "email": "student@colohouse.com", "password": "StrongPass123!" }
```
- `200` → `{ "access": "<token>", "refresh": "<token>" }`
- `401` → `{ "detail": "No active account found with the given credentials" }`

### Logged-in user
`GET /api/auth/me/` with header `Authorization: Bearer <access>`
- `200` → `{ "id": 1, "email": "...", "first_name": "...", "last_name": "..." }`
- `401` → token missing, invalid or expired

### Refresh the access token
`POST /api/auth/token/refresh/`
```json
{ "refresh": "<refresh token>" }
```
- `200` → `{ "access": "<new token>" }`
- `401` → refresh token expired, the user must log in again

**Token lifetimes:** access = 30 minutes, refresh = 7 days.

## How the app should use it

1. **Sign up** → on `201`, call login with the same email/password.
2. **Log in** → save `access` and `refresh` (e.g. `flutter_secure_storage`).
3. **App start** → call `/api/auth/me/`:
   - `200` → go to home
   - `401` → call `/api/auth/token/refresh/`, save the new `access`, retry; if that fails → login screen
4. **Log out** → delete the saved tokens.

## Dart example (`http` package)

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

const baseUrl = 'http://10.0.2.2:8000';

Future<Map<String, dynamic>?> login(String email, String password) async {
  final res = await http.post(
    Uri.parse('$baseUrl/api/auth/login/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'email': email, 'password': password}),
  );
  if (res.statusCode == 200) {
    return jsonDecode(res.body); // {"access": "...", "refresh": "..."}
  }
  return null;
}

Future<http.Response> getMe(String access) {
  return http.get(
    Uri.parse('$baseUrl/api/auth/me/'),
    headers: {'Authorization': 'Bearer $access'},
  );
}
```

You can also test every endpoint in the browser (open the URL, DRF shows a form) or in Postman (for `/me/`: Authorization → Bearer Token).
