/** @odoo-module **/

import { onWillStart } from "@odoo/owl";

// Función para crear elementos que faltan en el DOM
function createMissingElements() {
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
}

// Hook para ejecutar la función
onWillStart(() => {
    document.addEventListener('DOMContentLoaded', () => {
        createMissingElements();
        
        // También ejecutar después de que la página haya cargado completamente
        window.addEventListener('load', () => {
            setTimeout(createMissingElements, 100);
        });
    });
});