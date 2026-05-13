from sqlalchemy import text

# ЗАПРОС 1: Выручка врача (БЕЗ ДУБЛИРОВАНИЯ)
# Логика:
# 1. Находим всех пациентов, кто был на приеме в периоде.
# 2. Для каждого пациента определяем его "Главного врача" в этом периоде (у кого больше всего приемов).
# 3. Суммируем ВСЕ транзакции этого пациента и отдаем их Главному врачу.
REVENUE_QUERY = text("""
WITH period_appointments AS (
    -- Все приемы за период с указанием врача
    SELECT 
        a.patient_id,
        ss.doctor_id
    FROM appointments_appointment a
    JOIN schedules_schedule ss ON a.schedule_id = ss.id
    WHERE ss.doctor_id IS NOT NULL
      AND a.start_time >= :start_date 
      AND a.start_time <= :end_date
),
primary_doctor_per_patient AS (
    -- Определяем главного врача для каждого пациента (у кого больше всего приемов)
    SELECT 
        patient_id,
        doctor_id,
        COUNT(*) as visit_count,
        ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY COUNT(*) DESC, doctor_id ASC) as rn
    FROM period_appointments
    GROUP BY patient_id, doctor_id
),
patient_main_doctor AS (
    -- Оставляем только самого частого врача (rn=1)
    SELECT patient_id, doctor_id
    FROM primary_doctor_per_patient
    WHERE rn = 1
),
doctor_revenue AS (
    -- Суммируем транзакции пациентов, закрепляя их за главным врачом
    SELECT 
        pmd.doctor_id,
        SUM(t.amount) as total_sum,
        COUNT(t.id) as total_count
    FROM patient_main_doctor pmd
    JOIN patients_transaction t ON t.patient_id = pmd.patient_id
    WHERE t.is_voided = false AND t.amount > 0
    GROUP BY pmd.doctor_id
),
doctor_stats AS (
    -- Статистика по пациентам и приемам для отображения
    SELECT 
        pa.doctor_id,
        COUNT(DISTINCT pa.patient_id) as unique_patients,
        COUNT(pa.patient_id) as total_visits
    FROM period_appointments pa
    GROUP BY pa.doctor_id
)
SELECT 
    u.id as doctor_id,
    COALESCE(uep.short_name, u.first_name || ' ' || u.last_name) as doctor_name,
    COALESCE(dr.total_sum, 0) as total_revenue,
    COALESCE(dr.total_count, 0) as total_procedures,
    ds.unique_patients as patient_count
FROM doctor_stats ds
JOIN auth_user u ON ds.doctor_id = u.id
LEFT JOIN users_employeeprofile uep ON u.id = uep.user_id
LEFT JOIN doctor_revenue dr ON ds.doctor_id = dr.doctor_id
ORDER BY total_revenue DESC
""")

# ЗАПРОС 2: Перенаправляемость (Оставляем как есть, он корректен)
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