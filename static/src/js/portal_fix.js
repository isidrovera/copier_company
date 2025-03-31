/* Portal Fixes Script for Odoo 18 */
(function() {
    // Log para depuración
    console.log("[Copier Company] Inicializando portal_fix.js");
    
    // Función para suprimir errores de textContent
    function patchTextContent() {
        try {
            console.log("[Copier Company] Aplicando parche para textContent");
            var originalTextContentDescriptor = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
            
            Object.defineProperty(Node.prototype, 'textContent', {
                set: function(value) {
                    try {
                        if (this) {
                            originalTextContentDescriptor.set.call(this, value);
                        } else {
                            console.warn("[Copier Company] Intento de establecer textContent en un elemento nulo");
                        }
                    } catch (error) {
                        console.warn("[Copier Company] Error capturado al configurar textContent:", error);
                    }
                },
                get: originalTextContentDescriptor.get,
                configurable: true
            });
            console.log("[Copier Company] Parche para textContent aplicado con éxito");
        } catch (error) {
            console.error("[Copier Company] Error al aplicar parche para textContent:", error);
        }
    }
    
    // Función para crear elementos faltantes en el DOM
    function createMissingElements() {
        try {
            console.log("[Copier Company] Verificando elementos faltantes");
            var elementsToCreate = [
                'o_portal_navbar_content',
                'o_portal_navbar_content_menu',
                'o_portal_search_panel',
                'o_portal_counter_container'
            ];
            
            elementsToCreate.forEach(function(id) {
                if (!document.getElementById(id)) {
                    var div = document.createElement('div');
                    div.id = id;
                    div.style.display = 'none';
                    document.body.appendChild(div);
                    console.log("[Copier Company] Elemento creado:", id);
                } else {
                    console.log("[Copier Company] Elemento ya existe:", id);
                }
            });
            console.log("[Copier Company] Verificación de elementos faltantes completada");
        } catch (error) {
            console.error("[Copier Company] Error al crear elementos faltantes:", error);
        }
    }
    
    // Aplicar parche para textContent inmediatamente
    patchTextContent();
    
    // Crear elementos faltantes en diferentes momentos
    // 1. Inmediatamente
    createMissingElements();
    
    // 2. Cuando el DOM esté listo
    if (document.readyState === 'loading') {
        console.log("[Copier Company] DOM todavía cargando, esperando evento DOMContentLoaded");
        document.addEventListener('DOMContentLoaded', function() {
            console.log("[Copier Company] DOM cargado, ejecutando createMissingElements");
            createMissingElements();
        });
    } else {
        console.log("[Copier Company] DOM ya cargado");
    }
    
    // 3. Cuando la página haya cargado completamente
    window.addEventListener('load', function() {
        console.log("[Copier Company] Página completamente cargada, programando ejecución posterior");
        setTimeout(function() {
            console.log("[Copier Company] Ejecutando createMissingElements después de carga completa");
            createMissingElements();
        }, 200);
    });
    
    // 4. Intentar una última vez después de un tiempo
    setTimeout(function() {
        console.log("[Copier Company] Última ejecución programada de createMissingElements");
        createMissingElements();
    }, 1000);
    
    console.log("[Copier Company] Inicialización de portal_fix.js completada");
})();