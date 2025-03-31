/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * Componente para mostrar gráficos de contadores
 */
class CounterChartsComponent extends Component {
    setup() {
        this.monthlyChartRef = useRef("monthlyChart");
        this.yearlyChartRef = useRef("yearlyChart");
        this.chartData = null;
        this.isColor = false;
        this.charts = [];

        onMounted(async () => {
            // Cargar Chart.js de forma dinámica
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js");
            
            // Inicializar los gráficos
            this.initCharts();
        });
    }

    /**
     * Inicializa los gráficos
     */
    initCharts() {
        const chartDataElement = document.getElementById('counter_chart_data');
        if (!chartDataElement) {
            console.warn('No se encontraron datos para los gráficos');
            return;
        }
        
        try {
            this.chartData = JSON.parse(chartDataElement.dataset.chartData || '{"monthly":[],"yearly":[]}');
            this.isColor = chartDataElement.dataset.isColor === 'true';
            
            // Inicializar los gráficos
            this.initMonthlyChart();
            this.initYearlyChart();
        } catch (error) {
            console.error('Error al inicializar los gráficos:', error);
        }
    }

    /**
     * Inicializa el gráfico mensual
     */
    initMonthlyChart() {
        if (!this.chartData || !this.chartData.monthly || this.chartData.monthly.length === 0 || !this.monthlyChartRef.el) {
            return;
        }
        
        const ctx = this.monthlyChartRef.el.getContext('2d');
        
        const datasets = [
            {
                label: 'Copias B/N',
                data: this.chartData.monthly.map(item => item.bn),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }
        ];
        
        if (this.isColor) {
            datasets.push({
                label: 'Copias Color',
                data: this.chartData.monthly.map(item => item.color),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            });
        }
        
        // eslint-disable-next-line no-undef
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: this.chartData.monthly.map(item => item.name),
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
        
        this.charts.push(chart);
    }

    /**
     * Inicializa el gráfico anual
     */
    initYearlyChart() {
        if (!this.chartData || !this.chartData.yearly || this.chartData.yearly.length === 0 || !this.yearlyChartRef.el) {
            return;
        }
        
        const ctx = this.yearlyChartRef.el.getContext('2d');
        
        const datasets = [
            {
                label: 'Copias B/N',
                data: this.chartData.yearly.map(item => item.bn),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }
        ];
        
        if (this.isColor) {
            datasets.push({
                label: 'Copias Color',
                data: this.chartData.yearly.map(item => item.color),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            });
        }
        
        // eslint-disable-next-line no-undef
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: this.chartData.yearly.map(item => item.name),
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
        
        this.charts.push(chart);
    }
}

CounterChartsComponent.template = 'copier_company.CounterChartsComponent';

// Registrar el componente en el sistema
registry.category("public_components").add("counter_charts", {
    component: CounterChartsComponent,
    selector: '.o_counters_charts',
});

export default CounterChartsComponent;