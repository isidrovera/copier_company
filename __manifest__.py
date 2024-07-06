# -*- coding: utf-8 -*-
{
    'name': "Gestión de Fotocopiadoras",

    'summary': """
        Gestiona eficientemente el alquiler, venta y reparación de fotocopiadoras con el módulo dedicado de Copier Company.""",

    'description': """
        Este módulo está diseñado para Copier Company para manejar la complejidad del alquiler, venta y reparación de fotocopiadoras. Incluye funcionalidades para el seguimiento del inventario de fotocopiadoras, contratos con clientes, solicitudes de servicio y más, todo integrado en un único módulo de Odoo.
    """,

    'author': "Isidro",
    'website': "https://copiercompanysac.com",

    # Las categorías se pueden usar para filtrar módulos en el listado de módulos
    'category': 'Gestión de Equipos',
    'version': '0.1',

    # Módulos necesarios para que este funcione correctamente
    'depends': ['base', 'mail', 'contacts', 'helpdesk',
                'sale_management', 'portal', 'sale_subscription', 'website','web'],

    # Siempre cargado
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/ticket_copier.xml', 
        'views/descargas.xml',
        'views/marcas.xml',
        'views/portal.xml',        
        'views/descargas_portal.xml',
        'views/modelos.xml',
        'views/cotizaciones.xml',        
        'views/portal_suscripcion.xml',
        'views/vista_tree_portal.xml',
        'security/ir.model.access.csv',
        'static/src/js/script.js',
        'data/ir.secuencia.xml',
        'data/copier_company_data.xml',
        'views/extend_form_view.xml',
        'views/pCloud.xml',        
        'views/vista_nube.xml',        
        'views/portal_alquiler.xml',
        'views/confirmacion_formulario.xml',
        'views/formulario_help.xml',
        'views/demo_ticket.xml',
        'data/mail_ticket.xml',
        'views/pcloud_folder_list_template.xml',
        'views/cloud_storage_template.xml',
        'views/pcloud_templates.xml',        
        'views/pcloud_files_template.xml',
        'views/no_config_template.xml',
        'views/pcloudPublicoTemplate.xml',
        'views/pdf_view_template.xml',
        'views/ajustes_copier.xml',
        'report/copier_company_report.xml',
            
        
    ],

    'assets': {
        'web.assets_backend': [
            'copier_company/static/src/js/**/*.js',
           # 'copier_company/static/src/scss/**/*.scss',
            #'copier_company/static/src/xml/**/*.xml',
        ],
    },

   
    
    'application': True,
    'installable': True,
    'auto_install': False,
}
