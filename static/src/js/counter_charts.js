/*
 * Copier Company Module - Counter Charts
 * Este archivo contiene las funciones para la visualización de gráficos
 * de consumo de copias en el portal de clientes.
 *
 * IMPORTANTE:
 * - Mantiene la lógica existente de gráficos.
 * - Mantiene window.updateUserDataFromTemplate(userData).
 * - Corrige compatibilidad entre user.copies y user.total/bn/color.
 * - Mantiene soporte para Chart.js y tabs.
 */

// Variables globales para los gráficos
let monthlyChart = null;
let yearlyChart = null;
let userChart = null;
let userDetailChart = null;
let userAnalysisChart = null;
let userMonthlyChart = null;
let equipmentRankingChart = null;
let allUserData = [];

// Compatibilidad con la instancia usada en tu lógica anterior
window.userMonthlyChartInstance = window.userMonthlyChartInstance || null;

document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart === 'undefined') {
        console.log('Chart.js no está cargado aún, esperando...');
        setTimeout(initCharts, 1000);
    } else {
        console.log('Chart.js está cargado, inicializando gráficos...');
        initCharts();
    }
});

/**
 * Devuelve un número seguro.
 */
function safeNumber(value) {
    const number = Number(value || 0);
    return isNaN(number) ? 0 : number;
}

/**
 * Formatea números.
 */
function formatNumber(value) {
    return safeNumber(value).toLocaleString('es-PE');
}

/**
 * Obtiene el total de copias de un usuario.
 * Compatibilidad:
 * - Nuevo: total
 * - Anterior: copies
 * - Fallback: bn + color
 */
function getUserCopyValue(user) {
    if (!user) {
        return 0;
    }

    if (user.total !== undefined && user.total !== null) {
        return safeNumber(user.total);
    }

    if (user.copies !== undefined && user.copies !== null) {
        return safeNumber(user.copies);
    }

    return safeNumber(user.bn) + safeNumber(user.color);
}

/**
 * Obtiene nombre seguro de usuario.
 */
function getUserName(user) {
    return user && user.name ? user.name : 'Sin usuario';
}

/**
 * Destruye un gráfico de forma segura.
 */
function destroyChartSafely(chartInstance) {
    if (chartInstance) {
        try {
            chartInstance.destroy();
        } catch (error) {
            console.warn('No se pudo destruir gráfico:', error);
        }
    }
}

/**
 * Destruye gráfico existente asociado a un canvas.
 */
function destroyExistingChartByCanvas(canvas) {
    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    try {
        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }
    } catch (error) {
        console.warn('No se pudo destruir Chart existente en canvas:', error);
    }
}

/**
 * Genera colores manteniendo compatibilidad visual.
 */
function getDefaultColors(length) {
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#C9CBCF', '#0d6efd', '#6610f2', '#6f42c1',
        '#d63384', '#dc3545', '#fd7e14', '#ffc107', '#198754',
        '#20c997', '#0dcaf0', '#6c757d'
    ];

    const result = [];
    for (let i = 0; i < length; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

/**
 * Inicializa todos los gráficos de consumo.
 */
function initCharts() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js no está disponible. No se pueden inicializar los gráficos.');
        return;
    }

    var chartDataElement = document.getElementById('charts-data');
    if (!chartDataElement) {
        console.warn('No se encontraron datos para los gráficos');

        // Intentar inicializar gráficos de usuario sin datos del backend
        initUserChartsFromTemplate();
        return;
    }

    try {
        var chartData = JSON.parse(chartDataElement.dataset.chartData || '{"monthly":[],"yearly":[]}');
        var isColor = chartDataElement.dataset.isColor === 'true';

        console.log('Datos para gráfico mensual:', chartData.monthly);
        console.log('Datos para gráfico anual:', chartData.yearly);
        console.log('Datos para gráfico por usuario:', chartData.by_user);
        console.log('Datos para gráfico mensual por usuario:', chartData.by_user_monthly);
        console.log('Datos para ranking por equipo:', chartData.by_equipment);

        // Inicializar gráficos principales
        initMonthlyChart(chartData.monthly || [], isColor);
        initYearlyChart(chartData.yearly || [], isColor);
        initUserChart(chartData.by_user || []);
        initUserMonthlyChart(chartData.by_user_monthly || { labels: [], datasets: [] });

        // Nuevo opcional: ranking por equipo si existe canvas y datos
        initEquipmentRankingChart(chartData.by_equipment || []);

        // Inicializar gráficos de usuario desde template
        initUserChartsFromTemplate();

    } catch (error) {
        console.error('Error al inicializar los gráficos:', error);

        // Fallback: intentar inicializar solo gráficos de usuario
        initUserChartsFromTemplate();
    }
}

