from sqlalchemy import func, and_, case, cast, Date
from .models import Appointment, Schedule, Transaction, User, EmployeeProfile


def get_revenue_data(db, start_date: str, end_date: str):
    doctor_appointments = (
        db.query(
            Schedule.doctor_id.label('doctor_id'),
            Appointment.patient_id.label('patient_id'),
            cast(Appointment.start_time, Date).label('visit_date')
        )
        .join(Schedule, Appointment.schedule_id == Schedule.id)
        .filter(
            Schedule.doctor_id.isnot(None),
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date
        )
        .subquery()
    )

    query = (
        db.query(
            User.id.label('doctor_id'),
            func.coalesce(
                EmployeeProfile.short_name,
                func.concat(User.first_name, ' ', User.last_name)
            ).label('doctor_name'),
            func.sum(Transaction.amount).label('total_revenue'),
            func.count(Transaction.id).label('total_procedures'),
            func.count(doctor_appointments.c.patient_id).label('patient_count')
        )
        .join(doctor_appointments, User.id == doctor_appointments.c.doctor_id)
        .join(
            Transaction,
            and_(
                Transaction.patient_id == doctor_appointments.c.patient_id,
                cast(Transaction.created_at, Date) == doctor_appointments.c.visit_date,
                #Transaction.is_voided == False
                Transaction.amount > 0
            )
        )
        .join(EmployeeProfile, User.id == EmployeeProfile.user_id)
        .group_by(User.id, EmployeeProfile.short_name, User.first_name, User.last_name)
        .order_by(func.sum(Transaction.amount).desc())
    )

    return query.all()


def get_referral_data(db, start_date: str, end_date: str):
    primary_visits = (
        db.query(
            Schedule.doctor_id.label('doctor_id'),
            Appointment.patient_id.label('patient_id'),
            func.min(Appointment.start_time).label('first_visit_time')
        )
        .join(Schedule, Appointment.schedule_id == Schedule.id)
        .filter(
            Schedule.doctor_id.isnot(None),
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date
        )
        .group_by(Schedule.doctor_id, Appointment.patient_id)
        .subquery()
    )

    subsequent_visits = (
        db.query(
            primary_visits.c.doctor_id.label('doctor_id'),
            primary_visits.c.patient_id.label('patient_id')
        )
        .join(
            Appointment,
            Appointment.patient_id == primary_visits.c.patient_id
        )
        .join(Schedule, Appointment.schedule_id == Schedule.id)
        .filter(
            Schedule.doctor_id != primary_visits.c.doctor_id,
            Schedule.doctor_id.isnot(None),
            Appointment.start_time > primary_visits.c.first_visit_time
        )
        .subquery()
    )

    referral_rate_case = case(
        (func.count(primary_visits.c.patient_id) > 0,
         func.round(
             100.0 * func.count(subsequent_visits.c.patient_id) /
             func.nullif(func.count(primary_visits.c.patient_id), 0),
             2
         )),
        else_=0
    )

    query = (
        db.query(
            User.id.label('doctor_id'),
            func.coalesce(
                EmployeeProfile.short_name,
                func.concat(User.first_name, ' ', User.last_name)
            ).label('doctor_name'),
            func.count(primary_visits.c.patient_id).label('total_patients'),
            func.count(subsequent_visits.c.patient_id).label('referred_patients'),
            referral_rate_case.label('referral_rate_pct')
        )
        .join(primary_visits, User.id == primary_visits.c.doctor_id)
        .outerjoin(
            subsequent_visits,
            and_(
                primary_visits.c.doctor_id == subsequent_visits.c.doctor_id,
                primary_visits.c.patient_id == subsequent_visits.c.patient_id
            )
        )
        .outerjoin(EmployeeProfile, User.id == EmployeeProfile.user_id)
        .group_by(User.id, EmployeeProfile.short_name, User.first_name, User.last_name)
        .order_by(func.count(primary_visits.c.patient_id).desc())
    )

    return query.all()