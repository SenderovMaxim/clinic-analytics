from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Numeric, ForeignKey, Date, cast
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Schedule(Base):
    __tablename__ = 'schedules_schedule'
    id = Column(BigInteger, primary_key=True)
    doctor_id = Column(Integer, ForeignKey('auth_user.id'), nullable=True)

class Appointment(Base):
    __tablename__ = 'appointments_appointment'
    id = Column(BigInteger, primary_key=True)
    schedule_id = Column(BigInteger, ForeignKey('schedules_schedule.id'), nullable=True)
    patient_id = Column(BigInteger, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)

class Transaction(Base):
    __tablename__ = 'patients_transaction'
    id = Column(BigInteger, primary_key=True)
    patient_id = Column(BigInteger, nullable=True)
    amount = Column(Numeric(10, 2), nullable=True)
    is_voided = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    treatment_stage_id = Column(BigInteger, ForeignKey('appointments_treatmentplanstage.id'), nullable=True)

class User(Base):
    __tablename__ = 'auth_user'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)

class EmployeeProfile(Base):
    __tablename__ = 'users_employeeprofile'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey('auth_user.id'), nullable=True)
    short_name = Column(String(500), nullable=True)

class TreatmentPlanStage(Base):
    __tablename__ = 'appointments_treatmentplanstage'
    id = Column(BigInteger, primary_key=True)
    appointment_id = Column(BigInteger, ForeignKey('appointments_appointment.id'))
    is_voided = Column(Boolean, default=False)