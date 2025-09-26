/*
 * Copier Company Module - Counter Charts
 * Este archivo contiene las funciones para la visualización de gráficos
 * de consumo de copias en el portal de clientes.
 */

// Variables globales para los gráficos
let monthlyChart = null;
let yearlyChart = null;
let userChart = null;
let userDetailChart = null;
let userAnalysisChart = null;
let allUserData = [];

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
 * Inicializa todos los gráficos de consumo
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

        // Inicializar gráficos principales
        initMonthlyChart(chartData.monthly, isColor);
        initYearlyChart(chartData.yearly, isColor);
        initUserChart(chartData.by_user);
        initUserMonthlyChart(chartData.by_user_monthly);
        
        // Inicializar gráficos de usuario desde template
        initUserChartsFromTemplate();
        
    } catch (error) {
        console.error('Error al inicializar los gráficos:', error);
        // Fallback: intentar inicializar solo gráficos de usuario
        initUserChartsFromTemplate();
    }
}

/**
 * Inicializa los gráficos de usuario desde datos del template
 */
function initUserChartsFromTemplate() {
    console.log('Inicializando gráficos de usuario desde template...');
    
    // Inicializar gráfico de detalle (tabla lateral)
    initUserDetailChartFromTemplate();
    
    // Inicializar gráfico de análisis con filtros
    initUserAnalysisChartFromTemplate();
}

/**
 * Inicializa el gráfico de detalle de usuario (tabla lateral)
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
        userDetailChart.destroy();
        userDetailChart = null;
    }
    
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }
    
    // Obtener datos desde elementos del DOM
    const userRows = document.querySelectorAll('#userDetailChart').length > 0 ? 
        document.querySelectorAll('tr[t-foreach*="usuario_detalle_ids"]') : [];
    
    if (userRows.length === 0) {
        console.log('No se encontraron datos de usuario en el DOM');
        return;
    }
    
    // Nota: Los datos reales se obtienen del backend a través del template
    // Este es un placeholder para cuando el template procese los datos
    const ctx = canvas.getContext('2d');
    const colors = ['#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0'];
    
    // Crear gráfico básico - los datos reales se cargarán cuando el template se procese
    userDetailChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: colors,
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
                            return `${context.label}: ${context.parsed.toLocaleString()} copias`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Inicializa el gráfico de análisis de usuario con filtros
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
        userAnalysisChart.destroy();
        userAnalysisChart = null;
    }
    
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }
    
    // Preparar datos y filtros
    prepareAllUserDataFromTemplate();
    populateMonthFilter();
    updateAnalysisChart();
    
    // Event listeners para los filtros
    const monthFilter = document.getElementById('monthFilter');
    const chartType = document.getElementById('chartType');
    
    if (monthFilter) {
        monthFilter.addEventListener('change', updateAnalysisChart);
    }
    
    if (chartType) {
        chartType.addEventListener('change', updateAnalysisChart);
    }
}

/**
 * Prepara datos de usuario desde el template
 */
function prepareAllUserDataFromTemplate() {
    allUserData = [];
    console.log('Preparando datos de usuario desde template...');
    
    // Esta función será complementada por el template QWeb
    // que inyectará los datos reales
}

/**
 * Pobla el filtro de meses
 */
function populateMonthFilter() {
    const monthFilter = document.getElementById('monthFilter');
    if (!monthFilter) return;
    
    console.log('Poblando filtro de meses...');
    
    // Limpiar opciones existentes (excepto "Todos los meses")
    while (monthFilter.children.length > 1) {
        monthFilter.removeChild(monthFilter.lastChild);
    }
    
    if (allUserData.length === 0) {
        console.log('No hay datos para poblar el filtro');
        return;
    }
    
    // Agregar opciones de meses
    allUserData.forEach((data, index) => {
        console.log(`Agregando opción ${index + 1}:`, data.month, '- Usuarios:', data.users.length);
        const option = document.createElement('option');
        option.value = data.month;
        option.textContent = `${data.month} (${data.users.length} usuarios)`;
        monthFilter.appendChild(option);
    });
    
    console.log('Filtro poblado con', allUserData.length, 'meses');
}

/**
 * Actualiza el gráfico de análisis según filtros seleccionados
 */
