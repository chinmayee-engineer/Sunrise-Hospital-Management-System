# 🏥 Sunrise Hospital Management System

A local, offline-first Hospital Management System with two desktop
applications built on PySide6 and SQLite:

- **`hospital_app/`** — staff console (Administrator, Doctor, Receptionist,
  Nurse, Lab Staff, Pharmacist)
- **`patient_app/`** — patient self-service portal

Both applications share one SQLite database (`data/hospital.db`) and one
business-logic layer (`core/`), so data entered in one app is immediately
visible in the other (e.g. a receptionist books an appointment → the patient
sees it instantly in their portal; a doctor completes a consultation → the
patient's medical timeline updates immediately).

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python hospital_app/main.py     # staff console
python patient_app/main.py      # patient portal
```

The first run creates `data/hospital.db`, the `documents/`, `reports/`,
`backups/`, `exports/` and `logs/` folders, and seeds ~28 demo patients,
8 demo doctors, and several months of appointment/consultation/prescription/
lab/billing history so the app is immediately explorable.

### Demo logins

**Staff app** (`hospital_app`):
| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123` | Administrator |
| `reception` | `Reception@123` | Receptionist |
| `nurse` | `Nurse@123` | Nurse |
| `labstaff` | `Lab@123` | Lab Staff |
| `pharmacist` | `Pharma@123` | Pharmacist |
| `dr.priya`, `dr.arvind`, `dr.kavita`, `dr.suresh`, `dr.anjali`, `dr.ramesh`, `dr.nandini`, `dr.manoj` | `Doctor@123` | Doctor |

**Patient app** (`patient_app`): any seeded patient has a login
`patient<numeric-id>` (e.g. `patient10001`) / `Patient@123`. New patients
can also self-register from the login screen.

## Project structure

```
HospitalManagementSystem/
├── core/                    # shared business logic & data layer
│   ├── database/            # SQLite connection + schema.sql
│   ├── security/            # password hashing, session
│   ├── services/            # one module per domain (patients, doctors,
│   │                         appointments, consultations, prescriptions,
│   │                         lab, billing, documents, messaging,
│   │                         notifications, analytics, audit, backup...)
│   ├── reports/             # PDF (reportlab) + Excel (openpyxl) generation
│   ├── seed/                # first-run demo data
│   ├── utils/                # paths, ID generation, validators
│   └── theme.py              # shared QSS design system
├── hospital_app/            # staff desktop app (PySide6)
│   ├── views/                # one file per sidebar section
│   └── *_dialog.py           # add/edit/booking/prescription dialogs
├── patient_app/              # patient desktop app (PySide6)
│   └── views/
├── shared_ui/                 # reusable themed widgets (cards, badges,
│                                toasts, empty states) used by both apps
├── data/                      # hospital.db (created on first run)
├── documents/, reports/, backups/, exports/, logs/
```

All paths are resolved relative to the project root at runtime
(`core/utils/paths.py`), so the folder can be moved or packaged into a
Windows `.exe` (e.g. with PyInstaller) without code changes.

## What's implemented

Authentication & role-based access (Administrator/Doctor/Receptionist/
Nurse/LabStaff/Pharmacist/Patient) · patient registration with duplicate
detection · doctor management & scheduling · appointment booking with
real slot availability and double-booking prevention · token/queue system
· consultations with automatic "previous visit" summary and permanent
history · digital prescriptions (multi-medicine) with PDF export · lab
test workflow (request → status → result) · medical document upload ·
billing/invoicing/payments with PDF invoices & receipts · doctor↔patient
messaging · notifications · analytics dashboard + Excel export · audit
log · manual database backup/restore · patient self-registration & profile
editing · medical timeline.

## Packaging as Windows .exe

Each app can be frozen independently, e.g. with PyInstaller:

```bash
pyinstaller --name "Sunrise Hospital Staff" --onedir hospital_app/main.py
pyinstaller --name "Sunrise Hospital Patient Portal" --onedir patient_app/main.py
```

Because `core/utils/paths.py` resolves `data/`, `documents/`, `reports/`,
etc. relative to the executable's own folder when frozen, copy those
folders alongside the built `.exe` (or let the app create them on first
run) rather than trying to write inside the PyInstaller temp extraction
directory.

## Notes on scope

This is a genuinely functional, working implementation of the core
patient → appointment → consultation → prescription → lab → billing
workflow end-to-end, covering the great majority of the original spec.
A handful of the more exotic asks (animated UI transitions, background
worker threads with progress bars for exports, granular per-field audit
diffs, exhaustive automated test suite) were simplified in the interest
of shipping something you can actually run and rely on rather than a
much larger surface with placeholder pages. The architecture (one
service module per domain, clean separation from the GUI) makes it
straightforward to extend.
