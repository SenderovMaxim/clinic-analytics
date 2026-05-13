from sqlalchemy import text

# ЗАПРОС 1: Выручка врача (Через расписание)
REVENUE_QUERY = text("""
WITH doctor_patients AS (
    -- Находим пациентов через расписание, а не через created_by_id
    SELECT DISTINCT 
        ss.doctor_id as doctor_id,
        a.patient_id
    FROM appointments_appointment a
    JOIN schedules_schedule ss ON a.schedule_id = ss.id
    WHERE ss.doctor_id IS NOT NULL
      AND a.start_time >= :start_date 
      AND a.start_time <= :end_date
)
SELECT 
    u.id as doctor_id,
    COALESCE(uep.short_name, u.first_name || ' ' || u.last_name) as doctor_name,
    COALESCE(SUM(t.amount), 0) as total_revenue,
    COUNT(t.id) as total_procedures
FROM doctor_patients dp
JOIN auth_user u ON dp.doctor_id = u.id
LEFT JOIN users_employeeprofile uep ON u.id = uep.user_id
LEFT JOIN patients_transaction t ON t.patient_id = dp.patient_id 
    AND t.is_voided = false 
    AND t.amount > 0
GROUP BY u.id, uep.short_name, u.first_name, u.last_name
ORDER BY total_revenue DESC
""")

# ЗАПРОС 2: Перенаправляемость (Также через расписание)
REFERRAL_QUERY = text("""
WITH primary_visits AS (
    SELECT 
        ss.doctor_id as doctor_id, 
        a.patient_id, 
        MIN(a.start_time) as first_visit_time
    FROM appointments_appointment a
    JOIN schedules_schedule ss ON a.schedule_id = ss.id
    WHERE ss.doctor_id IS NOT NULL
      AND a.start_time >= :start_date AND a.start_time <= :end_date
    GROUP BY ss.doctor_id, a.patient_id
),
subsequent_other_doctors AS (
    SELECT DISTINCT pv.doctor_id, pv.patient_id
    FROM primary_visits pv
    JOIN appointments_appointment a2 
      ON a2.patient_id = pv.patient_id
    JOIN schedules_schedule ss2 ON a2.schedule_id = ss2.id
     AND ss2.doctor_id != pv.doctor_id
     AND ss2.doctor_id IS NOT NULL
     AND a2.start_time > pv.first_visit_time
)
SELECT 
    u.id as doctor_id,
    COALESCE(uep.short_name, u.first_name || ' ' || u.last_name) as doctor_name,
    COUNT(DISTINCT pv.patient_id) as total_patients,
    COUNT(DISTINCT sod.patient_id) as referred_patients,
    CASE 
        WHEN COUNT(DISTINCT pv.patient_id) > 0 
        THEN ROUND(100.0 * COUNT(DISTINCT sod.patient_id) / COUNT(DISTINCT pv.patient_id), 2)
        ELSE 0 
    END as referral_rate_pct
FROM primary_visits pv
JOIN auth_user u ON pv.doctor_id = u.id
LEFT JOIN users_employeeprofile uep ON u.id = uep.user_id
LEFT JOIN subsequent_other_doctors sod ON pv.doctor_id = sod.doctor_id AND pv.patient_id = sod.patient_id
GROUP BY u.id, uep.short_name, u.first_name, u.last_name
ORDER BY total_patients DESC
""")