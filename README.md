# Exam Management & Automation System (EMS)

A production-grade exam management platform for colleges and institutes. Built with Django + Tailwind CSS.

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Django 4.2, Django REST Framework   |
| Frontend   | HTML, Tailwind CSS, JavaScript      |
| Database   | SQLite (dev) / PostgreSQL (prod)    |
| Storage    | All content as text in database     |
| Reports    | ReportLab (PDF), OpenPyXL (Excel)   |
| Hosting    | Render                              |

---

## Roles

| Role                  | Access Level                                      |
|-----------------------|---------------------------------------------------|
| **Admin**             | Full system access, manage coordinators            |
| **Exam Coordinator**  | Full exam workflow, master data, scheduling, marks |
| **Subject Coordinator** | Assessment schemes, question papers, CO/BTL mapping |
| **Subject Faculty**   | View duties, enter marks, view assigned analysis   |

---

## Features — Implementation Status

### ✅ Fully Implemented

| #  | Module                   | What's Built                                                    |
|----|--------------------------|----------------------------------------------------------------|
| 1  | **Project Setup**        | Django project, modular app structure, base layout, Render config |
| 2  | **Authentication**       | Login, logout, change password, forgot/reset password, profile  |
| 3  | **Role-Based Access**    | 4-role RBAC, decorators, middleware, role-based dashboards       |
| 4  | **Master Data**          | Programs, Subjects, Divisions, Classrooms — full CRUD + archive |
| 5  | **Exam Management**      | Create, edit, delete, archive exams with status tracking         |
| 6  | **Student CSV Import**   | Upload CSV, preview, validate, detect duplicates, import wizard |
| 7  | **Curriculum Import**    | CSV import for assessment scheme + curriculum mapping            |
| 8  | **Faculty Assignment**   | Subject coordinator & faculty CSV upload, assign/reassign       |
| 9  | **Assessment Scheme**    | Component tree, sub-components, formula builder, validation     |
| 10 | **Exam Scheduling**      | Auto-generate, edit, regenerate, lock schedules                  |
| 11 | **Dashboards**           | Role-based dashboards (Admin, Coordinator, Subject Coord, Faculty) |
| 12 | **Audit Logging**        | Action logging for login, CRUD, password changes                |
| 13 | **Core Infrastructure**  | BaseModel (timestamps, archiving), mixins, template tags, context processors |

### 🔲 Scaffolded (Models/URLs registered, views empty)

| #  | Module                     | Status                        |
|----|----------------------------|-------------------------------|
| 14 | **Seating Arrangement**    | App created, no implementation |
| 15 | **Duty Chart**             | App created, no implementation |
| 16 | **Question Papers**        | App created, no implementation |
| 17 | **Marks Entry**            | App created, no implementation |
| 18 | **Marks Review & Locking** | App created, no implementation |
| 19 | **Result Analysis**        | App created, no implementation |
| 20 | **Reports & Export**       | App created, no implementation |

---

## Project Structure

```
Exam-Management-Automation-System/
├── config/                     # Django project config
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── development.py      # Dev-specific settings
│   │   └── production.py       # Production settings (Render)
│   ├── urls.py                 # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── apps/                       # All Django apps
│   ├── accounts/               # Auth, user model, RBAC
│   ├── core/                   # Base models, audit, mixins, utils
│   ├── dashboard/              # Role-based dashboards
│   ├── master_data/            # Programs, Subjects, Divisions, Classrooms
│   ├── exams/                  # Exam CRUD & status tracking
│   ├── students/               # Student CSV import
│   ├── curriculum/             # Curriculum & assessment scheme import
│   ├── faculty/                # Faculty assignment management
│   ├── assessment/             # Assessment component & formula config
│   ├── scheduling/             # Exam schedule generation
│   ├── seating/                # Seating arrangement (stub)
│   ├── duty_chart/             # Supervision duty chart (stub)
│   ├── question_papers/        # Question paper management (stub)
│   ├── marks/                  # Marks entry (stub)
│   ├── reports/                # Reports & export (stub)
│   └── analysis/               # Result analysis (stub)
├── templates/                  # HTML templates
│   ├── base.html               # Master layout
│   ├── accounts/
│   ├── dashboard/
│   ├── master_data/
│   ├── exams/
│   ├── students/
│   ├── curriculum/
│   ├── faculty/
│   ├── scheduling/
│   ├── assessment/
│   └── components/
├── static/                     # CSS, JS, images
├── requirements.txt
├── manage.py
├── Procfile                    # Render deployment
├── render.yaml                 # Render blueprint
└── .env.example                # Environment template
```

---

## How to Run (Local Development)

### 1. Clone the repo

```bash
git clone https://github.com/YugPatel11/Exam-Management-Automation-System.git
cd Exam-Management-Automation-System
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

```bash
copy .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY` — any random string
- `DEBUG=True`
- Email settings (optional for local dev)

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create superuser (Admin)

```bash
python manage.py createsuperuser
```

> Set the role to `admin` via Django admin at `/admin/` after creation.

### 7. Start dev server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## Key URLs

| URL                       | Purpose                    |
|---------------------------|----------------------------|
| `/`                       | Redirects to login         |
| `/accounts/login/`        | Login page                 |
| `/dashboard/admin/`       | Admin dashboard            |
| `/dashboard/coordinator/` | Exam coordinator dashboard |
| `/master-data/`           | Master data management     |
| `/exams/`                 | Exam management            |
| `/students/`              | Student CSV import         |
| `/curriculum/`            | Curriculum import          |
| `/faculty/`               | Faculty assignments        |
| `/assessment/`            | Assessment scheme config   |
| `/scheduling/`            | Exam scheduling            |
| `/admin/`                 | Django admin panel         |

---

## Production Deployment (Render)

1. Push code to GitHub
2. Connect repo to [Render](https://render.com)
3. Set environment variables from `.env.example` in Render dashboard
4. Render uses `Procfile` and `render.yaml` for auto-deployment
