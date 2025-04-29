/*
 * Copier Company Module - Counter Charts
 * Este archivo contiene las funciones para la visualización de gráficos
 * de consumo de copias en el portal de clientes.
 */

document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart === 'undefined') {
        // Si Chart.js no está cargado aún, esperar un poco
        console.log('Chart.js no está cargado aún, esperando...');
        setTimeout(initCharts, 1000);
    } else {
        console.log('Chart.js está cargado, inicializando gráficos...');
        initCharts();
    }
});

/**
 * Inicializa los gráficos de consumo
 */
function initCharts() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js no está disponible. No se pueden inicializar los gráficos.');
        return;
    }
    
    var chartDataElement = document.getElementById('charts-data');
    if (!chartDataElement) {
        console.warn('No se encontraron datos para los gráficos');
        return;
    }

    try {
        var chartData = JSON.parse(chartDataElement.dataset.chartData || '{"monthly":[],"yearly":[]}');
        var isColor = chartDataElement.dataset.isColor === 'true';

        console.log('Datos para gráfico mensual:', chartData.monthly);
        console.log('Datos para gráfico anual:', chartData.yearly);
        console.log('Datos para gráfico por usuario:', chartData.by_user);

        initMonthlyChart(chartData.monthly, isColor);
        initYearlyChart(chartData.yearly, isColor);
        initUserChart(chartData.by_user); // ✅ LLAMADA AL NUEVO GRÁFICO
    } catch (error) {
        console.error('Error al inicializar los gráficos:', error);
    }
}

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
    var monthlyChart = new Chart(ctx, {
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
    var yearlyChart = new Chart(ctx, {
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

function initUserChart(data) {
    if (!data || data.length === 0 || !document.getElementById('userChart')) {
        console.warn('No hay datos para el gráfico por usuario o no existe el canvas');
        return;
    }

    var ctx = document.getElementById('userChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: 'Copias por Usuario',
                data: data.map(item => item.copies),
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
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
        }
    });
}
