# 🏥 Sunrise Hospital Management System

> A professional, offline-first Hospital Management System built with Python and PySide6, providing integrated patient management, doctor management, appointments, consultations, prescriptions, laboratory workflows, billing, medical records, notifications, analytics, and audit logging through dedicated Staff and Patient applications.

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.x-41CD52?style=flat&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=flat&logo=sqlite&logoColor=white)
![ReportLab](https://img.shields.io/badge/ReportLab-4.x-B71C1C?style=flat)
![OpenPyXL](https://img.shields.io/badge/OpenPyXL-3.x-217346?style=flat&logo=microsoftexcel&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat&logo=windows&logoColor=white)

---

## 📌 Overview

**Sunrise Hospital Management System** is a complete desktop-based healthcare management application developed using **Python, PySide6, and SQLite**.

The system is designed to manage the complete hospital workflow from patient registration and appointment scheduling to doctor consultations, prescriptions, laboratory investigations, billing, medical documents, notifications, and patient history.

The project provides **two dedicated desktop applications**:

- 🏥 **Hospital Staff Console**
- 👤 **Patient Portal**

Both applications share the same SQLite database and centralized business-logic layer, ensuring that information remains synchronized across the system.

For example:

```text
Receptionist books appointment
            ↓
      Shared Database
            ↓
Patient sees appointment
            ↓
Doctor conducts consultation
            ↓
Consultation stored in history
            ↓
Prescription / Lab Test
            ↓
Billing & Payment
            ↓
Patient medical timeline updated
