
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

    'depends': [
        'base',
        'web',
        'mail',
        'contacts',
        'helpdesk',
        'sale_management',
        'portal',
        'sale_subscription',
        'website',
        'website_sale',
        'account',
        'odoo_onedrive_integration',
    ],

    'data': [

        # =========================================================
        # SEGURIDAD
        # =========================================================

        'security/portal_comercial_security.xml',
        'security/ir.model.access.csv',

        # =========================================================
        # DATOS BASE
        # =========================================================

        'data/ir.secuencia.xml',
        'data/libro_reclamaciones_sequence.xml',
        'data/plantillas_mail.xml',
        'data/copier_soporte_mail.xml',
        'data/whatsapp_service_templates.xml',
        'data/checklist_items_data.xml',
        'data/copier_company_data.xml',

        # =========================================================
        # REPORTES
        # =========================================================

        'report/copier_company_report.xml',
        'report/counter_report.xml',
        'report/sticker_report.xml',
        'report/cotizacion_multiples.xml',
        'report/report_counter_portal.xml',
        'report/report_service_request.xml',
        'report/quotation_simple_report.xml',
        'report/libro_reclamaciones_report.xml',

        # =========================================================
        # VISTAS BASE
        # =========================================================

        'views/views.xml',
        'views/marcas.xml',
        'views/modelos.xml',
        'views/portal_suscripcion.xml',
        'views/vista_tree_portal.xml',
        'views/copier_company_form_template.xml',
        'views/security_control_views.xml',

        # =========================================================
        # PCLOUD / DOCUMENTOS
        # =========================================================

        'views/pCloud.xml',
        'views/confirmacion_formulario.xml',
        'views/formulario_help.xml',
        'views/pcloud_folder_list_template.xml',
        'views/cloud_storage_template.xml',
        'views/pcloud_templates.xml',
        'views/pcloud_files_template.xml',
        'views/no_config_template.xml',

        # =========================================================
        # AJUSTES / CONTADORES
        # =========================================================

        'views/ajustes_copier.xml',
        'views/contadores.xml',
        'views/detalles_usuarios.xml',

        # =========================================================
        # PORTAL
        # =========================================================

        'views/portal_templates.xml',
        'views/manuals.xml',
        'views/manuals_template.xml',

        # =========================================================
        # STOCK
        # =========================================================

        'views/copier_stock_views.xml',
        'views/website_stock_templates.xml',
        'views/stock_copier_list_template.xml',
        'views/stock_copier_detail_template.xml',
        'views/sticker_template.xml',

        # =========================================================
        # VISTAS REQUERIDAS POR MENUS_ACTIONS
        # =========================================================

        'views/view_remote_assistance_request.xml',
        'views/view_client_counter_submission.xml',
        'views/view_toner_request.xml',
        'views/printtracker_config_views.xml',
        'views/copier_billing_group_views.xml',
        'views/copier_company_billing_group_views.xml',
        'views/copier_counter_billing_group_views.xml',

        # =========================================================
        # LIBRO DE RECLAMACIONES
        # =========================================================

        'views/libro_reclamaciones_views.xml',

        # =========================================================
        # ACCIONES Y MENÚS
        # =========================================================

        'views/menus_actions.xml',

        # =========================================================
        # VISTAS DEPENDIENTES DE ACCIONES
        # =========================================================

        'views/whatsapp_config_views.xml',
        'views/whatsapp_service_notification_views.xml',

        # =========================================================
        # WEBSITE / COMERCIAL
        # =========================================================

        'views/homepage_template.xml',
        'views/copier_about_us_views.xml',
        'views/sticker_a7_web.xml',
        'views/servicios_web.xml',
        'views/cotizaciones_multiples.xml',
        'views/template_cotizaciones.xml',
        'views/portal_servicios_cliente.xml',
        'views/public_service_tracking_templates.xml',

        # =========================================================
        # WIZARDS WHATSAPP
        # =========================================================

        'views/whatsapp_send_quotation_wizard_views.xml',
        'views/whatsapp_send_multi_quotation_wizard_views.xml',

        # =========================================================
        # REPORTES HEREDADOS / DOCUMENTOS
        # =========================================================

        'views/report_invoice_modern.xml',
        'views/report_delivery_document_modern.xml',
        'views/copier_soporte.xml',

        # =========================================================
        # PRODUCTOS
        # =========================================================

        'views/resolver_producto_page.xml',
        'views/view_product_name_alias.xml',
        'views/resolver_producto_views.xml',

        # =========================================================
        # FACTURACIÓN / ONEDRIVE
        # =========================================================

        'views/account_move_send_wizard.xml',

        # =========================================================
        # TIENDA
        # =========================================================

        'views/website_sale_modern.xml',

        # =========================================================
        # PORTAL COMERCIAL
        # =========================================================

        'views/portal_comercial_backend_views.xml',
        'views/portal_comercial_templates.xml',

        # =========================================================
        # LIBRO DE RECLAMACIONES - WEBSITE
        # =========================================================

        'views/libro_reclamaciones_website.xml',
        'views/politica_cambios_devoluciones.xml',
    ],

    # =============================================================
    # ASSETS ODOO 19
    # =============================================================

    'assets': {

        # =========================================================
        # BACKEND
        # =========================================================

        'web.assets_backend': [

            # Explorador interno de pCloud
            'copier_company/static/src/css/pcloud_explorer.css',
            'copier_company/static/src/xml/pcloud_explorer.xml',
            'copier_company/static/src/js/pcloud_explorer.js',

            # Selector OneDrive
            'copier_company/static/src/css/onedrive_selector.css',
            'copier_company/static/src/js/onedrive_selector_dialog.js',
            'copier_company/static/src/xml/onedrive_selector_dialog.xml',

            # Estilos generales backend Odoo 19
            'copier_company/static/src/scss/copier_company_odoo19.scss',
        ],

        # =========================================================
        # FRONTEND - WEBSITE Y PORTAL DE CLIENTES
        #
        # CORREGIDO PARA ODOO 19:
        # website.assets_frontend -> web.assets_frontend
        # =========================================================

        'web.assets_frontend': [

            # -----------------------------------------------------
            # Estilos generales del portal
            # -----------------------------------------------------

            'copier_company/static/src/css/counter_charts.css',
            'copier_company/static/src/css/cotizacion_styles.css',

            # -----------------------------------------------------
            # CENTRO DE DESCARGAS PCLOUD - ESTILO DROPBOX
            # -----------------------------------------------------

            'copier_company/static/src/css/PcloudDescargas.css',

            # -----------------------------------------------------
            # Otros estilos del sitio web
            # -----------------------------------------------------

            'copier_company/static/src/css/copier_list.css',
            'copier_company/static/src/scss/copier_company_shop.scss',
            'copier_company/static/src/css/portal_commercial.css',

            # -----------------------------------------------------
            # JavaScript general del portal
            # -----------------------------------------------------

            'copier_company/static/src/js/portal_commercial.js',
            'copier_company/static/src/js/manuals.js',
            'copier_company/static/src/js/counter_charts.js',

            # -----------------------------------------------------
            # CENTRO DE DESCARGAS PCLOUD - JAVASCRIPT
            # -----------------------------------------------------

            'copier_company/static/src/js/PcloudDescargas.js',

            # -----------------------------------------------------
            # Otros JavaScript del sitio web
            # -----------------------------------------------------

            'copier_company/static/src/js/cotizacion.js',
            'copier_company/static/src/js/copier_homepage_scripts.js',
            'copier_company/static/src/js/copier_services_scripts.js',

            # -----------------------------------------------------
            # Plantillas frontend
            # -----------------------------------------------------

            'copier_company/static/src/xml/counter_charts_templates.xml',

           
           
        ],

        # =========================================================
        # LIBRERÍAS FRONTEND EXISTENTES
        # =========================================================

        'website.assets_frontend_lib': [
            (
                'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
                {'type': 'external'}
            ),
        ],

        # =========================================================
        # ASSETS DE REPORTES
        # =========================================================

        'web.report_assets_common': [
            'copier_company/static/src/css/invoice_style.css',
        ],
    },

    # =============================================================
    # CONFIGURACIÓN DEL MÓDULO
    # =============================================================

    'application': True,
    'installable': True,
    'auto_install': False,
}
