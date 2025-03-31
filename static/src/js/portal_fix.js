/** @odoo-module **/

import { registry } from '@web/core/registry';
import { onMounted } from "@odoo/owl";

const fixPortalElements = {
    start() {
        onMounted(() => {
            // Función para comprobar y arreglar elementos faltantes
            const fixMissingElements = () => {
                // Crea divs vacíos para posibles elementos faltantes en el portal
                const possibleMissingIds = [
                    'o_portal_navbar_content',
                    'o_portal_navbar_content_menu',
                    'o_portal_search_panel'
                ];
                
                for (const id of possibleMissingIds) {
                    if (!document.getElementById(id)) {
                        const div = document.createElement('div');
                        div.id = id;
                        div.style.display = 'none';
                        document.body.appendChild(div);
                        console.log('Added missing element:', id);
                    }
                }
            };
            
            // Ejecutar inmediatamente
            fixMissingElements();
            
            // Y también después de que cargue completamente la página
            window.addEventListener('load', () => {
                setTimeout(fixMissingElements, 100);
            });
        });
    },
};

registry.category('website_backend_start').add('copier_company.fix_portal_elements', fixPortalElements);