function updateAnalysisChart() {
    const canvas = document.getElementById('userAnalysisChart');
    const monthFilter = document.getElementById('monthFilter');
    const chartType = document.getElementById('chartType');
    
    if (!canvas || allUserData.length === 0) return;
    
    const selectedMonth = monthFilter ? monthFilter.value : '';
    const selectedType = chartType ? chartType.value : 'doughnut';
    
    console.log('Actualizando gráfico - Mes:', selectedMonth, 'Tipo:', selectedType);
    
    // Filtrar datos por mes
    let filteredData = selectedMonth ? 
        allUserData.filter(data => data.month === selectedMonth) : 
        allUserData;
    
    if (filteredData.length === 0) return;
    
    // Agregar datos de usuarios
    const userTotals = {};
    filteredData.forEach(monthData => {
        monthData.users.forEach(user => {
            if (userTotals[user.name]) {
                userTotals[user.name] += user.copies;
            } else {
                userTotals[user.name] = user.copies;
            }
        });
    });
    
    const labels = Object.keys(userTotals);
    const data = Object.values(userTotals);
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', 
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
    ];
    
    // Destruir gráfico anterior
    if (userAnalysisChart) {
        userAnalysisChart.destroy();
    }
    
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
                            return `${labels[context.dataIndex]}: ${context.parsed.y ? context.parsed.y.toLocaleString() : context.parsed.toLocaleString()} copias`;
                        } else {
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed.toLocaleString()} copias (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };
    
    // Configurar datasets según tipo
    switch(selectedType) {
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
            
        default: // doughnut, pie, polarArea, bar
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
                        return value.toLocaleString();
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
                        return value.toLocaleString();
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
 * Función pública para actualizar datos de usuario desde el template
 */
window.updateUserDataFromTemplate = function(userData) {
    allUserData = userData;
    console.log('Datos de usuario actualizados desde template:', allUserData);
    populateMonthFilter();
    updateAnalysisChart();
};

/**
 * Inicializa el gráfico de consumo mensual
 * @param {Array} data - Datos para el gráfico
 * @param {Boolean} isColor - Indica si el equipo es color
 */
function initMonthlyChart(data, isColor) {
    if (!data || data.length === 0 || !document.getElementById('monthlyChart')) {
        console.warn('No hay datos para el gráfico mensual o no existe el elemento canvas');
        return;
    }
    
    var ctx = document.getElementById('monthlyChart').getContext('2d');
    
    var datasets = [
        {
            label: 'Copias B/N',
            data: data.map(function(item) { return item.bn; }),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }
    ];
    
    if (isColor) {
        datasets.push({
            label: 'Copias Color',
            data: data.map(function(item) { return item.color; }),
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
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toLocaleString();
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
                        var data = dataset.data[index];
                        if (data > 0) {
                            ctx.fillStyle = dataset.borderColor;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'bottom';
                            ctx.fillText(data.toLocaleString(), bar.x, bar.y - 5);
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
 * Inicializa el gráfico de consumo anual
 * @param {Array} data - Datos para el gráfico
 * @param {Boolean} isColor - Indica si el equipo es color
 */
function initYearlyChart(data, isColor) {
    if (!data || data.length === 0 || !document.getElementById('yearlyChart')) {
        console.warn('No hay datos para el gráfico anual o no existe el elemento canvas');
        return;
    }
    
    var ctx = document.getElementById('yearlyChart').getContext('2d');
    
    var datasets = [
        {
            label: 'Copias B/N',
            data: data.map(function(item) { return item.bn; }),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }
    ];
    
    if (isColor) {
        datasets.push({
            label: 'Copias Color',
            data: data.map(function(item) { return item.color; }),
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
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toLocaleString();
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
                        var data = dataset.data[index];
                        if (data > 0) {
                            ctx.fillStyle = dataset.borderColor;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'bottom';
                            ctx.fillText(data.toLocaleString(), bar.x, bar.y - 5);
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
 * Inicializa el gráfico de consumo por usuario (pestaña)
 * @param {Array} data - Datos para el gráfico
 */
function initUserChart(data) {
    if (!data || data.length === 0 || !document.getElementById('userChart')) {
        console.warn('No hay datos para el gráfico por usuario o no existe el canvas userChart');
        return;
    }

    const ctx = document.getElementById('userChart').getContext('2d');

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
                data: data.map(item => item.copies),
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
                        label: context => `${context.dataset.label}: ${context.raw.toLocaleString()}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Número de copias' }
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
                    if (meta) {
                        ctx.fillStyle = chart.data.datasets[0].borderColor[i];
                        ctx.textAlign = 'center';
                        ctx.fillText(val.toLocaleString(), meta.x, meta.y - 5);
                    }
                });
                ctx.restore();
            }
        }]
    });
    
    console.log('Gráfico por usuario inicializado correctamente');
}

/**
 * Inicializa el gráfico de consumo mensual por usuario
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

    var ctx = canvas.getContext('2d');
    
    var preparedDatasets = data.datasets.map((ds, i) => {
        const colorHue = (i * 47) % 360;
        return {
            ...ds,
            backgroundColor: `hsl(${colorHue}, 70%, 60%)`,
            borderColor: `hsl(${colorHue}, 70%, 50%)`,
            borderWidth: 1
        };
    });

    console.log('[initUserMonthlyChart] Inicializando instancia de Chart.js...');
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
                            return `${context.dataset.label}: ${context.raw.toLocaleString()}`;
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