
# 🏥 Sunrise Hospital Management System

> A professional, offline-first Hospital Management System built with Python and PySide6, providing integrated patient management, doctor management, appointments, consultations, prescriptions, laboratory workflows, billing, medical records, notifications, analytics, and audit logging through dedicated Staff and Patient applications.

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.x-41CD52?style=flat&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=flat&logo=sqlite&logoColor=white)
![ReportLab](https://img.shields.io/badge/ReportLab-PDF-B71C1C?style=flat)
![OpenPyXL](https://img.shields.io/badge/OpenPyXL-Excel-217346?style=flat&logo=microsoftexcel&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat&logo=windows&logoColor=white)

---

## 📌 Overview

**Sunrise Hospital Management System** is a complete desktop-based healthcare management application developed using **Python, PySide6, and SQLite**.

The system is designed to manage the complete hospital workflow from patient registration and appointment scheduling to doctor consultations, prescriptions, laboratory investigations, billing, medical documents, notifications, and patient history.

The project provides two dedicated desktop applications:

- 🏥 **Hospital Staff Console**
- 👤 **Patient Portal**

Both applications share the same SQLite database and centralized business-logic layer, ensuring that information remains synchronized across the system.

### Core Hospital Workflow

```text
Patient Registration
        ↓
Doctor Selection
        ↓
Appointment Booking
        ↓
Queue / Check-In
        ↓
Doctor Consultation
        ↓
Diagnosis & Treatment
        ↓
Prescription / Laboratory Test
        ↓
Test Results
        ↓
Billing & Payment
        ↓
Medical History
        ↓
Follow-Up
````

---

# ✨ Key Features

## 🔐 Authentication & Role-Based Access

The application includes authentication and role-based access control.

Supported roles include:

| Role               | Main Responsibilities                                   |
| ------------------ | ------------------------------------------------------- |
| 👑 Administrator   | System administration and overall management            |
| 👨‍⚕️ Doctor       | Consultations, prescriptions, patients and appointments |
| 🧑‍💼 Receptionist | Patient registration and appointment management         |
| 👩‍⚕️ Nurse        | Patient and clinical workflow support                   |
| 🧪 Lab Staff       | Laboratory requests and test results                    |
| 💊 Pharmacist      | Prescription and medication-related workflows           |
| 👤 Patient         | Patient self-service portal                             |

The authentication layer includes password handling, user sessions, role validation, and account status management.

---

# 🧑‍🤝‍🧑 Patient Management

The patient module provides centralized patient records.

### Features

* New patient registration
* Patient ID generation
* Duplicate patient detection
* Patient search
* Patient profile management
* Contact information
* Emergency contact information
* Blood group
* Allergies
* Existing medical conditions
* Previous surgeries
* Chronic conditions
* Medical history
* Patient status
* Important notes
* Medical timeline
* Patient self-registration

Patient information is shared between the Staff Console and Patient Portal.

---

# 👨‍⚕️ Doctor Management

Hospital staff can manage doctor profiles and scheduling information.

### Doctor Information

* Doctor name
* Specialization
* Qualification
* Department
* Experience
* Consultation fee
* Working days
* Working hours
* Break schedules
* Appointment duration
* Doctor availability
* Leave management
* Active/inactive status

---

# 📅 Appointment Management

The appointment module provides a complete scheduling workflow.

### Features

* Appointment booking
* Patient selection
* Doctor selection
* Appointment date
* Appointment time
* Appointment reason
* Slot availability
* Double-booking prevention
* Appointment status
* Appointment history
* Patient check-in
* Token generation
* Appointment cancellation
* No-show handling

### Appointment Lifecycle

```text
Scheduled
    ↓
Checked In
    ↓
In Consultation
    ↓
Completed
```

Additional states:

```text
Cancelled
No Show
```

---

# 🎫 Queue & Token Management

The system includes a dedicated queue-management module.

### Features

* Token generation
* Patient queue
* Appointment status
* Check-in tracking
* Queue progression
* Consultation status
* Current queue information

This provides staff with a structured way to manage patient flow.

---

# 🩺 Consultation Management

Doctors can create detailed consultation records for every patient visit.

### Clinical Information

* Chief complaint
* Symptoms
* Temperature
* Blood pressure
* Heart rate
* Respiratory rate
* Oxygen saturation
* Weight
* Height
* BMI
* Physical examination
* Diagnosis
* Treatment
* Doctor notes
* Follow-up date

## Previous Visit Support

When a doctor starts a new consultation, the system can provide a summary of the patient's previous visit information.

Completed consultations become part of the patient's permanent medical history.

---

# 💊 Digital Prescription Management

Doctors can create structured digital prescriptions.

### Prescription Features

* Multiple medicines
* Medicine name
* Dosage
* Frequency
* Duration
* Before/after food instructions
* Medicine-specific instructions
* General instructions
* Diagnosis
* Follow-up date
* Additional notes
* PDF prescription generation

### Prescription Workflow

```text
Consultation
      ↓
Diagnosis
      ↓
Prescription
      ↓
Medicines
      ↓
PDF Prescription
```

---

# 🧪 Laboratory Management

The laboratory module manages diagnostic test requests and results.

### Laboratory Workflow

```text
Test Requested
      ↓
Scheduled
      ↓
Sample Collected
      ↓
Processing
      ↓
Completed
      ↓
Result Available
```

### Supported Diagnostic Categories

* Blood tests
* Urine tests
* X-Ray
* MRI
* CT Scan
* Ultrasound
* ECG
* Other diagnostic tests

The system can maintain:

* Test requests
* Test status
* Results
* Result summaries
* Result dates
* Notes
* Associated documents

---

# 📄 Medical Documents

Medical documents can be associated with individual patient records.

Supported document categories include:

* Prescriptions
* Laboratory reports
* X-Ray reports
* Scan reports
* Medical certificates
* Other medical documents

Generated files are organized into dedicated directories.

```text
documents/
├── certificates/
├── prescriptions/
├── lab_reports/
├── scans/
└── other/
```

---

# 💳 Billing & Payment Management

The billing system provides invoice and payment management.

### Features

* Invoice generation
* Invoice items
* Consultation charges
* Laboratory charges
* Diagnostic charges
* Procedure charges
* Medicine charges
* Discounts
* Taxes
* Payment tracking
* Partial payments
* Full payments
* Payment references
* Refund/cancellation states
* PDF invoices
* PDF receipts

### Payment Methods

* Cash
* Card
* UPI
* Insurance
* Other

---

# 💬 Doctor–Patient Messaging

The system provides an internal communication mechanism between doctors and patients.

### Features

* Patient-to-doctor messages
* Doctor-to-patient messages
* Message history
* Read/unread status
* Message timestamps

This provides a centralized communication channel within the application.

---

# 🔔 Notifications

The notification system provides updates for important events.

Examples include:

* Appointments
* Prescriptions
* Laboratory updates
* Payments
* Messages
* System events

Notifications support read/unread tracking.

---

# 📊 Dashboard & Analytics

The Staff Console includes dashboard and analytics functionality.

The analytics system can help monitor hospital activity and generate structured reports.

### Excel Export

Analytics and report data can be exported using **OpenPyXL**.

---

# 📑 PDF Reports

The application uses **ReportLab** for PDF generation.

Generated documents can include:

* Prescriptions
* Invoices
* Receipts
* Medical reports
* Summary reports

Generated reports are organized into dedicated folders.

```text
reports/
├── invoices/
├── receipts/
└── summaries/
```

---

# 📝 Audit Logging

Important system activities can be recorded using the audit module.

Audit records can contain:

* User
* Role
* Action
* Related record
* Description
* Timestamp

This provides traceability for important operations performed within the application.

---

# 💾 Backup & Restore

The project includes database backup and restore functionality.

Backup files are stored separately from the application source code.

```text
backups/
```

The system maintains dedicated directories for:

```text
data/
documents/
reports/
backups/
exports/
logs/
```

---

# 🖥️ Hospital Staff Console

The Hospital Staff Console provides centralized access to hospital operations.

### Available Modules

* 📊 Dashboard
* 🧑‍🤝‍🧑 Patients
* 👨‍⚕️ Doctors
* 📅 Appointments
* 🎫 Queue
* 🩺 Consultations
* 💊 Prescriptions
* 🧪 Laboratory
* 💳 Billing
* 📄 Documents
* 💬 Messages
* 🔔 Notifications
* 📈 Reports
* 📊 Analytics
* 📝 Audit
* ⚙️ Settings

---

# 👤 Patient Portal

The Patient Portal provides a dedicated self-service interface.

### Available Modules

* 📊 Dashboard
* 👤 Profile
* 👨‍⚕️ Find Doctor
* 📅 Appointments
* 📜 Appointment History
* 🩺 Medical History
* 💊 Prescriptions
* 🧪 Laboratory
* 📄 Documents
* 💳 Billing
* 💬 Messages
* 🚨 Emergency Information
* 🔔 Notifications

Patients can also register themselves through the portal.

---

# 🔄 Shared Data Architecture

One of the major design features of the project is the shared architecture between the Staff Console and Patient Portal.

Both applications use the same database and centralized service layer.

```text
                    ┌──────────────────────┐
                    │   Hospital Staff     │
                    │       Console        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Shared Service     │
                    │       Layer          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   SQLite Database    │
                    └──────────┬───────────┘
                               ▲
                               │
                    ┌──────────┴───────────┐
                    │    Patient Portal    │
                    └──────────────────────┘
```

### Example

```text
Receptionist
     │
     │ Books appointment
     ▼
SQLite Database
     ▲
     │
     │ Appointment becomes available
     │
Patient Portal
     │
     ▼
Patient views appointment
```

This approach prevents the Staff Console and Patient Portal from maintaining separate copies of important hospital data.

---

# 🏗️ Application Architecture

The application follows a modular architecture separating:

* User interface
* Application views
* Business logic
* Service layer
* Security
* Database operations
* Reporting
* Utilities

### Architecture

```text
┌──────────────────────────────────────┐
│          PySide6 GUI Layer           │
├──────────────────────────────────────┤
│       Application / View Layer       │
├──────────────────────────────────────┤
│          Service Layer               │
│                                      │
│ Patients • Doctors • Appointments    │
│ Consultations • Prescriptions        │
│ Laboratory • Billing • Documents     │
│ Messaging • Notifications            │
│ Analytics • Audit • Backup           │
├──────────────────────────────────────┤
│       Security / Utility Layer       │
├──────────────────────────────────────┤
│            SQLite Database            │
└──────────────────────────────────────┘
```

---

# 📁 Project Structure

```text
HospitalManagementSystem/
│
├── core/
│   ├── database/
│   │   ├── db.py
│   │   └── schema.sql
│   │
│   ├── security/
│   │
│   ├── services/
│   │   ├── patient_service.py
│   │   ├── doctor_service.py
│   │   ├── appointment_service.py
│   │   ├── consultation_service.py
│   │   ├── prescription_service.py
│   │   ├── lab_service.py
│   │   ├── billing_service.py
│   │   ├── document_service.py
│   │   ├── message_service.py
│   │   ├── notification_service.py
│   │   ├── analytics_service.py
│   │   ├── audit_service.py
│   │   ├── backup_service.py
│   │   └── user_service.py
│   │
│   ├── reports/
│   ├── seed/
│   ├── utils/
│   └── theme.py
│
├── hospital_app/
│   ├── main.py
│   ├── login_window.py
│   ├── main_window.py
│   ├── dialogs/
│   └── views/
│
├── patient_app/
│   ├── main.py
│   ├── login_window.py
│   ├── main_window.py
│   └── views/
│
├── shared_ui/
│
├── data/
├── documents/
├── reports/
├── backups/
├── exports/
├── logs/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 🛠️ Technology Stack

| Technology      | Purpose                          |
| --------------- | -------------------------------- |
| **Python**      | Core application development     |
| **PySide6**     | Desktop graphical user interface |
| **SQLite**      | Local relational database        |
| **SQL**         | Database schema and queries      |
| **ReportLab**   | PDF generation                   |
| **OpenPyXL**    | Excel generation and export      |
| **QSS**         | Application styling              |
| **PyInstaller** | Windows executable packaging     |
| **Git**         | Version control                  |
| **GitHub**      | Project hosting                  |

---

# 📋 Requirements

Recommended environment:

```text
Python 3.12+
Windows 10 / 11
```

Main dependencies include:

```text
PySide6
ReportLab
OpenPyXL
```

All required packages are listed in:

```text
requirements.txt
```

> Python 3.12 or 3.13 is recommended for the best compatibility with the PySide6 ecosystem.

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Sunrise-Hospital-Management-System.git
```

Navigate into the project:

```bash
cd Sunrise-Hospital-Management-System
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Application

## 🏥 Hospital Staff Console

```bash
python hospital_app/main.py
```

## 👤 Patient Portal

```bash
python patient_app/main.py
```

On first launch, the application initializes the local SQLite database and required application directories.

---

# 🗄️ Database

The application uses **SQLite** as its local relational database.

The database is created automatically during the first application launch.

The database schema is maintained in:

```text
core/database/schema.sql
```

The project does not require an external database server for normal offline operation.

---

# 🌱 Demo Data

The application includes demonstration data for development and testing.

The seeded environment contains:

* Multiple patient records
* Multiple doctor records
* Appointments
* Consultation records
* Prescription history
* Laboratory records
* Billing records
* Related hospital workflow data

This allows the system to be explored immediately after installation.

---

# 🔑 Demo Credentials

> ⚠️ These credentials are for development and demonstration purposes only.

## Staff Console

| Username     | Password        | Role             |
| ------------ | --------------- | ---------------- |
| `admin`      | `Admin@123`     | Administrator    |
| `reception`  | `Reception@123` | Receptionist     |
| `nurse`      | `Nurse@123`     | Nurse            |
| `labstaff`   | `Lab@123`       | Laboratory Staff |
| `pharmacist` | `Pharma@123`    | Pharmacist       |

### Doctor Accounts

```text
dr.priya
dr.arvind
dr.kavita
dr.suresh
dr.anjali
dr.ramesh
dr.nandini
dr.manoj
```

Doctor password:

```text
Doctor@123
```

---

## Patient Portal

Seeded patient accounts follow the format:

```text
patient<numeric-id>
```

Example:

```text
Username: patient10001
Password: Patient@123
```

Patients can also create accounts through the registration functionality.

> ⚠️ Never use demonstration credentials for real patient information or production deployment.

---

# 📦 Windows Executable

The application can be packaged as a Windows executable using **PyInstaller**.

Install PyInstaller:

```bash
pip install pyinstaller
```

### Staff Console

```bash
pyinstaller --name "Sunrise Hospital Staff" --onedir hospital_app/main.py
```

### Patient Portal

```bash
pyinstaller --name "Sunrise Hospital Patient Portal" --onedir patient_app/main.py
```

The generated applications can be distributed as Windows desktop applications.

---

# 🔐 Security & Privacy

The application includes several application-level security mechanisms:

* Role-based access control
* Password hashing
* User authentication
* Session management
* Account status management
* Audit logging
* Database constraints
* Duplicate detection
* Appointment conflict prevention
* Input validation

### Production Considerations

For real-world healthcare deployment, additional security controls would be required, including:

* Encryption at rest
* Secure secrets management
* Strong authentication policies
* Two-factor authentication
* Secure document storage
* Network security
* HTTPS where applicable
* Detailed access auditing
* Data retention policies
* Disaster recovery
* Backup encryption
* Security testing
* Regulatory compliance

---

# 🔄 Complete Hospital Workflow

```text
┌─────────────────────┐
│ Patient Registration│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Doctor Selection    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Appointment Booking │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Queue / Check-In    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Doctor Consultation │
└───────┬─────┬───────┘
        │     │
        ↓     ↓
 Prescription  Laboratory
        │        │
        │        ↓
        │    Test Results
        │        │
        └────┬───┘
             ↓
       ┌────────────┐
       │   Billing  │
       └─────┬──────┘
             ↓
       Medical History
             ↓
          Follow-Up
```

---

# 🎯 Project Objectives

The project was designed around the following objectives:

### Centralized Patient Management

Maintain structured patient information in one centralized system.

### Connected Hospital Operations

Connect registration, appointments, consultations, prescriptions, laboratory services, documents, and billing.

### Data Synchronization

Allow the Staff Console and Patient Portal to work with the same underlying information.

### Offline-First Operation

Provide a local hospital-management solution without requiring a cloud service or external database server.

### Modular Architecture

Separate GUI, business logic, services, database operations, reporting, security, and utilities.

### Practical Workflow

Create a complete end-to-end hospital workflow rather than a collection of disconnected screens.

---

# 📊 What This Project Demonstrates

This project demonstrates practical experience with:

* Python programming
* Object-oriented programming
* PySide6 / Qt
* Desktop application development
* SQLite database design
* SQL
* CRUD operations
* Authentication
* Role-based authorization
* Session management
* Data validation
* Patient management
* Doctor management
* Appointment scheduling
* Queue management
* Consultation workflows
* Prescription management
* Laboratory workflows
* Billing systems
* PDF generation
* Excel generation
* File management
* Database backup and restore
* Audit logging
* Modular architecture
* UI/UX development
* Windows application packaging
* Git and GitHub

---

# 🧪 Testing & Extensibility

The modular architecture makes the application suitable for automated testing.

Potential test areas include:

* Authentication
* User permissions
* Patient registration
* Duplicate patient detection
* Appointment scheduling
* Double-booking prevention
* Consultation creation
* Prescription generation
* Laboratory workflow
* Billing calculations
* Database operations
* Backup and restore
* Report generation

The service-oriented architecture also allows additional modules to be introduced without redesigning the entire application.

---

# 🔮 Future Enhancements

Potential future improvements include:

* [ ] Automated unit testing
* [ ] Automated integration testing
* [ ] Two-factor authentication
* [ ] Email notifications
* [ ] SMS notifications
* [ ] Pharmacy inventory management
* [ ] Advanced analytics
* [ ] Advanced reporting
* [ ] Calendar integration
* [ ] Multi-hospital support
* [ ] Cloud synchronization
* [ ] Mobile patient application
* [ ] Flask web edition
* [ ] PostgreSQL edition
* [ ] Advanced permission management
* [ ] Background task processing
* [ ] Enhanced document security

---

# 📸 Screenshots

Screenshots can be added to showcase the application interface.

Recommended screenshots:

```text
screenshots/
├── login.png
├── staff-dashboard.png
├── patient-management.png
├── doctor-management.png
├── appointments.png
├── queue.png
├── consultation.png
├── prescriptions.png
├── laboratory.png
├── billing.png
├── patient-portal.png
└── medical-history.png
```

Example:

```markdown
![Staff Dashboard](screenshots/staff-dashboard.png)
```

---

# 📁 Application Data

Generated application data is organized into dedicated directories:

```text
data/
documents/
reports/
backups/
exports/
logs/
```

Keeping generated files separate from source-code modules makes the application easier to maintain and back up.

---

# ⚠️ Disclaimer

This project is intended for:

* Educational purposes
* Software-development practice
* Portfolio presentation
* Demonstration
* Local testing

It is **not intended to replace a certified hospital information system or production healthcare platform** without appropriate security assessment, clinical validation, privacy controls, regulatory compliance, professional testing, and deployment safeguards.

Do not store real patient information in the demonstration environment.

---

# 👨‍💻 Developer

## Designed & Developed by **Chinmayee**

Built with:

**Python • PySide6 • SQLite • ReportLab • OpenPyXL**

Designed with a focus on:

**Modular Architecture • Data Consistency • Usability • Offline-First Operation • End-to-End Hospital Workflow**

---

# ⭐ Support the Project

If you find this project useful or interesting:

⭐ **Star the repository**

🍴 **Fork the repository**

🐛 **Report bugs**

💡 **Suggest improvements**

🤝 **Contribute**

---

# 📜 License

This project is intended for educational and portfolio purposes.

If you plan to distribute or modify the project publicly, add an appropriate open-source license such as the **MIT License**.

---

<div align="center">

# 🏥 Sunrise Hospital Management System

### A Complete Desktop Healthcare Management Solution

**Python • PySide6 • SQLite • ReportLab • OpenPyXL**

**Designed & Developed by Chinmayee**

</div>
```