/**
 * Inicializa los gráficos de usuario desde datos del template.
 */
function initUserChartsFromTemplate() {
    console.log('Inicializando gráficos de usuario desde template...');

    // Inicializar gráfico de detalle (tabla lateral)
    initUserDetailChartFromTemplate();

    // Inicializar gráfico de análisis con filtros
    initUserAnalysisChartFromTemplate();
}

/**
 * Inicializa el gráfico de detalle de usuario (tabla lateral).
 */
function initUserDetailChartFromTemplate() {
    const canvas = document.getElementById('userDetailChart');
    if (!canvas) {
        console.log('Canvas userDetailChart no encontrado');
        return;
    }

    console.log('Inicializando gráfico de detalle de usuario...');

    // Destruir gráfico existente
    if (userDetailChart) {
        destroyChartSafely(userDetailChart);
        userDetailChart = null;
    }

    destroyExistingChartByCanvas(canvas);

    const ctx = canvas.getContext('2d');
    const colors = [
        '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
        '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0'
    ];

    /*
     * En tu lógica anterior este gráfico iniciaba vacío porque los datos reales
     * llegan desde el template por window.updateUserDataFromTemplate().
     * Mantengo ese comportamiento, pero si ya existe allUserData, lo uso.
     */
    const userTotals = {};

    if (allUserData && allUserData.length > 0) {
        allUserData.forEach(monthData => {
            (monthData.users || []).forEach(user => {
                const name = getUserName(user);
                const value = getUserCopyValue(user);

                if (!userTotals[name]) {
                    userTotals[name] = 0;
                }
                userTotals[name] += value;
            });
        });
    }

    const labels = Object.keys(userTotals);
    const values = Object.values(userTotals);

    userDetailChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed || 0;
                            const total = values.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                            return `${context.label}: ${formatNumber(value)} copias (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Inicializa el gráfico de análisis de usuario con filtros.
 */
function initUserAnalysisChartFromTemplate() {
    const canvas = document.getElementById('userAnalysisChart');
    if (!canvas) {
        console.log('Canvas userAnalysisChart no encontrado');
        return;
    }

    console.log('Inicializando gráfico de análisis de usuario...');

    // Destruir gráfico existente
    if (userAnalysisChart) {
        destroyChartSafely(userAnalysisChart);
        userAnalysisChart = null;
    }

    destroyExistingChartByCanvas(canvas);

    // Preparar datos y filtros
    prepareAllUserDataFromTemplate();
    populateMonthFilter();
    updateAnalysisChart();

    // Event listeners para los filtros
    const monthFilter = document.getElementById('monthFilter');
    const chartType = document.getElementById('chartType');

    if (monthFilter && !monthFilter.dataset.listenerAttached) {
        monthFilter.addEventListener('change', updateAnalysisChart);
        monthFilter.dataset.listenerAttached = '1';
    }

    if (chartType && !chartType.dataset.listenerAttached) {
        chartType.addEventListener('change', updateAnalysisChart);
        chartType.dataset.listenerAttached = '1';
    }
}

/**
 * Prepara datos de usuario desde el template.
 *
 * En tu lógica original esta función se dejaba como placeholder
 * porque el template QWeb inyecta datos reales usando:
 * window.updateUserDataFromTemplate(userData)
 */
function prepareAllUserDataFromTemplate() {
    console.log('Preparando datos de usuario desde template...');

    if (!allUserData) {
        allUserData = [];
    }

    // No limpiamos allUserData si ya tiene datos,
    // porque puede haber sido actualizado por window.updateUserDataFromTemplate().
    if (allUserData.length === 0) {
        console.log('allUserData vacío. Se espera actualización desde template QWeb.');
    }
}

/**
 * Pobla el filtro de meses.
 */
function populateMonthFilter() {
    const monthFilter = document.getElementById('monthFilter');
    if (!monthFilter) return;

    console.log('Poblando filtro de meses...');

    // Limpiar opciones existentes (excepto "Todos los meses")
    while (monthFilter.children.length > 1) {
        monthFilter.removeChild(monthFilter.lastChild);
    }

    if (!allUserData || allUserData.length === 0) {
        console.log('No hay datos para poblar el filtro');
        return;
    }

    const addedMonths = new Set();

    // Agregar opciones de meses
    allUserData.forEach((data, index) => {
        const monthKey = data.key || data.month || '';
        const monthLabel = data.month || data.key || 'Sin mes';

        if (!monthKey || addedMonths.has(monthKey)) {
            return;
        }

        addedMonths.add(monthKey);

        const usersLength = data.users ? data.users.length : 0;

        console.log(`Agregando opción ${index + 1}:`, monthLabel, '- Usuarios:', usersLength);

        const option = document.createElement('option');
        option.value = monthKey;
        option.textContent = `${monthLabel} (${usersLength} usuarios)`;
        monthFilter.appendChild(option);
    });

    console.log('Filtro poblado con', addedMonths.size, 'meses');
}

/**
 * Actualiza el gráfico de análisis según filtros seleccionados.
 */
function updateAnalysisChart() {
    const canvas = document.getElementById('userAnalysisChart');
    const monthFilter = document.getElementById('monthFilter');
    const chartType = document.getElementById('chartType');

    if (!canvas) {
        console.log('Canvas userAnalysisChart no encontrado');
        return;
    }

    if (!allUserData || allUserData.length === 0) {
        console.log('No hay datos de usuario para actualizar gráfico');
        return;
    }

    const selectedMonth = monthFilter ? monthFilter.value : '';
    const selectedType = chartType ? chartType.value : 'doughnut';

    console.log('Actualizando gráfico - Mes:', selectedMonth, 'Tipo:', selectedType);

    // Filtrar datos por mes
    let filteredData = selectedMonth
        ? allUserData.filter(data => (data.key || data.month) === selectedMonth)
        : allUserData;

    if (filteredData.length === 0) {
        console.log('No hay datos filtrados para el mes seleccionado');
        return;
    }

    // Agregar datos de usuarios
    const userTotals = {};
    filteredData.forEach(monthData => {
        (monthData.users || []).forEach(user => {
            const name = getUserName(user);
            const value = getUserCopyValue(user);

            if (userTotals[name]) {
                userTotals[name] += value;
            } else {
                userTotals[name] = value;
            }
        });
    });

    const labels = Object.keys(userTotals);
    const data = Object.values(userTotals);
    const colors = getDefaultColors(labels.length);

    // Destruir gráfico anterior
    if (userAnalysisChart) {
        destroyChartSafely(userAnalysisChart);
        userAnalysisChart = null;
    }

    destroyExistingChartByCanvas(canvas);

    const ctx = canvas.getContext('2d');

    // Configuración del dataset según tipo de gráfico
    let datasets = [];
    let chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: ['bar', 'line', 'scatter', 'bubble'].includes(selectedType) ? 'top' : 'right'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        if (['bubble', 'scatter'].includes(selectedType)) {
                            const parsedValue = context.parsed && context.parsed.y ? context.parsed.y : 0;
                            return `${labels[context.dataIndex]}: ${formatNumber(parsedValue)} copias`;
                        } else {
                            const total = data.reduce((a, b) => a + b, 0);
                            const value = context.parsed || context.raw || 0;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                            return `${context.label}: ${formatNumber(value)} copias (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    // Configurar datasets según tipo
    switch (selectedType) {
        case 'bubble':
            datasets = [{
                label: 'Copias por Usuario',
                data: data.map((value, index) => ({
                    x: index + 1,
                    y: value,
                    r: Math.max(5, Math.min(50, Math.sqrt(value) / 100))
                })),
                backgroundColor: colors.slice(0, labels.length).map(color => color + '80'),
                borderColor: colors.slice(0, labels.length),
                borderWidth: 2
            }];
            break;

        case 'scatter':
            datasets = [{
                label: 'Copias por Usuario',
                data: data.map((value, index) => ({
                    x: index + 1,
                    y: value
                })),
                backgroundColor: colors.slice(0, labels.length),
                borderColor: colors.slice(0, labels.length),
                borderWidth: 2,
                pointRadius: 8
            }];
            break;

        case 'radar':
            datasets = [{
                label: 'Copias por Usuario',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 2,
                pointBackgroundColor: colors.slice(0, labels.length),
                pointBorderColor: '#fff'
            }];
            break;

        case 'line':
            datasets = [{
                label: 'Copias por Usuario',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }];
            break;

        default:
            // doughnut, pie, polarArea, bar
            datasets = [{
                label: 'Copias por Usuario',
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: '#ffffff',
                borderWidth: 2
            }];
    }

    // Escalas para gráficos que las necesitan
    if (['bar', 'line', 'scatter', 'bubble'].includes(selectedType)) {
        chartOptions.scales = {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Número de Copias'
                },
                ticks: {
                    callback: function(value) {
                        return formatNumber(value);
                    }
                }
            }
        };

        if (['scatter', 'bubble'].includes(selectedType)) {
            chartOptions.scales.x = {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: 'Orden de Usuario'
                }
            };
        } else {
            chartOptions.scales.x = {
                title: {
                    display: true,
                    text: 'Usuarios'
                }
            };
        }
    } else if (selectedType === 'radar') {
        chartOptions.scales = {
            r: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return formatNumber(value);
                    }
                }
            }
        };
    }

    // Crear gráfico
    userAnalysisChart = new Chart(ctx, {
        type: selectedType,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });

    console.log('Gráfico de análisis actualizado');
}

