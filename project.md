# Project.md — Exam Management & Automation System

## Project Goal

Build a full exam management and automation system for colleges and institutes.

This is a **real product**, not only an MVP. It should be stable, easy to use, scalable, and ready for long-term use.

The system must support:

* role-based login and access
* master data management
* student and curriculum CSV import
* exam creation and scheduling
* question paper management
* seating arrangement generation
* supervision duty chart generation
* marks entry and review
* result analysis dashboards
* reports and exports
* audit logs and notifications

## Tech Stack

Use these technologies only:

### Frontend

* HTML
* Tailwind CSS
* JavaScript if needed for interactivity

### Backend

* Django
* Django REST Framework

### Database

* Use Django’s default database for now
* Keep the data model ready so it can move to PostgreSQL later if needed

### File Storage

* Store all PDF files in Google Drive
* Store file links and metadata in the database
* Do not store PDFs directly in the database

### Hosting

* Deploy backend on Render
* Deploy frontend in a way that works well with Render

## Product Vision

The system should work like a complete academic ERP for exams.

It should not feel like a small demo app.
It should feel like software that an institute can actually use.

That means:

* clean workflows
* strong validation
* role-based screens
* proper error handling
* reusable code
* responsive UI
* export features
* dashboard analytics
* safe data handling

## Main Roles

The system must support these roles:

### 1. Admin

* create and manage exam coordinator accounts
* manage permissions
* view all reports and institute-wide analytics

### 2. Exam Coordinator

* full control over exam workflow
* manage master data
* create exams
* upload data files
* assign subject coordinators
* assign subject faculties
* generate exam schedules
* generate seating plans
* generate duty charts
* allocate marks entry work
* review and lock marks
* view result analysis
* generate reports

### 3. Subject Coordinator

* manage assessment scheme
* create question papers
* assign CO and BTL mapping
* view analysis for assigned subjects

### 4. Subject Faculty

* view assigned duties
* enter marks
* upload marks CSV
* view analysis for assigned subjects and divisions

## Phase 1 — Project Setup and Core Structure

### Goal

Create the base of the system in a clean and organized way.

### Work to do

* set up Django project
* set up HTML + Tailwind frontend structure
* create app structure for modules
* create base layout
* create authentication flow
* create role-based routing
* set up database models
* set up Google Drive integration structure for PDFs
* set up Render-ready project structure

### Output

* working login system
* base dashboard shell
* project structure ready for all modules
* clean folder structure

### Important Notes

* keep code reusable
* keep views and templates separated properly
* keep APIs clean
* do not hardcode logic in templates

## Phase 2 — Authentication and Access Control

### Goal

Build secure login and role-based access.

### Features

* login
* logout
* change password
* forgot password
* role-based access control
* route protection by role

### Rules

* each role must only see its own data
* admin must have full access
* subject coordinator and faculty must only see assigned data
* exam coordinator must see all academic operations

### Output

* secure login system
* protected dashboards
* permission-based menu and page access

## Phase 3 — Master Data Management

### Goal

Create the core academic master data.

### Managed by

* Exam Coordinator

### Entities

* Programs

  * program name
  * program code
* Subjects

  * subject code
  * subject name
* Divisions

  * program
  * semester
  * division
* Classrooms

  * classroom number
  * capacity

### Output

* add, edit, delete, archive actions
* search and filter support
* table-based UI

## Phase 4 — Exam Management

### Goal

Allow exam coordinators to create and manage exams.

### Fields

* academic year
* exam name
* exam type

  * Internal 1
  * Internal 2
  * Continuous Evaluation
  * Other
* programs
* start date
* end date

### Features

* create exam
* edit exam
* delete exam
* archive exam

### Output

* exam list page
* exam detail page
* exam status tracking

## Phase 5 — Student CSV Import

### Goal

Import student data from ERP export files.

### CSV Columns

* RollNo
* EnrollmentNo
* StudentName
* ProgramName
* Semester
* DivisionCode
* LabBatchNo
* Gender
* StudentDisplayNo
* AdmissionApplicationNo
* PhoneStudent1
* PhoneStudent2
* Email

### Features

* upload CSV
* preview data
* validate records
* detect duplicates
* import to database

