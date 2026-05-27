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
    'license': 'LGPL-3',

    'external_dependencies': {
        'python': ['requests', 'requests_toolbelt', 'qrcode', 'PIL'],
        'bin': ['wkhtmltoimage'],
    },

    # 👉 Añadimos odoo_onedrive_integration porque el wizard de envío
    # de facturas reutiliza el componente OneDriveApp.
    'depends': [
        'base', 'web', 'mail', 'contacts', 'helpdesk',
        'sale_management', 'portal', 'sale_subscription',
        'website',
        'account',
        'odoo_onedrive_integration',
    ],

    'data': [
        # VISTAS / DATOS / REPORTES
        'views/views.xml',
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
        'report/report_counter_portal.xml',
        'report/report_service_request.xml',
        'reports/quotation_simple_report.xml',
        'views/copier_company_form_template.xml',
        'views/security_control_views.xml',
        'data/plantillas_mail.xml',
        'data/copier_soporte_mail.xml',
        'data/whatsapp_service_templates.xml',
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
        'views/copier_about_us_views.xml',
        'views/sticker_a7_web.xml',
        'views/servicios_web.xml',
        'views/cotizaciones_multiples.xml',
        'views/template_cotizaciones.xml',
        'views/printtracker_config_views.xml',
        'views/portal_servicios_cliente.xml',
        'views/whatsapp_config_views.xml',
        'views/whatsapp_service_notification_views.xml',
        'views/public_service_tracking_templates.xml',
        'views/whatsapp_send_quotation_wizard_views.xml',
        'views/whatsapp_send_multi_quotation_wizard_views.xml',
        'views/report_invoice_modern.xml',
        'views/report_delivery_document_modern.xml',
        'views/copier_soporte.xml',
        'views/resolver_producto_page.xml',
        'views/view_product_name_alias.xml',
        'views/resolver_producto_views.xml',
        'views/account_move_send_wizard.xml',
        'views/copier_billing_group_views.xml',
        'views/copier_company_billing_group_views.xml',
        'views/copier_counter_billing_group_views.xml',
        'views/menus_actions.xml',
    ],

    'assets': {
        'web.assets_backend': [
            # pCloud explorer
            'copier_company/static/src/css/pcloud_explorer.css',
            'copier_company/static/src/xml/pcloud_explorer.xml',
            'copier_company/static/src/js/pcloud_explorer.js',

            # OneDrive selector (wizard envío facturas) — TODO en backend
            'copier_company/static/src/css/onedrive_selector.css',
            'copier_company/static/src/js/onedrive_selector_dialog.js',
            'copier_company/static/src/xml/onedrive_selector_dialog.xml',
        ],

        # ✅ Website / frontend
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
            'copier_company/static/src/js/cotizacion.js',
            'copier_company/static/src/js/copier_homepage_scripts.js',
            'copier_company/static/src/js/copier_services_scripts.js',

            # 📄 Templates QWeb del frontend
            # (En Odoo 17+ los XML van directo aquí, no en assets_qweb)
            'copier_company/static/src/xml/counter_charts_templates.xml',

            # 📄 PDF.js
            ('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js', {'type': 'external'}),
            ('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js', {'type': 'external'}),

            # 🔎 Lucide
            ('https://unpkg.com/lucide@0.451.0/dist/umd/lucide.min.js', {'type': 'external'}),
        ],

        # Librerías externas adicionales
        'website.assets_frontend_lib': [
            ('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js', {'type': 'external'}),
        ],

        # Assets de reportes
        'web.report_assets_common': [
            'copier_company/static/src/css/invoice_style.css',
        ],
    },

    'application': True,
    'installable': True,
    'auto_install': False,
}