/**
 * Función pública para actualizar datos de usuario desde el template.
 *
 * El template QWeb usa esta función para enviar:
 * [
 *   {
 *     month: 'Mayo 2026',
 *     date: '2026-05-01',
 *     name: 'Referencia',
 *     users: [
 *       {name:'Usuario', bn:10, color:5, total:15}
 *     ]
 *   }
 * ]
 */
window.updateUserDataFromTemplate = function(userData) {
    allUserData = Array.isArray(userData) ? userData : [];

    // Compatibilidad: si no viene copies, se calcula desde total/bn/color
    allUserData = allUserData.map(monthData => {
        const users = (monthData.users || []).map(user => {
            const fixedUser = { ...user };

            if (fixedUser.copies === undefined || fixedUser.copies === null) {
                fixedUser.copies = getUserCopyValue(fixedUser);
            }

            if (fixedUser.total === undefined || fixedUser.total === null) {
                fixedUser.total = getUserCopyValue(fixedUser);
            }

            return fixedUser;
        });

        return {
            ...monthData,
            key: monthData.key || monthData.month,
            users: users
        };
    });

    console.log('Datos de usuario actualizados desde template:', allUserData);

    populateMonthFilter();
    updateAnalysisChart();

    // Actualizar también el detalle por usuario si existe canvas
    if (document.getElementById('userDetailChart')) {
        initUserDetailChartFromTemplate();
    }
};

