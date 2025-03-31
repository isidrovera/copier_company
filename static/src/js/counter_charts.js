odoo.define('copier_company.counter_charts', function (require) {
    'use strict';

    // Dependencias
    var publicWidget = require('web.public.widget');

    publicWidget.registry.CopierCounterCharts = publicWidget.Widget.extend({
        selector: '.o_counters_charts',
        
        /**
         * @override
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initCharts();
            });
        },
        
        /**
         * Inicializa los gráficos de contadores
         */
        _initCharts: function () {
            var self = this;
            
            // Obtener datos del elemento data
            var chartDataElement = document.getElementById('counter_chart_data');
            if (!chartDataElement) {
                console.warn('No se encontraron datos para los gráficos');
                return;
            }
            
            var chartData = JSON.parse(chartDataElement.dataset.chartData || '{"monthly":[],"yearly":[]}');
            var isColor = chartDataElement.dataset.isColor === 'true';
            
            // Inicializar los gráficos si hay datos
            this._initMonthlyChart(chartData.monthly, isColor);
            this._initYearlyChart(chartData.yearly, isColor);
        },
        
        /**
         * Inicializa el gráfico mensual
         * @param {Array} data - Datos mensuales
         * @param {Boolean} isColor - Indica si el equipo es a color
         */
        _initMonthlyChart: function (data, isColor) {
            if (!data || data.length === 0 || !document.getElementById('monthlyChart')) {
                return;
            }
            
            var monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
            
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
            
            // eslint-disable-next-line no-undef
            new Chart(monthlyCtx, {
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
        },
        
        /**
         * Inicializa el gráfico anual
         * @param {Array} data - Datos anuales
         * @param {Boolean} isColor - Indica si el equipo es a color
         */
        _initYearlyChart: function (data, isColor) {
            if (!data || data.length === 0 || !document.getElementById('yearlyChart')) {
                return;
            }
            
            var yearlyCtx = document.getElementById('yearlyChart').getContext('2d');
            
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
            
            // eslint-disable-next-line no-undef
            new Chart(yearlyCtx, {
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
        }
    });

    return publicWidget.registry.CopierCounterCharts;
});