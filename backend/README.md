# Colohouse Backend (Django REST API)

Django + Django REST Framework + JWT (SimpleJWT) + PostgreSQL.

## What is done (Sprint 1)

- Sign up, log in with JWT, refresh the token
- Profile: name, phone, bio, profile picture, university, field of study, campus
- Lifestyle & housing preferences: budget, room type, move-in date, distance to campus, sleep schedule, noise tolerance, cleanliness, smoking, "looking for a room"
- Notification settings
- Delete account
- List of campuses (for a dropdown)
- Everything manageable in the Django admin (`/admin`)

## Project structure

```
backend/
├── manage.py
├── requirements.txt
├── Colohouse/        # the Django project (settings.py, urls.py)
└── accounts/         # the app: User, Campus, RoommateProfile + serializers, views, urls, tests
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
python manage.py createsuperuser   # for /admin
python manage.py runserver
```

**After every `git pull`:** run `pip install -r requirements.txt` and `python manage.py migrate` again.

**Campuses** are added by an admin: open `http://127.0.0.1:8000/admin` → Campuses → Add. Add a few so the app's campus dropdown has data.

Run the tests with `python manage.py test accounts`.

## Base URL for the Flutter app

| Where the app runs | Base URL |
|---|---|
| Android emulator | `http://10.0.2.2:8000` |
| Real phone (same Wi-Fi) | `http://<PC IP>:8000`, start the server with `python manage.py runserver 0.0.0.0:8000` and add the IP to `ALLOWED_HOSTS` in `Colohouse/settings.py` |
| Chrome (`flutter run -d chrome`) | Not supported yet (CORS is not enabled), use the emulator |

## API

Requests and responses are JSON (`Content-Type: application/json`), except the picture upload (multipart).
Every endpoint marked 🔒 needs the header `Authorization: Bearer <access>`, otherwise it returns `401`.
A `400` always returns the errors per field, e.g. `{ "phone": ["Enter a valid phone number."] }`: show them under the inputs.

| Method | URL | What it does |
|---|---|---|
| POST | `/api/auth/register/` | Sign up |
| POST | `/api/auth/login/` | Log in → tokens |
| POST | `/api/auth/token/refresh/` | New access token |
| GET 🔒 | `/api/auth/me/` | My profile |
| PATCH 🔒 | `/api/auth/me/` | Edit my profile / upload picture / notification settings |
| DELETE 🔒 | `/api/auth/me/` | Delete my account |
| GET 🔒 | `/api/auth/me/preferences/` | My lifestyle & housing preferences |
| PATCH 🔒 | `/api/auth/me/preferences/` | Edit my preferences |
| GET | `/api/campuses/` | List of campuses |

### Sign up
`POST /api/auth/register/`
```json
{ "email": "student@colohouse.com", "first_name": "Student", "last_name": "Test", "password": "StrongPass123!" }
```
- `201` → `{ "id": 1, "email": "student@colohouse.com", "first_name": "Student", "last_name": "Test" }`
- `400` → e.g. `{ "email": ["user with this email already exists."], "password": ["This password is too short..."] }`

### Log in
`POST /api/auth/login/`
```json
{ "email": "student@colohouse.com", "password": "StrongPass123!" }
```
- `200` → `{ "access": "<token>", "refresh": "<token>" }`
- `401` → `{ "detail": "No active account found with the given credentials" }`

### Refresh the access token
`POST /api/auth/token/refresh/` with `{ "refresh": "<refresh token>" }`
- `200` → `{ "access": "<new token>" }`
- `401` → refresh token expired, the user must log in again

**Token lifetimes:** access = 30 minutes, refresh = 7 days.

### My profile 🔒
`GET /api/auth/me/` → `200`
```json
{
  "id": 1,
  "email": "student@colohouse.com",
  "first_name": "Student",
  "last_name": "Test",
  "phone": "+21612345678",
  "profile_picture": "http://10.0.2.2:8000/media/profile_pictures/avatar.png",
  "bio": "Calm student, likes cooking.",
  "university": "Test University",
  "field_of_study": "Computer Science",
  "campus": { "id": 1, "name": "Main Campus", "university": "Test University", "address": "Main street", "latitude": 36.8, "longitude": 10.18 },
  "push_enabled": true,
  "notify_requests": true,
  "notify_messages": true,
  "date_joined": "2026-10-14T15:49:13Z"
}
```
Empty values come back as `""` (text) or `null` (`profile_picture`, `campus`).

