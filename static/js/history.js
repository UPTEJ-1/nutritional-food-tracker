(function () {
    const dataElement = document.getElementById('history-chart-data');
    if (!dataElement) {
        return;
    }

    const payload = JSON.parse(dataElement.textContent);
    const chartData = payload.chart_data || [];
    const todayTotals = payload.today_totals || {};
    const calorieGoal = payload.calorie_goal;
    const proteinGoal = payload.protein_goal;
    const macroGoals = payload.macro_goals || {};

    const sortedDays = chartData.slice().reverse();
    const labels = sortedDays.map((day) => {
        const parts = day.date.split('-').map(Number);
        const dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
        return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    const calorieSeries = sortedDays.map((day) => day.calories);
    const proteinSeries = sortedDays.map((day) => day.protein);

    const tickStyle = { font: { size: 13 } };

    const calorieCanvas = document.getElementById('calorieChart');
    if (calorieCanvas) {
        new Chart(calorieCanvas.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Daily Calories',
                        data: calorieSeries,
                        borderColor: '#52B788',
                        backgroundColor: 'rgba(82, 183, 136, 0.12)',
                        yAxisID: 'yCalories',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4,
                    },
                    {
                        label: 'Daily Protein (g)',
                        data: proteinSeries,
                        borderColor: '#4895EF',
                        backgroundColor: 'rgba(72, 149, 239, 0.08)',
                        yAxisID: 'yProtein',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 3,
                    },
                    {
                        label: 'Calorie Goal',
                        data: Array(labels.length).fill(calorieGoal),
                        borderColor: '#2D6A4F',
                        yAxisID: 'yCalories',
                        borderDash: [6, 6],
                        borderWidth: 2,
                        pointRadius: 0,
                    },
                    {
                        label: 'Protein Goal',
                        data: Array(labels.length).fill(proteinGoal),
                        borderColor: '#1D3557',
                        yAxisID: 'yProtein',
                        borderDash: [6, 6],
                        borderWidth: 2,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { font: { size: 13, weight: 'bold' } },
                    },
                },
                scales: {
                    x: {
                        ticks: {
                            ...tickStyle,
                            maxRotation: 45,
                            minRotation: 0,
                        },
                    },
                    yCalories: {
                        type: 'linear',
                        position: 'left',
                        beginAtZero: true,
                        title: { display: true, text: 'Calories (kcal)' },
                        ticks: tickStyle,
                    },
                    yProtein: {
                        type: 'linear',
                        position: 'right',
                        beginAtZero: true,
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Protein (g)' },
                        ticks: tickStyle,
                    },
                },
            },
        });
    }

    const macroCanvas = document.getElementById('macroChart');
    if (macroCanvas) {
        new Chart(macroCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Protein', 'Carbs', 'Fats'],
                datasets: [
                    {
                        label: 'Today',
                        data: [
                            todayTotals.protein || 0,
                            todayTotals.carbs || 0,
                            todayTotals.fats || 0,
                        ],
                        backgroundColor: '#52B788',
                        borderColor: '#2D6A4F',
                        borderWidth: 1,
                    },
                    {
                        label: 'Goal',
                        data: [
                            macroGoals.protein || 0,
                            macroGoals.carbs || 0,
                            macroGoals.fats || 0,
                        ],
                        backgroundColor: '#E9ECEF',
                        borderColor: '#6C757D',
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { font: { size: 13, weight: 'bold' } },
                    },
                },
                scales: {
                    x: {
                        ticks: {
                            ...tickStyle,
                            maxRotation: 45,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Grams (g)' },
                        ticks: tickStyle,
                    },
                },
            },
        });
    }
})();
