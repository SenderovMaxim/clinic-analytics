from sqlalchemy import func, and_, case, distinct, cast, Date
from .models import Appointment, Schedule, Transaction, User, EmployeeProfile


def get_revenue_data(db, start_date: str, end_date: str):
    """
    Выручка врача: сумма транзакций, привязанных к врачу через ближайший прием пациента.
    Логика: Для каждой транзакции находим прием, который был ближе всего по времени (до или после оплаты).
    Это лучший компромисс между точностью и отсутствием прямых связей.
    """

    # Шаг 1: Соединяем транзакции со всеми приемами этого пациента в периоде отчета
    tx_appt_join = (
        db.query(
            Transaction.id.label('tx_id'),
            Transaction.amount.label('tx_amount'),
            Schedule.doctor_id.label('doctor_id'),
            # Вычисляем абсолютную разницу во времени в секундах между приемом и оплатой
            func.abs(func.extract('epoch', Appointment.start_time - Transaction.created_at)).label('time_diff')
        )
            .join(Appointment, Appointment.patient_id == Transaction.patient_id)
            .join(Schedule, Appointment.schedule_id == Schedule.id)
            .filter(
            Transaction.is_voided == False,
            Transaction.amount > 0,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            # Ограничиваем приемы периодом отчета, чтобы не захватывать старые визиты из прошлого года
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date,
            Schedule.doctor_id.isnot(None)
        )
            .subquery()
    )

    # Шаг 2: Нумеруем приемы для каждой транзакции по близости времени (rn=1 - самый близкий)
    ranked_appts = (
        db.query(
            tx_appt_join.c.tx_id,
            tx_appt_join.c.tx_amount,
            tx_appt_join.c.doctor_id,
            func.row_number().over(
                partition_by=tx_appt_join.c.tx_id,
                order_by=tx_appt_join.c.time_diff.asc()
            ).label('rn')
        )
            .subquery()
    )

    # Шаг 3: Отбираем только самые близкие приемы (rn=1)
    last_appts = (
        db.query(
            ranked_appts.c.tx_id,
            ranked_appts.c.tx_amount,
            ranked_appts.c.doctor_id
        )
            .filter(ranked_appts.c.rn == 1)
            .subquery()
    )

    # Шаг 4: Агрегируем выручку по врачам
    query = (
        db.query(
            User.id.label('doctor_id'),
            func.coalesce(
                EmployeeProfile.short_name,
                func.concat(User.first_name, ' ', User.last_name)
            ).label('doctor_name'),

            func.sum(last_appts.c.tx_amount).label('total_revenue'),
            func.count(last_appts.c.tx_id).label('total_procedures'),
            func.count(distinct(last_appts.c.tx_id)).label('patient_count')
        )
            .join(last_appts, User.id == last_appts.c.doctor_id)
            .outerjoin(EmployeeProfile, User.id == EmployeeProfile.user_id)
            .group_by(User.id, EmployeeProfile.short_name, User.first_name, User.last_name)
            .order_by(func.sum(last_appts.c.tx_amount).desc())
    )

    return query.all()


def get_referral_data(db, start_date: str, end_date: str):
    """
    Перенаправляемость: пациенты, которые после приема у врача А пошли к врачу Б.
    """
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
            .distinct()
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