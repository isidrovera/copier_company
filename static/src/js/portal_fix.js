/* Portal Fixes Script for Odoo 18 - Enhanced Error Handling */
(function() {
    console.log("[Copier Company] Inicializando portal_fix.js - Versión mejorada");
    
    // Función para identificar el elemento problemático
    function monitorTextContentAccess() {
        try {
            console.log("[Copier Company] Monitoreando accesos a textContent");
            
            // Sobreescribir querySelector y querySelectorAll para detectar elementos que podrían causar problemas
            const originalQuerySelector = Element.prototype.querySelector;
            Element.prototype.querySelector = function(selector) {
                const result = originalQuerySelector.call(this, selector);
                if (!result && selector.includes('o_portal')) {
                    console.warn("[Copier Company] querySelector falló para:", selector, "en:", this);
                }
                return result;
            };
            
            // Patch más agresivo para textContent
            var originalTextContentDescriptor = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
            
            Object.defineProperty(Node.prototype, 'textContent', {
                set: function(value) {
                    if (!this) {
                        console.warn("[Copier Company] Intento de establecer textContent en elemento nulo", new Error().stack);
                        return; // Evitar la excepción por completo
                    }
                    try {
                        originalTextContentDescriptor.set.call(this, value);
                    } catch (error) {
                        console.warn("[Copier Company] Error capturado al establecer textContent:", error, "Elemento:", this, "Stack:", error.stack);
                        // Crear un proxy para este elemento
                        try {
                            // Intento de recuperación
                            this.innerText = value;
                        } catch (innerError) {
                            // Ignorar error adicional
                        }
                    }
                },
                get: function() {
                    if (!this) {
                        console.warn("[Copier Company] Intento de leer textContent de elemento nulo");
                        return '';
                    }
                    try {
                        return originalTextContentDescriptor.get.call(this);
                    } catch (error) {
                        console.warn("[Copier Company] Error capturado al leer textContent:", error);
                        return '';
                    }
                },
                configurable: true
            });
            
            // Parche global para manejar errores no capturados
            window.addEventListener('error', function(event) {
                if (event.message && event.message.includes('textContent')) {
                    console.log("[Copier Company] Error global capturado relacionado con textContent:", event);
                    event.preventDefault();
                    return false;
                }
            }, true);
            
            console.log("[Copier Company] Monitoreo de textContent configurado con éxito");
        } catch (error) {
            console.error("[Copier Company] Error al configurar monitoreo:", error);
        }
    }
    
    // Crear una amplia variedad de elementos potencialmente faltantes
    function createPortalElements() {
        try {
            console.log("[Copier Company] Creando elementos del portal");
            
            const elementsToCreate = [
                // Elementos generales del portal
                'o_portal_navbar_content', 
                'o_portal_navbar_content_menu',
                'o_portal_search_panel',
                'o_portal_counter_container',
                
                // Elementos específicos de tickets y equipos
                'portal_my_items',
                'o_portal_sidebar',
                'o_portal_equipment_content',
                'o_my_sidebar',
                'o_portal_pager',
                'o_portal_my_doc_table',
                'o_my_equipment',
                'o_my_tickets'
            ];
            
            // También crear clases comunes como divs vacíos
            const commonClasses = [
                'o_portal_docs',
                'o_portal_items',
                'o_portal_equipment_list',
                'o_portal_navbar'
            ];
            
            elementsToCreate.forEach(function(id) {
                if (!document.getElementById(id)) {
                    const div = document.createElement('div');
                    div.id = id;
                    div.style.display = 'none';
                    div.setAttribute('data-fix', 'created-by-portal-fix');
                    document.body.appendChild(div);
                    console.log("[Copier Company] Elemento creado:", id);
                }
            });
            
            commonClasses.forEach(function(className) {
                if (document.getElementsByClassName(className).length === 0) {
                    const div = document.createElement('div');
                    div.className = className;
                    div.style.display = 'none';
                    div.setAttribute('data-fix', 'created-by-portal-fix');
                    document.body.appendChild(div);
                    console.log("[Copier Company] Elemento con clase creado:", className);
                }
            });
            
            console.log("[Copier Company] Elementos del portal creados");
        } catch (error) {
            console.error("[Copier Company] Error al crear elementos:", error);
        }
    }
    
    // Aplicar todas las soluciones
    monitorTextContentAccess();
    createPortalElements();
    
    // Ejecutar nuevamente después de que DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        console.log("[Copier Company] DOM cargado");
        createPortalElements();
    });
    
    // Una última vez después de que todo esté cargado
    window.addEventListener('load', function() {
        console.log("[Copier Company] Página completamente cargada");
        setTimeout(createPortalElements, 200);
    });
    
    console.log("[Copier Company] Inicialización completada");
})();