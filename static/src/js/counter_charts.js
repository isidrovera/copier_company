/**
 * Script para inicializar los gráficos de contadores
 * Compatible con Odoo 18
 */

// Esperar a que el documento esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, verificando Chart.js...');
    
    // Verificar si se ha cargado Chart.js correctamente
    if (typeof Chart === 'undefined') {
        console.error('Chart.js no está disponible. Intentando cargar desde CDN...');
        
        // Intentar cargar Chart.js manualmente si no está disponible
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js';
        script.async = true;
        script.onload = function() {
            console.log('Chart.js cargado manualmente, inicializando gráficos...');
            initCharts();
        };
        script.onerror = function() {
            console.error('No se pudo cargar Chart.js desde CDN.');
        };
        document.head.appendChild(script);
    } else {
        console.log('Chart.js ya está disponible, inicializando gráficos...');
        initCharts();
    }
});

/**
 * Inicializa los gráficos de contadores
 */
function initCharts() {
    try {
        // Obtener datos para los gráficos
        const chartDataElement = document.getElementById('counter_chart_data');
        if (!chartDataElement) {
            console.warn('No se encontraron datos para los gráficos');
            return;
        }
        
        const chartData = JSON.parse(chartDataElement.dataset.chartData || '{"monthly":[],"yearly":[]}');
        const isColor = chartDataElement.dataset.isColor === 'true';
        
        console.log('Datos para gráfico mensual:', chartData.monthly);
        console.log('Datos para gráfico anual:', chartData.yearly);
        
        // Inicializar gráfico mensual
        initMonthlyChart(chartData.monthly, isColor);
        
        // Inicializar gráfico anual
        initYearlyChart(chartData.yearly, isColor);
    } catch (error) {
        console.error('Error al inicializar los gráficos:', error);
    }
}

/**
 * Inicializa el gráfico mensual
 */
function initMonthlyChart(data, isColor) {
    if (!data || data.length === 0 || !document.getElementById('monthlyChart')) {
        console.warn('No hay datos para el gráfico mensual o no existe el elemento canvas');
        return;
    }
    
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    
    const datasets = [
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
    new Chart(ctx, {
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
        }
    });
    console.log('Gráfico mensual inicializado correctamente');
}

/**
 * Inicializa el gráfico anual
 */
function initYearlyChart(data, isColor) {
    if (!data || data.length === 0 || !document.getElementById('yearlyChart')) {
        console.warn('No hay datos para el gráfico anual o no existe el elemento canvas');
        return;
    }
    
    const ctx = document.getElementById('yearlyChart').getContext('2d');
    
    const datasets = [
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
    new Chart(ctx, {
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
        }
    });
    console.log('Gráfico anual inicializado correctamente');
}