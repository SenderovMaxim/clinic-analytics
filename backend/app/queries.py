from sqlalchemy import text

# ЗАПРОС 1: Выручка врача
# Цепочка: Транзакция -> Этап плана лечения -> Прием -> Врач
# ЗАПРОС 1: Выручка врача (исправленный)
# Добавлено условие AND t.amount > 0, чтобы исключить возвраты и корректировки
# ЗАПРОС 1: Выручка врача (для тестирования - без фильтра по датам)
# ЗАПРОС 1: Выручка врача (ЧЕРЕЗ ПАЦИЕНТОВ)
# Считаем сумму всех успешных транзакций пациентов, которые ходили к этому врачу
REVENUE_QUERY = text("""
WITH doctor_patients AS (
    SELECT DISTINCT a.patient_id, a.created_by_id as doctor_id
    FROM appointments_appointment a
    WHERE a.created_by_id IS NOT NULL
)
SELECT 
    u.id as doctor_id,
    u.first_name || ' ' || u.last_name as doctor_name,
    COALESCE(SUM(t.amount), 0) as total_revenue
FROM doctor_patients dp
JOIN auth_user u ON dp.doctor_id = u.id
JOIN patients_transaction t ON t.patient_id = dp.patient_id
WHERE t.is_voided = false
  AND t.amount > 0  -- Только приход денег
GROUP BY u.id, u.first_name, u.last_name
ORDER BY total_revenue DESC
""")

# ЗАПРОС 2: Перенаправляемость
# Логика: находим первичный прием врача А, затем ищем любые другие приемы этого пациента у врачей Б, В, Г...
# ЗАПРОС 2: Перенаправляемость (для тестирования - без фильтра по датам)
REFERRAL_QUERY = text("""
WITH primary_visits AS (
    SELECT 
        a.created_by_id as doctor_id, 
        a.patient_id, 
        MIN(a.start_time) as first_visit_time
    FROM appointments_appointment a
    -- WHERE a.start_time >= :start_date AND a.start_time <= :end_date  -- Закомментировано
    GROUP BY a.created_by_id, a.patient_id
),
subsequent_other_doctors AS (
    SELECT DISTINCT pv.doctor_id, pv.patient_id
    FROM primary_visits pv
    JOIN appointments_appointment a2 
      ON a2.patient_id = pv.patient_id
     AND a2.created_by_id != pv.doctor_id
     AND a2.start_time > pv.first_visit_time
)
SELECT 
    pv.doctor_id,
    u.first_name || ' ' || u.last_name as doctor_name,
    COUNT(DISTINCT pv.patient_id) as total_patients,
    COUNT(DISTINCT sod.patient_id) as referred_patients,
    CASE 
        WHEN COUNT(DISTINCT pv.patient_id) > 0 
        THEN ROUND(100.0 * COUNT(DISTINCT sod.patient_id) / COUNT(DISTINCT pv.patient_id), 2)
        ELSE 0 
    END as referral_rate_pct
FROM primary_visits pv
JOIN auth_user u ON pv.doctor_id = u.id
LEFT JOIN subsequent_other_doctors sod ON pv.doctor_id = sod.doctor_id AND pv.patient_id = sod.patient_id
GROUP BY pv.doctor_id, u.first_name, u.last_name
ORDER BY pv.doctor_id
""")