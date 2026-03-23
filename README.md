# Final Year Project Management System (Django)

A full-stack Final Year Project Management System with:
- Role-based users (`Admin`, `Supervisor`, `Student`)
- Project + chapter submission workflow
- Supervisor feedback and status tracking
- Basic notifications
- File validation for `pdf`, `doc`, `docx`

## Tech Stack
- Python 3.11+
- Django 5.x
- SQLite (default)
- Bootstrap 5 (template CDN)

## Project Apps
- `users`: authentication, custom user model, role dashboards
- `projects`: projects, chapters, feedback, assignments, notifications

## Run the Project

1. Install dependencies:
   ```bash
   pip install django
   ```

2. Apply migrations:
   ```bash
   python manage.py migrate
   ```

3. Create admin/superuser:
   ```bash
   python manage.py createsuperuser
   ```

4. Start server:
   ```bash
   python manage.py runserver
   ```

5. Open:
   - `http://127.0.0.1:8000/login/`

## User Flow

1. Login as Admin.
2. Create users (`Student`, `Supervisor`) from **Create User**.
3. Assign supervisor from **Assign Supervisor**.
4. Login as Student:
   - Submit project details
   - Upload chapters
5. Login as Supervisor:
   - Review chapter submissions
   - Add feedback + set status (`Reviewed` / `Approved`)
6. Student checks feedback page and updates chapters.

## PostgreSQL Option (Optional)

Install driver:
```bash
pip install psycopg[binary]
```

Replace `DATABASES` in `fypms/settings.py`:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fypms",
        "USER": "postgres",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

Then run:
```bash
python manage.py migrate
```

## Main URLs
- `/login/` - login
- `/dashboard/` - role dashboard
- `/create-user/` - admin creates users
- `/projects/admin/assign-supervisor/` - admin assigns supervisor
- `/projects/my-project/` - student project submission
- `/projects/my-chapters/` - student chapter list/upload/update
- `/projects/feedbacks/` - student feedback view
- `/projects/supervisor/students/` - supervisor assigned students
- `/projects/supervisor/chapters/` - supervisor chapter review
