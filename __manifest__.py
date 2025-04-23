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

    'category': 'Gestión de Equipos',
    'version': '0.1',

    # Añadimos las dependencias externas
    'external_dependencies': {
        'python': ['requests', 'requests_toolbelt'],
    },

    'depends': [
        'base', 
        'mail', 
        'contacts', 
        'helpdesk',
        'sale_management', 
        'portal', 
        'sale_subscription', 
        'website',
        'web',
        'auth_signup', 
        'auth_oauth',
        
    ],

    'data': [
        'views/views.xml',        
        'views/ticket_copier.xml',         
        'views/marcas.xml',             
        'views/modelos.xml',               
        'views/portal_suscripcion.xml',
        'views/vista_tree_portal.xml',
        'security/ir.model.access.csv',        
        'data/ir.secuencia.xml',             
        'report/copier_company_report.xml',
        'report/counter_report.xml',
        'views/copier_company_form_template.xml',
        'views/security_control_views.xml',
        'data/plantillas_mail.xml',
        'data/checklist_items_data.xml',
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
        'views/contadores.xml',
        'views/detalles_usuarios.xml',
        'views/portal_templates.xml',
        'views/manuals.xml', 
        'views/manuals_template.xml',
        'views/copier_stock_views.xml',
        'views/website_stock_templates.xml',
        'views/stock_copier_list_template.xml',
        'views/stock_copier_detail_template.xml',      
        'static/src/xml/counter_charts_templates.xml',
        
        
        
        
        
    ],

    'assets': {
        'web.assets_frontend': [
            # 1) Bootstrap CSS/JS de Odoo 18
            'copier_company/static/lib/bootstrap/css/bootstrap.min.css',
            'copier_company/static/lib/bootstrap/js/bootstrap.bundle.min.js',
            # 2) Tus estilos propios
            'copier_company/static/src/css/counter_charts.css',
            'copier_company/static/src/css/cotizacion_styles.css',
            'copier_company/static/src/css/PcloudDescargas.css',
            'copier_company/static/src/css/copier_list.css',
            # 3) Tus scripts propios
            'copier_company/static/src/js/manuals.js',
            'copier_company/static/src/js/counter_charts.js',
            'copier_company/static/src/js/PcloudDescargas.js',
            'copier_company/static/src/js/custom_script.js',
            # ❌ Ya no incluimos copier_list.js aquí porque es independiente
            # 'copier_company/static/src/js/copier_list.js',
            # 4) Bibliotecas externas si las necesitas
            'copier_company/static/lib/pdfjs/pdf.mjs',
            'copier_company/static/lib/pdfjs/pdf.worker.mjs',
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
        ],
        'web.assets_frontend_libs': [
            ('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js', {'type': 'external'}),
        ],
        'web.report_assets_common': [
            'https://unpkg.com/modern-normalize@2.0.0/modern-normalize.css',
            'https://unpkg.com/@tailwindcss/typography@0.5.10/dist/typography.min.css',
            'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap',
        ],
    },

    
    'application': True,
    'installable': True,
    'auto_install': False,
}