-- Hospital Management System schema (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS roles (
    role_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name   TEXT UNIQUE NOT NULL,      -- Administrator, Doctor, Receptionist, Nurse, LabStaff, Pharmacist, Patient
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,       -- U-1001
    username       TEXT UNIQUE NOT NULL,
    password_hash  TEXT NOT NULL,
    password_salt  TEXT NOT NULL,
    full_name      TEXT NOT NULL,
    role_id        INTEGER NOT NULL REFERENCES roles(role_id),
    linked_patient_id TEXT REFERENCES patients(patient_id),
    linked_doctor_id  TEXT REFERENCES doctors(doctor_id),
    email          TEXT,
    phone          TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL,
    last_login_at  TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    department_id TEXT PRIMARY KEY,        -- DEPT-101
    name          TEXT UNIQUE NOT NULL,
    description   TEXT
);

CREATE TABLE IF NOT EXISTS patients (
    patient_id      TEXT PRIMARY KEY,      -- P-10001
    full_name       TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,
    gender          TEXT NOT NULL,
    blood_group     TEXT,
    phone           TEXT NOT NULL,
    email           TEXT,
    address         TEXT,
    city            TEXT,
    state           TEXT,
    pin_code        TEXT,
    emergency_contact_name  TEXT,
    emergency_relationship  TEXT,
    emergency_phone         TEXT,
    allergies        TEXT,
    existing_conditions TEXT,
    previous_surgeries  TEXT,
    chronic_conditions  TEXT,
    medical_history      TEXT,
    important_notes  TEXT,
    status           TEXT NOT NULL DEFAULT 'Active',   -- Active / Archived
    registration_date TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id        TEXT PRIMARY KEY,     -- D-1001
    full_name        TEXT NOT NULL,
    gender           TEXT,
    date_of_birth    TEXT,
    phone            TEXT,
    email            TEXT,
    qualification    TEXT,
    specialization   TEXT NOT NULL,
    department_id    TEXT REFERENCES departments(department_id),
    experience_years INTEGER DEFAULT 0,
    consultation_fee REAL DEFAULT 0,
    description      TEXT,
    working_days     TEXT,      -- comma separated: Mon,Tue,Wed
    start_time       TEXT,      -- HH:MM
    end_time         TEXT,      -- HH:MM
    break_start      TEXT,
    break_end        TEXT,
    slot_duration_minutes INTEGER DEFAULT 15,
    is_active        INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS doctor_leaves (
    leave_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id    TEXT NOT NULL REFERENCES doctors(doctor_id),
    leave_date   TEXT NOT NULL,
    reason       TEXT
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id TEXT PRIMARY KEY,        -- A-100001
    patient_id     TEXT NOT NULL REFERENCES patients(patient_id),
    doctor_id      TEXT NOT NULL REFERENCES doctors(doctor_id),
    appointment_date TEXT NOT NULL,         -- YYYY-MM-DD
    appointment_time TEXT NOT NULL,         -- HH:MM
    reason         TEXT,
    status         TEXT NOT NULL DEFAULT 'Scheduled', -- Scheduled/CheckedIn/InConsultation/Completed/Cancelled/NoShow
    token_number   INTEGER,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    UNIQUE(doctor_id, appointment_date, appointment_time)
);

CREATE TABLE IF NOT EXISTS consultations (
    consultation_id TEXT PRIMARY KEY,       -- C-100001
    appointment_id  TEXT REFERENCES appointments(appointment_id),
    patient_id      TEXT NOT NULL REFERENCES patients(patient_id),
    doctor_id       TEXT NOT NULL REFERENCES doctors(doctor_id),
    consultation_date TEXT NOT NULL,
    chief_complaint TEXT,
    symptoms        TEXT,
    temperature     REAL,
    blood_pressure  TEXT,
    heart_rate      INTEGER,
    respiratory_rate INTEGER,
    oxygen_saturation REAL,
    weight_kg       REAL,
    height_cm       REAL,
    bmi             REAL,
    physical_examination TEXT,
    diagnosis       TEXT,
    treatment       TEXT,
    doctor_notes    TEXT,
    follow_up_date  TEXT,
    status          TEXT NOT NULL DEFAULT 'Completed',
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id TEXT PRIMARY KEY,       -- RX-100001
    consultation_id TEXT REFERENCES consultations(consultation_id),
    patient_id      TEXT NOT NULL REFERENCES patients(patient_id),
    doctor_id       TEXT NOT NULL REFERENCES doctors(doctor_id),
    prescription_date TEXT NOT NULL,
    diagnosis       TEXT,
    symptoms        TEXT,
    instructions    TEXT,
    follow_up_date  TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prescription_items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id TEXT NOT NULL REFERENCES prescriptions(prescription_id),
    medicine_name   TEXT NOT NULL,
    dosage          TEXT,
    frequency       TEXT,
    duration        TEXT,
    before_after_food TEXT,
    instructions    TEXT
);

CREATE TABLE IF NOT EXISTS lab_tests (
    lab_test_id     TEXT PRIMARY KEY,       -- LAB-100001
    patient_id      TEXT NOT NULL REFERENCES patients(patient_id),
    doctor_id       TEXT NOT NULL REFERENCES doctors(doctor_id),
    consultation_id TEXT REFERENCES consultations(consultation_id),
    test_type       TEXT NOT NULL,          -- Blood Test / Urine / X-Ray / MRI / CT Scan / Ultrasound / ECG / Other
    test_name       TEXT NOT NULL,
    requested_date  TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Requested', -- Requested/Scheduled/SampleCollected/Processing/Completed/Cancelled
    result_summary  TEXT,
    result_file_path TEXT,
    result_date     TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medical_documents (
    document_id   TEXT PRIMARY KEY,         -- DOC-100001
    patient_id    TEXT NOT NULL REFERENCES patients(patient_id),
    uploaded_by   TEXT,                     -- user_id
    document_type TEXT NOT NULL,            -- Prescription/X-Ray/Scan/Lab Report/Medical Certificate/Discharge Summary/Insurance/Other
    title         TEXT NOT NULL,
    file_path     TEXT NOT NULL,
    is_archived   INTEGER NOT NULL DEFAULT 0,
    uploaded_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id    TEXT PRIMARY KEY,         -- INV-100001
    patient_id    TEXT NOT NULL REFERENCES patients(patient_id),
    appointment_id TEXT REFERENCES appointments(appointment_id),
    invoice_date  TEXT NOT NULL,
    subtotal      REAL NOT NULL DEFAULT 0,
    discount      REAL NOT NULL DEFAULT 0,
    tax           REAL NOT NULL DEFAULT 0,
    total          REAL NOT NULL DEFAULT 0,
    amount_paid    REAL NOT NULL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'Pending', -- Pending/PartiallyPaid/Paid/Cancelled/Refunded
    notes          TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoice_items (
    item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id   TEXT NOT NULL REFERENCES invoices(invoice_id),
    description  TEXT NOT NULL,
    category     TEXT,        -- Consultation/Lab/Diagnostic/Procedure/Medicine/Other
    quantity     REAL NOT NULL DEFAULT 1,
    unit_price   REAL NOT NULL DEFAULT 0,
    line_total   REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id    TEXT PRIMARY KEY,        -- PAY-100001
    invoice_id    TEXT NOT NULL REFERENCES invoices(invoice_id),
    patient_id    TEXT NOT NULL REFERENCES patients(patient_id),
    amount        REAL NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'Cash',  -- Cash/Card/UPI/Insurance/Other
    payment_date  TEXT NOT NULL,
    reference_no  TEXT,
    notes         TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id    TEXT PRIMARY KEY,        -- MSG-100001
    patient_id    TEXT NOT NULL REFERENCES patients(patient_id),
    doctor_id     TEXT NOT NULL REFERENCES doctors(doctor_id),
    sender        TEXT NOT NULL,           -- 'patient' or 'doctor'
    body          TEXT NOT NULL,
    is_read       INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,      -- N-100001
    user_id          TEXT REFERENCES users(user_id),
    patient_id       TEXT REFERENCES patients(patient_id),
    doctor_id        TEXT REFERENCES doctors(doctor_id),
    category         TEXT NOT NULL,        -- Appointment/Prescription/Lab/Payment/Message/System
    title            TEXT NOT NULL,
    body             TEXT,
    is_read          INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT,
    role_name     TEXT,
    action        TEXT NOT NULL,
    related_record TEXT,
    description   TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hospital_settings (
    setting_key   TEXT PRIMARY KEY,
    setting_value TEXT
);

CREATE TABLE IF NOT EXISTS backups (
    backup_id    TEXT PRIMARY KEY,         -- BK-1001
    file_path    TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    created_by   TEXT,
    notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_patients_name  ON patients(full_name);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);
CREATE INDEX IF NOT EXISTS idx_doctors_name   ON doctors(full_name);
CREATE INDEX IF NOT EXISTS idx_doctors_spec   ON doctors(specialization);
CREATE INDEX IF NOT EXISTS idx_appt_date      ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appt_patient   ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appt_doctor    ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_consult_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_rx_patient      ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_patient     ON lab_tests(patient_id);
CREATE INDEX IF NOT EXISTS idx_invoice_patient ON invoices(patient_id);
CREATE INDEX IF NOT EXISTS idx_doc_patient     ON medical_documents(patient_id);
CREATE INDEX IF NOT EXISTS idx_audit_created   ON audit_logs(created_at);
