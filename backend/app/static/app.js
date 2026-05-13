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
    const labels = data.revenue.map(d => d.doctor_name);
    const revenueData = data.revenue.map(d => d.total_revenue);
    const referralData = data.referrals.map(d => d.referral_rate_pct);

    // График выручки
    const ctxRev = document.getElementById('revenueChart');
    if (ctxRev) {
        if (revChart) revChart.destroy();
        revChart = new Chart(ctxRev, {
            type: 'bar',
            data: {  // <--- ДОБАВЛЕНО КЛЮЧЕВОЕ СЛОВО data:
                labels: labels,
                datasets: [{
                    label: 'Выручка (₽)',
                    data: revenueData, // <--- ДОБАВЛЕНО КЛЮЧЕВОЕ СЛОВО data:
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
            data: {  // <--- ДОБАВЛЕНО КЛЮЧЕВОЕ СЛОВО data:
                labels: labels,
                datasets: [{
                    label: '% рефералов',
                    data: referralData, // <--- ДОБАВЛЕНО КЛЮЧЕВОЕ СЛОВО data:
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

    if (data.referrals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">Нет данных</td></tr>';
        return;
    }

    data.referrals.forEach((r, i) => {
        const rev = data.revenue.find(item => item.doctor_id === r.doctor_id)?.total_revenue || 0;
        tbody.innerHTML += `
            <tr>
                <td>${r.doctor_name}</td>
                <td>${rev.toLocaleString('ru-RU')}</td>
                <td>${r.total_patients}</td>
                <td>${r.referred_patients}</td>
                <td>${r.referral_rate_pct}%</td>
            </tr>
        `;
    });
}

window.onload = loadData;