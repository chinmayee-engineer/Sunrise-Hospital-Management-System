"""Demo data initialization (spec sections 11, 22, 45).

Runs once, the first time the database has no patients. Creates
realistic (fictional) demo users, doctors, patients, appointments,
consultations, prescriptions, lab tests, invoices and notifications
so the application looks populated immediately after installation.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from core.database.db import query_one
from core.services import (
    appointment_service, billing_service, consultation_service, doctor_service,
    lab_service, notification_service, patient_service, prescription_service, user_service,
)
from core.services.audit_service import log_action

FIRST_NAMES_M = ["Arjun", "Rohan", "Vikram", "Karthik", "Aditya", "Sanjay", "Rahul", "Manoj",
                  "Suresh", "Anil", "Nikhil", "Deepak", "Ramesh", "Gaurav", "Amit"]
FIRST_NAMES_F = ["Priya", "Ananya", "Sneha", "Divya", "Kavya", "Meera", "Pooja", "Neha",
                  "Shreya", "Lakshmi", "Anjali", "Ritu", "Swati", "Nandini", "Isha"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Nair", "Reddy", "Gupta", "Menon", "Rao", "Pillai",
              "Kulkarni", "Mehta", "Joshi", "Desai", "Bhat", "Chowdhury"]
CITIES = [("Bengaluru", "Karnataka", "560001"), ("Chennai", "Tamil Nadu", "600001"),
          ("Hyderabad", "Telangana", "500001"), ("Pune", "Maharashtra", "411001"),
          ("Mumbai", "Maharashtra", "400001")]
BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
ALLERGY_OPTIONS = ["", "", "", "Penicillin", "Dust", "Peanuts", "Sulfa drugs", "Pollen"]
CONDITION_OPTIONS = ["", "", "", "Hypertension", "Type 2 Diabetes", "Asthma", "Hypothyroidism"]

DOCTORS = [
    dict(full_name="Priya Sharma", gender="Female", specialization="General Medicine",
         department="General Medicine", qualification="MBBS, MD (General Medicine)",
         experience_years=12, consultation_fee=500),
    dict(full_name="Arvind Menon", gender="Male", specialization="Cardiology",
         department="Cardiology", qualification="MBBS, DM (Cardiology)",
         experience_years=18, consultation_fee=900),
    dict(full_name="Kavita Rao", gender="Female", specialization="Dermatology",
         department="Dermatology", qualification="MBBS, MD (Dermatology)",
         experience_years=9, consultation_fee=600),
    dict(full_name="Suresh Nair", gender="Male", specialization="Pediatrics",
         department="Pediatrics", qualification="MBBS, MD (Pediatrics)",
         experience_years=15, consultation_fee=550),
    dict(full_name="Anjali Desai", gender="Female", specialization="Orthopedics",
         department="Orthopedics", qualification="MBBS, MS (Orthopedics)",
         experience_years=11, consultation_fee=700),
    dict(full_name="Ramesh Iyer", gender="Male", specialization="Neurology",
         department="Neurology", qualification="MBBS, DM (Neurology)",
         experience_years=20, consultation_fee=1000),
    dict(full_name="Nandini Bhat", gender="Female", specialization="Gynecology",
         department="Gynecology", qualification="MBBS, MS (Obstetrics & Gynecology)",
         experience_years=14, consultation_fee=650),
    dict(full_name="Manoj Kulkarni", gender="Male", specialization="ENT",
         department="ENT", qualification="MBBS, MS (ENT)",
         experience_years=8, consultation_fee=500),
]

DIAGNOSES = ["Viral Infection", "Upper Respiratory Infection", "Migraine", "Gastritis",
             "Seasonal Allergy", "Mild Hypertension", "Type 2 Diabetes (Follow-up)",
             "Muscle Strain", "Anxiety-related symptoms", "Common Cold"]
SYMPTOMS_LIST = ["Fever, fatigue, headache", "Sore throat, cough", "Nausea, dizziness",
                  "Abdominal pain, bloating", "Sneezing, itchy eyes", "Joint pain, swelling",
                  "Shortness of breath on exertion", "Back pain", "Restlessness, poor sleep"]
MEDICINES = [
    dict(medicine_name="Paracetamol", dosage="500mg", frequency="Twice daily", duration="5 days",
         before_after_food="After food"),
    dict(medicine_name="Amoxicillin", dosage="250mg", frequency="Thrice daily", duration="7 days",
         before_after_food="After food"),
    dict(medicine_name="Cetirizine", dosage="10mg", frequency="Once daily", duration="5 days",
         before_after_food="After food"),
    dict(medicine_name="Omeprazole", dosage="20mg", frequency="Once daily", duration="10 days",
         before_after_food="Before food"),
    dict(medicine_name="Ibuprofen", dosage="400mg", frequency="Twice daily", duration="3 days",
         before_after_food="After food"),
]
LAB_TEST_OPTIONS = [("Blood Test", "Complete Blood Count (CBC)"), ("Blood Test", "Lipid Profile"),
                     ("Urine Test", "Routine Urine Analysis"), ("X-Ray", "Chest X-Ray"),
                     ("ECG", "12-Lead ECG"), ("Blood Test", "Fasting Blood Sugar")]


def _rand_date_within(days_back: int) -> str:
    return (datetime.now() - timedelta(days=random.randint(1, days_back))).strftime("%Y-%m-%d")


def _rand_dob(min_age: int = 1, max_age: int = 85) -> str:
    age = random.randint(min_age, max_age)
    birth_year = datetime.now().year - age
    return f"{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"


def needs_seeding() -> bool:
    return query_one("SELECT COUNT(*) AS c FROM patients")["c"] == 0


def run_seed() -> None:
    if not needs_seeding():
        return

    user_service.ensure_roles()

    # --- Core staff accounts -------------------------------------------------
    admin_id = user_service.create_user("admin", "Admin@123", "System Administrator", "Administrator",
                                         email="admin@sunrisehospital.example")
    reception_id = user_service.create_user("reception", "Reception@123", "Fatima Khan", "Receptionist",
                                              email="reception@sunrisehospital.example")
    nurse_id = user_service.create_user("nurse", "Nurse@123", "Latha Krishnan", "Nurse")
    lab_id = user_service.create_user("labstaff", "Lab@123", "Rajesh Kumar", "LabStaff")
    pharm_id = user_service.create_user("pharmacist", "Pharma@123", "Sunita Agarwal", "Pharmacist")

    # --- Doctors ---------------------------------------------------------------
    doctor_ids = []
    for i, d in enumerate(DOCTORS):
        doctor_id = doctor_service.create_doctor(dict(
            full_name=d["full_name"], gender=d["gender"], date_of_birth=_rand_dob(35, 60),
            phone=f"98{random.randint(10000000, 99999999)}",
            email=f"dr.{d['full_name'].split()[0].lower()}@sunrisehospital.example",
            qualification=d["qualification"], specialization=d["specialization"],
            department=d["department"], experience_years=d["experience_years"],
            consultation_fee=d["consultation_fee"],
            description=f"Dr. {d['full_name']} is a specialist in {d['specialization']} "
                        f"with {d['experience_years']} years of clinical experience.",
            working_days="Mon,Tue,Wed,Thu,Fri" if i % 3 else "Mon,Wed,Fri,Sat",
            start_time="09:00", end_time="17:00", break_start="13:00", break_end="14:00",
            slot_duration_minutes=20,
        ), admin_id, "Administrator")
        doctor_ids.append(doctor_id)
        user_service.create_user(
            f"dr.{d['full_name'].split()[0].lower()}", "Doctor@123", f"Dr. {d['full_name']}", "Doctor",
            email=f"dr.{d['full_name'].split()[0].lower()}@sunrisehospital.example",
            linked_doctor_id=doctor_id,
        )

    # --- Patients ----------------------------------------------------------
    patient_ids = []
    used_names = set()
    for _ in range(28):
        gender = random.choice(["Male", "Female"])
        first = random.choice(FIRST_NAMES_M if gender == "Male" else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        while full_name in used_names:
            full_name = f"{random.choice(FIRST_NAMES_M if gender == 'Male' else FIRST_NAMES_F)} {last}"
        used_names.add(full_name)
        city, state, pin = random.choice(CITIES)
        dob = _rand_dob(4, 82)
        phone = f"9{random.randint(100000000, 999999999)}"
        patient_id = patient_service.create_patient(dict(
            full_name=full_name, date_of_birth=dob, gender=gender, blood_group=random.choice(BLOOD_GROUPS),
            phone=phone, email=f"{first.lower()}.{last.lower()}@example.com",
            address=f"{random.randint(1, 400)}, {random.choice(['Park Street','MG Road','Lake View','Church Street','Ring Road'])}",
            city=city, state=state, pin_code=pin,
            emergency_contact_name=f"{random.choice(FIRST_NAMES_M + FIRST_NAMES_F)} {last}",
            emergency_relationship=random.choice(["Spouse", "Parent", "Sibling", "Child", "Friend"]),
            emergency_phone=f"9{random.randint(100000000, 999999999)}",
            allergies=random.choice(ALLERGY_OPTIONS), existing_conditions=random.choice(CONDITION_OPTIONS),
            previous_surgeries=random.choice(["", "", "Appendectomy (2019)", "Tonsillectomy (2015)"]),
            chronic_conditions=random.choice(CONDITION_OPTIONS),
            medical_history="No significant medical history reported." if random.random() > 0.3 else
                             "Family history of cardiovascular disease.",
            important_notes="", registration_date=_rand_date_within(400),
        ), admin_id, "Administrator")
        patient_ids.append(patient_id)
        user_service.create_user(
            f"patient{patient_id.split('-')[1]}", "Patient@123", full_name, "Patient",
            email=f"{first.lower()}.{last.lower()}@example.com", phone=phone, linked_patient_id=patient_id,
        )

    # --- Historical + upcoming appointments, consultations, prescriptions, labs, billing ---
    today = datetime.now().date()
    for patient_id in patient_ids:
        visit_count = random.randint(1, 4)
        used_slots = set()
        for v in range(visit_count):
            doctor_id = random.choice(doctor_ids)
            is_past = (v < visit_count - 1) or random.random() < 0.6
            if is_past:
                day = _rand_date_within(240)
            else:
                day = (today + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d")
            slot_key = (doctor_id, day)
            if slot_key in used_slots:
                continue
            used_slots.add(slot_key)
            hour = random.randint(9, 16)
            minute = random.choice([0, 20, 40])
            time_str = f"{hour:02d}:{minute:02d}"

            existing = query_one(
                "SELECT 1 FROM appointments WHERE doctor_id=? AND appointment_date=? AND appointment_time=?",
                (doctor_id, day, time_str))
            if existing:
                continue

            from core.database.db import execute, next_numeric_id
            from core.utils.ids import next_id
            appointment_id = next_id("appointment", next_numeric_id("appointments", "appointment_id"))
            token = random.randint(1, 30)
            status = "Completed" if is_past else "Scheduled"
            now_iso = datetime.now().isoformat(timespec="seconds")
            execute(
                """INSERT INTO appointments (appointment_id, patient_id, doctor_id, appointment_date,
                      appointment_time, reason, status, token_number, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (appointment_id, patient_id, doctor_id, day, time_str,
                 random.choice(SYMPTOMS_LIST), status, token, now_iso, now_iso),
            )

            if is_past:
                consultation_id = consultation_service.create_consultation(dict(
                    appointment_id=appointment_id, patient_id=patient_id, doctor_id=doctor_id,
                    consultation_date=day, chief_complaint=random.choice(SYMPTOMS_LIST),
                    symptoms=random.choice(SYMPTOMS_LIST),
                    temperature=round(random.uniform(97.5, 101.5), 1),
                    blood_pressure=f"{random.randint(110,140)}/{random.randint(70,90)}",
                    heart_rate=random.randint(65, 95), respiratory_rate=random.randint(14, 20),
                    oxygen_saturation=round(random.uniform(96, 99.5), 1),
                    weight_kg=round(random.uniform(45, 95), 1), height_cm=round(random.uniform(150, 185), 1),
                    physical_examination="No acute distress noted on examination.",
                    diagnosis=random.choice(DIAGNOSES), treatment="Symptomatic management advised.",
                    doctor_notes="Patient advised to rest and follow up if symptoms persist.",
                    follow_up_date=(datetime.strptime(day, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d"),
                ), admin_id, "Administrator")

                chosen_meds = random.sample(MEDICINES, k=random.randint(1, 3))
                prescription_service.create_prescription(dict(
                    consultation_id=consultation_id, patient_id=patient_id, doctor_id=doctor_id,
                    prescription_date=day, diagnosis=random.choice(DIAGNOSES),
                    symptoms=random.choice(SYMPTOMS_LIST),
                    instructions="Drink plenty of fluids and get adequate rest.",
                    follow_up_date=(datetime.strptime(day, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d"),
                ), chosen_meds, admin_id, "Administrator")

                if random.random() < 0.5:
                    test_type, test_name = random.choice(LAB_TEST_OPTIONS)
                    lab_test_id = lab_service.request_test(dict(
                        patient_id=patient_id, doctor_id=doctor_id, consultation_id=consultation_id,
                        test_type=test_type, test_name=test_name, requested_date=day,
                    ), admin_id, "Administrator")
                    if random.random() < 0.8:
                        lab_service.enter_result(lab_test_id, "Results within normal reference range.",
                                                   actor_user_id=lab_id, actor_role="LabStaff")

                doctor = doctor_service.get_doctor(doctor_id)
                invoice_id = billing_service.create_invoice(
                    patient_id, [dict(description=f"Consultation - {doctor['specialization']}",
                                       category="Consultation", quantity=1, unit_price=doctor["consultation_fee"])],
                    appointment_id=appointment_id, tax=round(doctor["consultation_fee"] * 0.05, 2),
                    actor_user_id=reception_id, actor_role="Receptionist")
                if random.random() < 0.75:
                    invoice = billing_service.get_invoice(invoice_id)
                    billing_service.record_payment(invoice_id, invoice["total"], random.choice(["Cash", "Card", "UPI"]),
                                                     actor_user_id=reception_id, actor_role="Receptionist")

    # --- A couple of sample messages -----------------------------------------
    from core.services import message_service
    if patient_ids and doctor_ids:
        message_service.send_message(patient_ids[0], doctor_ids[0], "patient",
                                       "Hello Doctor, I still have mild headaches. Should I continue the medication?")
        message_service.send_message(patient_ids[0], doctor_ids[0], "doctor",
                                       "Yes, please continue for 2 more days and monitor your temperature.")

    notification_service.create_notification("System", "Welcome to Sunrise Hospital",
                                               "Your account has been created. Explore your dashboard to get started.")

    log_action(admin_id, "Administrator", "Demo Data Seeded", "",
               f"{len(patient_ids)} patients, {len(doctor_ids)} doctors initialized.")
