# -*- coding: utf-8 -*-
{
    'name': "Onedrive",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "isidro",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail', 'contacts','helpdesk',
    'sale_management','portal','sale_subscription'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/ticket_copier.xml', 
        'views/descargas.xml',
        'views/marcas.xml',
        'views/portal.xml',        
        'views/descargas_portal.xml',
        'views/modelos.xml',
        #'views/cotizacion_formulario.xml',
        #'views/cotizaciones.xml',        
        'views/portal_suscripcion.xml',
        'views/vista_tree_portal.xml',
        'security/ir.model.access.csv',
        'static/src/js/script.js',
        'data/ir.secuencia.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',        
    ],
    
        'application': True,
        'installable': True,
        'auto_install': False,
    
}
