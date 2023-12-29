odoo.define('sat.mi_script', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.MiScript = publicWidget.Widget.extend({
        selector: '#select_serie',
        start: function() {
            this._super.apply(this, arguments);
            this.cargarSeries();
        },
        cargarSeries: function() {
            var self = this;
            this._rpc({
                route: '/helpdesk/get_series'
            }).then(function(data) {
                self.$el.empty();
                self.$el.append($('<option/>', {
                    value: '',
                    text: 'Seleccione una serie...'
                }));
                data.forEach(function(item) {
                    self.$el.append($('<option/>', {
                        value: item.id,
                        text: item.name
                    }));
                });
            }).catch(function(error) {
                alert("Error al cargar las series: " + JSON.stringify(error));
            });
        },
    });
});

