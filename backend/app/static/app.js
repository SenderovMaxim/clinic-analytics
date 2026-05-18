let revChart = null;
let refChart = null;

async function loadData() {
    const start = document.getElementById('start').value || '2019-01-01';
    const end = document.getElementById('end').value || '2026-12-31';

    console.log("Загрузка данных...", start, end);

    try {
        const response = await fetch(`/api/analytics?start_date=${start}&end_date=${end}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        console.log("Данные получены:", data);
        renderCharts(data);
        renderTable(data);
    } catch (error) {
        console.error("Ошибка:", error);
        alert("Не удалось загрузить данные. Проверьте консоль (F12).");
    }
}

function renderCharts(data) {
    if (!data.revenue || !data.referrals) return;

    const labels = data.revenue.map(d => d.doctor_name);
    const revenueData = data.revenue.map(d => d.total_revenue);
    const referralData = data.referrals.map(d => d.referral_rate_pct);

    // График выручки
    const ctxRev = document.getElementById('revenueChart');
    if (ctxRev) {
        if (revChart) revChart.destroy();
        revChart = new Chart(ctxRev, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Выручка (₽)',
                    data: revenueData,
                    backgroundColor: '#4f46e5'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // График перенаправляемости
    const ctxRef = document.getElementById('referralChart');
    if (ctxRef) {
        if (refChart) refChart.destroy();
        refChart = new Chart(ctxRef, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    label: '% рефералов',
                    data: referralData,
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}

function renderTable(data) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    if (!data.referrals || data.referrals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">Нет данных за выбранный период</td></tr>';
        return;
    }

    let totalRevenue = 0;
    let totalProcedures = 0;
    let totalPatients = 0;
    let totalReferred = 0;

    data.referrals.forEach((r, i) => {
        const revData = data.revenue ? data.revenue.find(item => item.doctor_id === r.doctor_id) : null;

        const revenue = revData && revData.total_revenue !== undefined ? revData.total_revenue : 0;
        const procedures = revData && revData.total_procedures !== undefined ? revData.total_procedures : 0;

        totalRevenue += revenue;
        totalProcedures += procedures;
        totalPatients += (r.total_patients || 0);
        totalReferred += (r.referred_patients || 0);

        tbody.innerHTML += `
            <tr>
                <td>${r.doctor_name || 'Не указано'}</td>
                <td>${Number(revenue).toLocaleString('ru-RU')}</td>
                <td>${Number(procedures).toLocaleString('ru-RU')}</td>
                <td>${r.total_patients || 0}</td>
                <td>${r.referred_patients || 0}</td>
                <td>${r.referral_rate_pct !== undefined ? r.referral_rate_pct : 0}%</td>
            </tr>
        `;
    });

    tbody.innerHTML += `
        <tr style="font-weight: bold; background-color: #e2e8f0;">
            <td>ИТОГО</td>
            <td>${totalRevenue.toLocaleString('ru-RU')}</td>
            <td>${totalProcedures.toLocaleString('ru-RU')}</td>
            <td>${totalPatients.toLocaleString('ru-RU')}</td>
            <td>${totalReferred.toLocaleString('ru-RU')}</td>
            <td>-</td>
        </tr>
    `;
}

window.onload = loadData;