/**
 * Inicializa el gráfico de consumo mensual.
 * @param {Array} data - Datos para el gráfico
 * @param {Boolean} isColor - Indica si el equipo es color
 */
function initMonthlyChart(data, isColor) {
    if (!data || data.length === 0 || !document.getElementById('monthlyChart')) {
        console.warn('No hay datos para el gráfico mensual o no existe el elemento canvas');
        return;
    }

    var canvas = document.getElementById('monthlyChart');
    destroyExistingChartByCanvas(canvas);

    var ctx = canvas.getContext('2d');

    var datasets = [
        {
            label: 'Copias B/N',
            data: data.map(function(item) { return safeNumber(item.bn); }),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }
    ];

    if (isColor) {
        datasets.push({
            label: 'Copias Color',
            data: data.map(function(item) { return safeNumber(item.color); }),
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
        });
    }

    console.log('Inicializando gráfico mensual...');

    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(function(item) { return item.name; }),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Consumo Mensual de Copias'
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatNumber(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de copias'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Mes'
                    }
                }
            }
        },
        plugins: [{
            afterDraw: function(chart) {
                var ctx = chart.ctx;
                ctx.save();
                ctx.font = 'bold 12px Arial';

                chart.data.datasets.forEach(function(dataset, i) {
                    var meta = chart.getDatasetMeta(i);
                    meta.data.forEach(function(bar, index) {
                        var value = dataset.data[index];
                        if (value > 0) {
                            ctx.fillStyle = dataset.borderColor;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'bottom';
                            ctx.fillText(formatNumber(value), bar.x, bar.y - 5);
                        }
                    });
                });

                ctx.restore();
            }
        }]
    });

    console.log('Gráfico mensual inicializado correctamente');
}