### Edit my profile 🔒
`PATCH /api/auth/me/`: send **only the fields you change**:
```json
{ "phone": "+21612345678", "bio": "...", "university": "...", "field_of_study": "...", "campus_id": 1 }
```
- `campus_id`: the `id` from `/api/campuses/` (send `null` to remove it). The response returns the full `campus` object.
- `phone`: digits only, optional `+` at the start, 8–15 digits.
- `email` cannot be changed.
- Notification settings use the same endpoint: `{ "push_enabled": false, "notify_requests": true, "notify_messages": false }`
- Returns `200` with the full updated profile.

### Upload a profile picture 🔒
`PATCH /api/auth/me/` as **multipart/form-data** with a file field `profile_picture` (an image, max 5 MB).
Returns `200`, and `profile_picture` is a full URL you can show with `Image.network(...)`.
To remove the picture: `PATCH` JSON `{ "profile_picture": null }`.

### Delete my account 🔒
`DELETE /api/auth/me/` → `204`. The user and their preferences are deleted. Then delete the saved tokens and go to the login screen.

### My preferences 🔒
`GET /api/auth/me/preferences/` → `200` (the first time, everything is empty)
```json
{
  "budget": 450,
  "preferred_room_type": "private",
  "move_in_date": "2026-11-01",
  "max_distance_to_campus": 3.5,
  "sleep_schedule": "late",
  "noise_tolerance": 2,
  "cleanliness": 5,
  "smoker": false,
  "accepts_smokers": false,
  "looking_for_room": true,
  "updated_at": "2026-10-14T15:49:14Z"
}
```
`PATCH /api/auth/me/preferences/`: send only the fields you change. Allowed values:

| Field | Values |
|---|---|
| `budget` | whole number per month, e.g. `450` (or `null`) |
| `preferred_room_type` | `"private"`, `"shared"`, `"studio"`, or `""` = no preference |
| `move_in_date` | `"YYYY-MM-DD"` (or `null`) |
| `max_distance_to_campus` | km, e.g. `3.5` (or `null`) |
| `sleep_schedule` | `"early"` (early bird), `"normal"`, `"late"` (night owl), or `""` |
| `noise_tolerance` | `1`–`5` (1 = needs quiet, 5 = noise is fine) |
| `cleanliness` | `1`–`5` (1 = relaxed, 5 = very tidy) |
| `smoker` | `true` / `false` (do I smoke) |
| `accepts_smokers` | `true` / `false` (OK to live with a smoker) |
| `looking_for_room` | `true` / `false` (show me as looking for a room) |

### Campuses
`GET /api/campuses/` (no token needed) → `200`
```json
[ { "id": 1, "name": "Main Campus", "university": "Test University", "address": "Main street", "latitude": 36.8, "longitude": 10.18 } ]
```

## How the app should use it

1. **Sign up** → on `201`, call login with the same email/password.
2. **Log in** → save `access` and `refresh` (e.g. `flutter_secure_storage`).
3. **After the first login** → profile setup screens: personal & study info (`PATCH /me/`, campus dropdown from `/api/campuses/`), picture, then lifestyle (`PATCH /me/preferences/`).
4. **App start** → call `/api/auth/me/`:
   - `200` → go to home
   - `401` → call `/api/auth/token/refresh/`, save the new `access`, retry; if that fails → login screen
5. **Settings screen** → notification switches (`PATCH /me/`), log out, delete account.
6. **Log out** → delete the saved tokens.

## Dart examples (`http` package)

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

Future<http.Response> updateProfile(String access, Map<String, dynamic> changes) {
  return http.patch(
    Uri.parse('$baseUrl/api/auth/me/'),
    headers: {'Authorization': 'Bearer $access', 'Content-Type': 'application/json'},
    body: jsonEncode(changes), // e.g. {"phone": "+21612345678", "campus_id": 1}
  );
}

Future<http.StreamedResponse> uploadPicture(String access, String filePath) async {
  final request = http.MultipartRequest('PATCH', Uri.parse('$baseUrl/api/auth/me/'))
    ..headers['Authorization'] = 'Bearer $access'
    ..files.add(await http.MultipartFile.fromPath('profile_picture', filePath));
  return request.send();
}
```

You can also test every endpoint in the browser (open the URL, DRF shows a form) or in Postman (Authorization → Bearer Token).
