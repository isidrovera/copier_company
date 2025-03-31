(function() {
    console.log("[Copier Company] Inicializando portal_fix.js - Versión mejorada");
    
    // Función para crear elementos faltantes de manera más robusta
    function ensureElementExists(selector, createIfMissing = true) {
        let element = document.querySelector(selector);
        
        if (!element && createIfMissing) {
            console.warn(`[Copier Company] Elemento no encontrado: ${selector}. Creando.`);
            
            element = document.createElement('div');
            if (selector.startsWith('#')) {
                element.id = selector.substring(1);
            } else if (selector.startsWith('.')) {
                element.className = selector.substring(1);
            }
            
            element.style.display = 'none';
            document.body.appendChild(element);
        }
        
        return element;
    }
    
    // Función para manejar la inicialización de elementos del portal
    function initPortalElements() {
        console.log("[Copier Company] Inicializando elementos del portal");
        
        const elementsToEnsure = [
            '#o_portal_navbar_content',
            '.o_portal_docs',
            '.o_portal_navbar',
            '#portal_my_items',
            '.o_portal_my_doc_table'
        ];
        
        elementsToEnsure.forEach(ensureElementExists);
    }
    
    // Parche para manejar textContent de manera segura
    function patchTextContentAccess() {
        const originalTextContentDescriptor = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
        
        Object.defineProperty(Node.prototype, 'textContent', {
            set: function(value) {
                if (!this) {
                    console.warn("[Copier Company] Intento de establecer textContent en un elemento nulo.");
                    return;
                }
                try {
                    originalTextContentDescriptor.set.call(this, value);
                } catch (error) {
                    console.error("[Copier Company] Error al establecer textContent:", error);
                }
            },
            get: function() {
                try {
                    return this ? originalTextContentDescriptor.get.call(this) : '';
                } catch (error) {
                    console.error("[Copier Company] Error al obtener textContent:", error);
                    return '';
                }
            },
            configurable: true
        });
    }
    
    // Aplicar parches globales
    function applyGlobalPatches() {
        // Manejar errores no capturados
        window.addEventListener('error', function(event) {
            if (event.message && event.message.includes('textContent')) {
                console.warn("[Copier Company] Error global capturado:", event);
                event.preventDefault();
                return false;
            }
        }, true);
        
        // Manejar promesas no manejadas
        window.addEventListener('unhandledrejection', function(event) {
            console.warn("[Copier Company] Promesa no manejada:", event.reason);
            event.preventDefault();
        });
    }
    
    // Inicialización
    function initialize() {
        try {
            initPortalElements();
            patchTextContentAccess();
            applyGlobalPatches();
            
            console.log("[Copier Company] Inicialización completada");
        } catch (error) {
            console.error("[Copier Company] Error en la inicialización:", error);
        }
    }
    
    // Ejecutar en diferentes etapas de carga para asegurar estabilidad
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        window.addEventListener('load', initialize);
    }
})();