/**
 * Inicializa el gráfico de consumo anual.
 * @param {Array} data - Datos para el gráfico
 * @param {Boolean} isColor - Indica si el equipo es color
 */
function initYearlyChart(data, isColor) {
    if (!data || data.length === 0 || !document.getElementById('yearlyChart')) {
        console.warn('No hay datos para el gráfico anual o no existe el elemento canvas');
        return;
    }

    var canvas = document.getElementById('yearlyChart');
    destroyExistingChartByCanvas(canvas);

    var ctx = canvas.getContext('2d');

    var datasets = [
        {
            label: 'Copias B/N',
            data: data.map(function(item) { return safeNumber(item.bn); }),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }
    ];

    if (isColor) {
        datasets.push({
            label: 'Copias Color',
            data: data.map(function(item) { return safeNumber(item.color); }),
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
        });
    }

    console.log('Inicializando gráfico anual...');

    yearlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(function(item) { return item.name; }),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Consumo Anual de Copias'
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatNumber(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de copias'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Año'
                    }
                }
            }
        },
        plugins: [{
            afterDraw: function(chart) {
                var ctx = chart.ctx;
                ctx.save();
                ctx.font = 'bold 12px Arial';

                chart.data.datasets.forEach(function(dataset, i) {
                    var meta = chart.getDatasetMeta(i);
                    meta.data.forEach(function(bar, index) {
                        var value = dataset.data[index];
                        if (value > 0) {
                            ctx.fillStyle = dataset.borderColor;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'bottom';
                            ctx.fillText(formatNumber(value), bar.x, bar.y - 5);
                        }
                    });
                });

                ctx.restore();
            }
        }]
    });

    console.log('Gráfico anual inicializado correctamente');
}

/**
 * Inicializa el gráfico de consumo por usuario (pestaña).
 * @param {Array} data - Datos para el gráfico
 */
