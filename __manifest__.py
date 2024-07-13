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
        'views/ticket_copier.xml',         
        'views/marcas.xml',             
        'views/modelos.xml',               
        'views/portal_suscripcion.xml',
        'views/vista_tree_portal.xml',
        'security/ir.model.access.csv',        
        'data/ir.secuencia.xml',
        'data/copier_company_data.xml',        
        'views/pCloud.xml', 
        'views/confirmacion_formulario.xml',
        'views/formulario_help.xml',     
        'views/pcloud_folder_list_template.xml',
        'views/cloud_storage_template.xml',
        'views/pcloud_templates.xml',        
        'views/pcloud_files_template.xml',
        'views/no_config_template.xml',
        'views/ajustes_copier.xml',
        'report/copier_company_report.xml',
        'views/copier_company_form_template.xml',
        
            
        
    ],

    'assets': {
        'web.assets_frontend': [
            'copier_company/static/src/js/custom_script.js',
            'copier_company/static/src/js/PcloudDescargas.js',
            'copier_company/static/src/css/PcloudDescargas.css',
            
            
        ],
    },


   
    
    'application': True,
    'installable': True,
    'auto_install': False,
}
