/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted } from "@odoo/owl";

// Función para cargar Chart.js dinámicamente
const loadChartJS = () => {
    console.log('Iniciando carga de Chart.js...');
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js";
        script.onload = () => {
            console.log('Chart.js cargado exitosamente');
            resolve();
        };
        script.onerror = (error) => {
            console.error('Error al cargar Chart.js:', error);
            reject(new Error("No se pudo cargar Chart.js"));
        };
        document.head.appendChild(script);
    });
};

const componentRegistry = registry.category("public_components");

class CounterChartsComponent extends Component {
    setup() {
        console.log('Inicializando componente CounterChartsComponent');
        this.monthlyChartInst = null;
        this.yearlyChartInst = null;
        
        // Usar onMounted para asegurarnos que el DOM está listo
        onMounted(async () => {
            console.log('Componente montado, cargando Chart.js y datos...');
            this.initCharts();
        });
    }

    async initCharts() {
        console.log('Iniciando inicialización de gráficos...');
        try {
            // Cargar Chart.js dinámicamente
            await loadChartJS();
            
            // Verificar que Chart esté disponible
            if (typeof Chart === 'undefined') {
                throw new Error('Chart.js no se cargó correctamente');
            }
            
            console.log('Chart.js disponible, obteniendo datos para gráficos');
            // Obtener datos para los gráficos
            const chartDataElement = document.getElementById('counter_chart_data');
            if (!chartDataElement) {
                console.warn('No se encontraron datos para los gráficos');
                return;
            }
            
            try {
                const chartData = JSON.parse(chartDataElement.dataset.chartData || '{"monthly":[],"yearly":[]}');
                const isColor = chartDataElement.dataset.isColor === 'true';
                
                console.log('Datos para gráfico mensual:', chartData.monthly);
                console.log('Datos para gráfico anual:', chartData.yearly);
                
                // Inicializar gráfico mensual
                this.initMonthlyChart(chartData.monthly, isColor);
                
                // Inicializar gráfico anual
                this.initYearlyChart(chartData.yearly, isColor);
            } catch (error) {
                console.error('Error al procesar los datos de los gráficos:', error);
            }
        } catch (error) {
            console.error('Error al inicializar los gráficos:', error);
        }
    }

    initMonthlyChart(data, isColor) {
        console.log('Inicializando gráfico mensual...');
        if (!data || data.length === 0) {
            console.warn('No hay datos para el gráfico mensual');
            return;
        }
        
        const monthlyChartElement = document.getElementById('monthlyChart');
        if (!monthlyChartElement) {
            console.warn('No se encontró el elemento canvas para el gráfico mensual');
            return;
        }
        
        const ctx = monthlyChartElement.getContext('2d');
        
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
        
        // Crear el gráfico mensual
        this.monthlyChartInst = new Chart(ctx, {
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

    initYearlyChart(data, isColor) {
        console.log('Inicializando gráfico anual...');
        if (!data || data.length === 0) {
            console.warn('No hay datos para el gráfico anual');
            return;
        }
        
        const yearlyChartElement = document.getElementById('yearlyChart');
        if (!yearlyChartElement) {
            console.warn('No se encontró el elemento canvas para el gráfico anual');
            return;
        }
        
        const ctx = yearlyChartElement.getContext('2d');
        
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
        
        // Crear el gráfico anual
        this.yearlyChartInst = new Chart(ctx, {
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
}

CounterChartsComponent.template = 'copier_company.CounterChartsComponent';
componentRegistry.add("counter_charts", CounterChartsComponent);

export default CounterChartsComponent;