function initUserChart(data) {
    if (!data || data.length === 0 || !document.getElementById('userChart')) {
        console.warn('No hay datos para el gráfico por usuario o no existe el canvas userChart');
        return;
    }

    const canvas = document.getElementById('userChart');
    destroyExistingChartByCanvas(canvas);

    const ctx = canvas.getContext('2d');

    const colors = [
        'rgba(255, 99, 132, 0.6)',
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 159, 64, 0.6)'
    ];

    const borderColors = colors.map(c => c.replace('0.6', '1'));

    userChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: 'Copias por Usuario',
                data: data.map(item => getUserCopyValue(item)),
                backgroundColor: colors.slice(0, data.length),
                borderColor: borderColors.slice(0, data.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Copias por Usuario (Período Actual)'
                },
                tooltip: {
                    callbacks: {
                        label: context => `${context.dataset.label}: ${formatNumber(context.raw)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Número de copias' },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            }
        },
        plugins: [{
            afterDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                ctx.font = 'bold 12px Arial';

                chart.data.datasets[0].data.forEach((val, i) => {
                    const meta = chart.getDatasetMeta(0).data[i];
                    if (meta && val > 0) {
                        ctx.fillStyle = chart.data.datasets[0].borderColor[i];
                        ctx.textAlign = 'center';
                        ctx.fillText(formatNumber(val), meta.x, meta.y - 5);
                    }
                });

                ctx.restore();
            }
        }]
    });

    console.log('Gráfico por usuario inicializado correctamente');
}

/**
 * Inicializa ranking por máquina si existe canvas.
 * Este gráfico es opcional y no rompe la lógica anterior si el canvas no existe.
 * @param {Array} data
 */
function initEquipmentRankingChart(data) {
    const canvas = document.getElementById('equipmentRankingChart');

    if (!canvas) {
        console.log('Canvas equipmentRankingChart no encontrado. Se omite ranking por equipo.');
        return;
    }

    if (!data || data.length === 0) {
        console.warn('No hay datos para ranking por equipo');
        return;
    }

    if (equipmentRankingChart) {
        destroyChartSafely(equipmentRankingChart);
        equipmentRankingChart = null;
    }

    destroyExistingChartByCanvas(canvas);

    const ctx = canvas.getContext('2d');
    const colors = getDefaultColors(data.length);

    equipmentRankingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: 'Total de copias',
                data: data.map(item => safeNumber(item.total)),
                backgroundColor: colors.map(color => color + '99'),
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                title: {
                    display: true,
                    text: 'Máquinas con mayor consumo'
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatNumber(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Copias'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Máquina'
                    }
                }
            }
        }
    });

    console.log('Ranking por equipo inicializado correctamente');
}

/**
 * Inicializa el gráfico de consumo mensual por usuario.
 * @param {Object} data - Datos para el gráfico con formato {labels: [], datasets: []}
 */
function initUserMonthlyChart(data) {
    console.log('[initUserMonthlyChart] Iniciando inicialización del gráfico mensual por usuario...');

    if (!data) {
        console.error('[initUserMonthlyChart] Error: No hay datos proporcionados para el gráfico');
        return;
    }

    var canvas = document.getElementById('userMonthlyChart');
    if (!canvas) {
        console.error('[initUserMonthlyChart] Error: No se encontró el elemento canvas con ID "userMonthlyChart"');
        return;
    }

    if (!data.labels || !data.datasets) {
        console.error('[initUserMonthlyChart] Error: Estructura de datos incorrecta. Se esperaban "labels" y "datasets"');
        return;
    }

    destroyExistingChartByCanvas(canvas);

    if (window.userMonthlyChartInstance) {
        destroyChartSafely(window.userMonthlyChartInstance);
        window.userMonthlyChartInstance = null;
    }

    var ctx = canvas.getContext('2d');

    var preparedDatasets = data.datasets.map((ds, i) => {
        const colorHue = (i * 47) % 360;
        return {
            ...ds,
            data: (ds.data || []).map(value => safeNumber(value)),
            backgroundColor: `hsl(${colorHue}, 70%, 60%)`,
            borderColor: `hsl(${colorHue}, 70%, 50%)`,
            borderWidth: 1
        };
    });

    console.log('[initUserMonthlyChart] Inicializando instancia de Chart.js.');

    window.userMonthlyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: preparedDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Copias Mensuales por Usuario'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatNumber(context.raw)}`;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Copias'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Mes'
                    }
                }
            }
        }
    });

    userMonthlyChart = window.userMonthlyChartInstance;

    console.log('[initUserMonthlyChart] Gráfico mensual por usuario inicializado exitosamente.');
}

// Redibujar el gráfico mensual por usuario al activar su tab
document.addEventListener('DOMContentLoaded', function () {
    const tab = document.querySelector('#user-monthly-tab');
    if (tab) {
        tab.addEventListener('shown.bs.tab', function () {
            if (window.userMonthlyChartInstance) {
                console.log('[initUserMonthlyChart] Redibujando gráfico al mostrar el tab');
                window.userMonthlyChartInstance.resize();
            }
        });
    }
});