### Output

* import wizard
* validation report
* error list for bad rows

## Phase 6 — Curriculum and Examination Scheme Import

### Goal

Import curriculum data to support exam planning and marks structure.

### CSV Fields

* Course Code
* Course Title
* Program
* Semester
* Theory CE
* Theory ESE
* Practical CE
* Practical ESE
* Tutorial CE
* Tutorial ESE

### Purpose

* assessment structure setup
* exam schedule generation
* marks entry generation

### Output

* import screen
* preview screen
* scheme validation

## Phase 7 — Faculty Assignment

### Goal

Link subjects with coordinators and faculty members.

### Subject Coordinator Upload

* subject code
* subject name
* subject coordinator

### Subject Faculty Upload

* subject code
* subject name
* division
* faculty

### Important Rule

A faculty can be both subject coordinator and subject faculty for the same subject.

### Output

* assignment import
* assignment list
* update and reassign options

## Phase 8 — Assessment Scheme Configuration

### Goal

Let subject coordinators design assessment components.

### Features

* create components
* create sub-components
* configure formulas

### Example

* Theory CE = 40
* Internal 1 = 30
* Internal 2 = 30
* FE = 10
* Formula for CE Theory based on internal marks

### Validation Rule

The sum of child components must equal the parent component marks.

### Output

* dynamic form builder
* component tree view
* formula validation

## Phase 9 — Exam Schedule Generation

### Goal

Create schedules automatically for theory exams.

### Rule

Generate schedule only for subjects where:

* Theory ESE > 0

Do not schedule subjects with:

* Theory ESE = 0

### Features

* auto generate schedule
* edit schedule
* regenerate schedule
* lock schedule

### Output

* subject-wise schedule
* program-wise schedule
* date-wise schedule

## Phase 10 — Question Paper Management

### Goal

Allow subject coordinators to create question papers in the system.

### Auto Fetched Data

* subject
* program
* semester
* division
* exam date
* exam time
* maximum marks

### For Each Question

* question text
* marks
* CO mapping
* BTL mapping

### Output

* question paper form
* PDF generation
* CO mapping report
* BTL mapping report

### Storage Rule

* final PDFs must be stored in Google Drive
* database should only keep the file link, name, type, and metadata

## Phase 11 — Seating Arrangement Generation

### Goal

Generate room-wise seating plans automatically.

### Inputs

* student list
* classroom capacity
* exam schedule

### Features

* auto generate seating
* edit seating
* regenerate seating
* lock seating plan

### Output

* room-wise seating
* program-wise seating
* date-wise seating

## Phase 12 — Supervision Duty Chart

### Goal

Generate faculty supervision duties for each exam session.

### Inputs

* faculty list
* seating arrangement
* exam schedule

### Features

* auto generate duty chart
* workload balancing
* edit duty
* swap duty
* regenerate duty chart
* lock duty chart

### Output

* faculty-wise duty
* room-wise duty
* session-wise duty
* faculty dashboard duties view

## Phase 13 — Marks Entry Allocation

### Goal

Assign marks entry tasks to the right faculty automatically.

### Logic

Tasks should be created based on:

* subject faculty
* subject
* division
* semester

### Output

* marks entry tasks in faculty dashboard
* task status tracking
* assigned work list

## Phase 14 — Marks Entry

### Goal

Let faculty enter marks safely and quickly.

### Methods

* dynamic web form
* CSV upload

### Form Rules

The form must be generated from the assessment scheme.

### Example

For theory CE:

* Internal 1

  * Q1 to Q6
* Internal 2

  * Q1 to Q6
* FE

For practical CE:

* Performance
* Viva
* Journal
* Attendance

### System Calculations

* Internal 1 total
* Internal 2 total
* CE total
* Practical total
* ESE total
* grand total

### Features

* save draft
* submit marks

## Phase 15 — Marks Review and Locking

### Goal

Allow exam coordinators to review marks before final use.

### Features

* view marks
* edit marks
* unlock marks
* reopen submission
* final lock marks

### Output

* review dashboard
* correction flow
* lock status tracking

## Phase 16 — Result Analysis Dashboard

### Goal

Show useful analytics for all roles.

