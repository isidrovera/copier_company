# -*- coding: utf-8 -*-
{
    'name': "Gestión de Fotocopiadoras",
    'summary': "Gestiona alquiler, venta y reparación de fotocopiadoras.",
    'description': """
        Módulo para gestionar inventario, contratos, tickets, portal y website
        para Copier Company.
    """,
    'author': "Isidro",
    'website': "https://copiercompanysac.com",
    'category': 'Gestión de Equipos',
    'version': '0.1',

    'external_dependencies': {
        'python': ['requests', 'requests_toolbelt', 'qrcode', 'PIL'],
        'bin': ['wkhtmltoimage'],
    },

    # 👉 Añadimos módulos de Website que usas (snippets/event/form/dynamic)
    'depends': [
        'base', 'web', 'mail', 'contacts', 'helpdesk',
        'sale_management', 'portal', 'sale_subscription',
        'website',
        'auth_signup', 'auth_oauth',
    ],

    'data': [
        # VISTAS / DATOS / REPORTES
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
        'report/sticker_report.xml',
        'report/cotizacion_multiples.xml',
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
        'views/sticker_template.xml',
        'views/view_remote_assistance_request.xml',
        'views/view_client_counter_submission.xml',
        'views/view_toner_request.xml',
        'views/homepage_template.xml',
        'views/servicios_web.xml',
        'views/cotizaciones_multiples.xml',
        'views/template_cotizaciones.xml',       
        'views/menus_actions.xml',
        'views/printtracker_config_views.xml',
        # ❗️ No cargues QWeb de frontend aquí; mejor en assets_qweb (abajo)
        # 'static/src/xml/counter_charts_templates.xml',
    ],

    'assets': {
        # ✅ Website: mete aquí tus JS/CSS de frontend (NO en web.assets_frontend)
        'website.assets_frontend': [
            # Estilos propios
            'copier_company/static/src/css/counter_charts.css',
            'copier_company/static/src/css/cotizacion_styles.css',
            'copier_company/static/src/css/PcloudDescargas.css',
            'copier_company/static/src/css/copier_list.css',
            
         

            # Scripts propios
            'copier_company/static/src/js/manuals.js',
            'copier_company/static/src/js/counter_charts.js',
            'copier_company/static/src/js/PcloudDescargas.js',
            'copier_company/static/src/js/custom_script.js',            
            'copier_company/static/src/js/copier_homepage_scripts.js',

            # 📄 PDF.js: usa una sola variante; elimina los .mjs locales para evitar conflictos AMD
            # Si prefieres CDN UMD (suficiente para visor):
            ('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js', {'type': 'external'}),
            ('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js', {'type': 'external'}),

            # 🔎 Lucide: fija versión para evitar SourceMap 404; si no quieres sourcemaps, usa .min sin mapa
            ('https://unpkg.com/lucide@0.451.0/dist/umd/lucide.min.js', {'type': 'external'}),
        ],

        # Librerías externas adicionales (si de verdad las quieres separadas)
        'website.assets_frontend_lib': [
            ('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js', {'type': 'external'}),
        ],

        # QWeb de tus componentes/widgets (asegura que se carguen en frontend)
        'web.assets_qweb': [
            'copier_company/static/src/xml/counter_charts_templates.xml',
        ],

        # Assets para reportes (se permiten externos, pero mejor “vendorizar” si hay CSP/CDN bloqueos)
        'web.report_assets_common': [
            ('https://unpkg.com/modern-normalize@2.0.0/modern-normalize.css', {'type': 'external'}),
            ('https://unpkg.com/@tailwindcss/typography@0.5.10/dist/typography.min.css', {'type': 'external'}),
            ('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap', {'type': 'external'}),
        ],
    },

    'application': True,
    'installable': True,
    'auto_install': False,
}
