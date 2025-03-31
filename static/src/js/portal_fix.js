/**
 * Copier Company Portal Fix
 * Prevents errors related to textContent property on null elements
 * Version: 1.0.1
 */
(function() {
    console.log("[Copier Company] Inicializando portal_fix.js - Versión 1.0.1");
    
    // Función para crear elementos faltantes de manera segura
    function ensureElementExists(selector, parentSelector = 'body', createIfMissing = true) {
        const parent = document.querySelector(parentSelector) || document.body;
        let element = document.querySelector(selector);
        
        if (!element && createIfMissing) {
            console.warn(`[Copier Company] Elemento no encontrado: ${selector}. Creando.`);
            
            // Crear elemento
            element = document.createElement('div');
            if (selector.startsWith('#')) {
                element.id = selector.substring(1);
            } else if (selector.startsWith('.')) {
                element.className = selector.substring(1);
            }
            
            // Marcar como elemento de reserva
            element.setAttribute('data-copier-fallback', 'true');
            element.style.display = 'none';
            
            // Añadir al DOM
            parent.appendChild(element);
        }
        
        return element;
    }
    
    // Función para manejar la inicialización de elementos del portal
    function initPortalElements() {
        console.log("[Copier Company] Inicializando elementos del portal");
        
        // Elementos críticos del portal
        ensureElementExists('#o_portal_navbar_content', 'header');
        ensureElementExists('.o_portal_docs', 'main');
        ensureElementExists('#portal_service_category', '.o_portal_docs');
        
        // Elementos específicos de la sección equipos
        if (window.location.pathname.includes('/my/copier/equipment')) {
            ensureElementExists('.o_portal_my_doc_table', 'main');
        }
    }
    
    // Parche para manejar textContent de manera segura
    function patchTextContentAccess() {
        // Guardar el descriptor original
        const originalTextContentDescriptor = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
        
        // Reemplazar con versión segura
        Object.defineProperty(Node.prototype, 'textContent', {
            set: function(value) {
                if (this === null || this === undefined) {
                    console.warn("[Copier Company] Intento de establecer textContent en un elemento nulo");
                    return;
                }
                
                try {
                    return originalTextContentDescriptor.set.call(this, value);
                } catch (error) {
                    console.error("[Copier Company] Error al establecer textContent:", error);
                }
            },
            get: function() {
                if (this === null || this === undefined) {
                    console.warn("[Copier Company] Intento de leer textContent de un elemento nulo");
                    return '';
                }
                
                try {
                    return originalTextContentDescriptor.get.call(this);
                } catch (error) {
                    console.error("[Copier Company] Error al obtener textContent:", error);
                    return '';
                }
            },
            configurable: true
        });
    }
    
    // Parche para funciones de Odoo relacionadas con renderizado del portal
    function patchOdooPortalFunctions() {
        // Si el objeto portal existe
        if (window.odoo && window.odoo.portal) {
            const originalUpdateRightmenu = window.odoo.portal.updateRightMenu;
            
            // Sobreescribir updateRightMenu para hacerlo más seguro
            window.odoo.portal.updateRightMenu = function() {
                try {
                    // Asegurar que los elementos existan antes de llamar a la función original
                    ensureElementExists('#o_portal_navbar_content', 'header');
                    return originalUpdateRightmenu.apply(this, arguments);
                } catch (error) {
                    console.error("[Copier Company] Error en updateRightMenu:", error);
                }
            };
        }
    }
    
    // Manejar errores no capturados
    function setupErrorHandlers() {
        window.addEventListener('error', function(event) {
            if (event.message && (
                event.message.includes('textContent') || 
                event.message.includes('Cannot set properties of null')
            )) {
                console.warn("[Copier Company] Error prevenido:", event.message);
                event.preventDefault();
                return true; // Prevenir propagación
            }
        }, true);
        
        window.addEventListener('unhandledrejection', function(event) {
            if (event.reason && event.reason.message && (
                event.reason.message.includes('textContent') ||
                event.reason.message.includes('Cannot set properties of null')
            )) {
                console.warn("[Copier Company] Promesa no manejada prevenida:", event.reason.message);
                event.preventDefault();
            }
        });
    }
    
    // Inicialización completa
    function initialize() {
        try {
            // Aplicar todos los parches y mejoras
            setupErrorHandlers();
            patchTextContentAccess();
            initPortalElements();
            patchOdooPortalFunctions();
            
            // Reintento después de la carga completa
            setTimeout(initPortalElements, 500);
            
            console.log("[Copier Company] Inicialización completada con éxito");
        } catch (error) {
            console.error("[Copier Company] Error en la inicialización:", error);
        }
    }
    
    // Ejecutar en diferentes etapas para máxima compatibilidad
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
        // Segundo intento después de que todo esté cargado
        window.addEventListener('load', function() {
            setTimeout(initPortalElements, 1000);
        });
    }
})();