### Analysis Types

* program-wise
* division-wise
* subject-wise
* faculty-wise
* component-wise
* CO-wise
* BTL-wise

### Visuals

* bar charts
* pie charts
* line charts
* CO attainment graphs
* BTL attainment graphs
* program comparison charts
* division comparison charts
* subject performance charts

### Drill Down

* Program → Division → Subject → Student

### Visibility Rules

* Admin: all data
* Exam Coordinator: all data
* Subject Coordinator: only assigned subjects
* Subject Faculty: only assigned subjects and divisions

## Phase 17 — Reports and Export

### Goal

Generate professional reports for printing and sharing.

### Reports

* exam schedule report
* question paper report
* seating arrangement report
* duty chart report
* marks report
* program-wise analysis report
* division-wise analysis report
* subject-wise analysis report
* faculty-wise analysis report
* component-wise analysis report
* CO-wise analysis report
* BTL-wise analysis report

### Export Formats

* PDF
* Excel

### Output

* downloadable reports
* Google Drive PDF storage
* report history

## Phase 18 — Dashboards

### Goal

Create clear dashboards for every role.

### Admin Dashboard

Cards:

* total exams
* total students
* total programs
* total subjects
* total faculties
* total exam coordinators

### Exam Coordinator Dashboard

Cards:

* active exams
* pending question papers
* generated schedules
* generated seating plans
* generated duty charts
* pending marks entries
* analysis available

Quick actions:

* create exam
* generate schedule
* generate seating
* generate duty chart
* allocate marks
* view analysis

### Subject Coordinator Dashboard

Cards:

* assigned subjects
* pending assessment schemes
* pending question papers
* CO coverage status
* BTL coverage status

### Subject Faculty Dashboard

Cards:

* assigned subjects
* assigned divisions
* pending marks entry tasks
* upcoming duties
* submitted marks

## UI Requirements

The interface must look modern and professional.

### Must Have

* responsive design
* sidebar navigation
* data tables with filters
* advanced search
* charts and analytics
* CSV import wizard
* PDF export
* Excel export
* role-based menus
* dark mode support
* audit logs
* notifications
* professional academic ERP styling

## Backend Rules

* use Django models properly
* keep business logic in services or helpers where possible
* keep views clean
* validate all uploaded files
* protect all routes
* log important actions
* do not trust client-side data
* use clear API endpoints
* keep file upload handling separate
* store PDFs in Google Drive only through backend logic

## Database Plan

For now, use the default Django database.

Store:

* users
* roles
* programs
* subjects
* divisions
* classrooms
* exams
* students
* curriculum records
* faculty assignments
* assessment schemes
* schedules
* seating plans
* duty charts
* marks
* analysis data
* report metadata
* file links
* audit logs

## Google Drive PDF Storage Plan

All generated PDFs should go to Google Drive.

Store in database:

* file name
* file type
* Google Drive file ID
* file link
* created time
* related module name
* created by user

Do not store the full PDF inside the database.

## API Plan

Create APIs for all major modules:

* authentication
* master data
* student import
* curriculum import
* faculty assignment
* exam management
* schedule generation
* question paper management
* seating arrangement
* duty chart
* marks entry
* marks review
* analysis dashboard
* reports and exports

## Development Order

The work should be done in this order:

1. project setup
2. authentication
3. master data
4. exam management
5. CSV imports
6. faculty assignment
7. assessment scheme
8. schedule generation
9. question paper management
10. seating arrangement
11. duty chart
12. marks entry
13. marks review
14. dashboards
15. reports
16. polishing and testing
17. deployment on Render

## Quality Rules

The final product should be:

* reliable
* clean
* secure
* easy to use
* mobile responsive
* fast enough for daily use
* ready for real institute work
* easy to maintain

## Final Deliverables

The completed project should include:

* working frontend
* working Django backend
* database models
* APIs
* admin panel
* role dashboards
* CSV import system
* Google Drive PDF storage
* report exports
* charts and analysis
* deployable Render setup
* clean code and proper documentation

## Final Instruction to Developer

Build this as a full academic product, not a demo.
Focus on proper architecture, clean UI, strong validation, and complete workflows for every role and module.
