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
        // CORRECCIÓN: Cambiar el log para mostrar la propiedad correcta
        console.log('Datos para gráfico mensual por usuario:', chartData.by_user_monthly);

        initMonthlyChart(chartData.monthly, isColor);
        initYearlyChart(chartData.yearly, isColor);
        initUserChart(chartData.by_user);
        // CORRECCIÓN: Pasar la propiedad correcta a la función
        initUserMonthlyChart(chartData.by_user_monthly);
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

/**
 * Inicializa el gráfico de consumo por usuario
 * @param {Array} data - Datos para el gráfico
 */
function initUserChart(data) {
    if (!data || data.length === 0 || !document.getElementById('userChart')) {
        console.warn('No hay datos para el gráfico por usuario o no existe el canvas');
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

    const dataset = {
        label: 'Copias por Usuario',
        data: data.map(item => item.copies),
        backgroundColor: colors.slice(0, data.length),
        borderColor: borderColors.slice(0, data.length),
        borderWidth: 1
    };

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [dataset]
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
function debugUserMonthlyData(data) {
    console.group('Debug datos mensuales por usuario');
    console.log('Estructura del objeto:', Object.keys(data || {}));
    
    if (data && data.labels) {
        console.log('Labels:', data.labels);
    } else {
        console.error('No hay propiedad labels');
    }
    
    if (data && data.datasets) {
        console.log('Datasets:', data.datasets.length);
        data.datasets.forEach((ds, i) => {
            console.log(`Dataset ${i}:`, ds.label, 'con', ds.data.length, 'datos');
        });
    } else {
        console.error('No hay propiedad datasets');
    }
    console.groupEnd();
}

/**
 * Inicializa el gráfico de consumo mensual por usuario con mejor manejo de errores
 * @param {Object} data - Datos para el gráfico con formato {labels: [], datasets: []}
 */
function initUserMonthlyChart(data) {
    if (!data) {
        console.error('No hay datos para el gráfico mensual por usuario');
        return;
    }
    
    var canvas = document.getElementById('userMonthlyChart');
    if (!canvas) {
        console.error('No existe el elemento canvas con ID userMonthlyChart');
        return;
    }

    // Depurar la estructura de datos
    debugUserMonthlyData(data);
    
    // Verificar que tenemos la estructura correcta de datos
    if (!data.labels || !data.datasets) {
        console.error('Estructura de datos incorrecta para el gráfico mensual por usuario');
        return;
    }

    var ctx = canvas.getContext('2d');
    
    console.log('Inicializando gráfico mensual por usuario...');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, i) => ({
                ...ds,
                backgroundColor: `hsl(${(i * 47) % 360}, 70%, 60%)`, // colores únicos por usuario
                borderColor: `hsl(${(i * 47) % 360}, 70%, 50%)`,
                borderWidth: 1
            }))
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
    
    console.log('Gráfico mensual por usuario inicializado correctamente');
}