/** Copier Company SAC - formulario de Google Ads (Odoo 19).
 *  DNI: contacto; RUC: empresa. Sin DNI: ingreso manual.
 *  Las consultas JSON-RPC usan el controlador existente.
 */
(function () {
    'use strict';

    function init() {
        const form = document.getElementById('copier_form');
        if (!form) {
            console.info('[COTIZACION JS] No se encontró #copier_form en esta página.');
            return;
        }
        if (form.dataset.ccInitialized === '1') return;
        form.dataset.ccInitialized = '1';

        const $ = (id) => document.getElementById(id);
        const notice = $('cc_notice');
        const searchDni = $('buscar_dni');
        const searchRuc = $('buscar_ruc');
        const manualCheck = $('manual_contacto');
        const dniInput = $('dni_contacto');
        const rucInput = $('ruc_empresa');
        const contactInput = $('contacto');
        const companyInput = $('razon_social');
        const submitBtn = $('enviar_solicitud');

        const missing = [
            ['cc_notice', notice], ['buscar_dni', searchDni],
            ['buscar_ruc', searchRuc], ['manual_contacto', manualCheck],
            ['dni_contacto', dniInput], ['ruc_empresa', rucInput],
            ['contacto', contactInput], ['razon_social', companyInput],
            ['enviar_solicitud', submitBtn],
        ].filter((item) => !item[1]).map((item) => item[0]);
        if (missing.length) {
            console.error('[COTIZACION JS] Faltan elementos en la plantilla:', missing.join(', '));
            return;
        }

        function showMessage(message, error) {
            notice.textContent = message || '';
            notice.hidden = !message;
            notice.className = error ? 'cc-notice cc-error' : 'cc-notice';
        }

        async function lookup(kind) {
            const isDni = kind === 'dni';
            const numberInput = isDni ? dniInput : rucInput;
            const targetInput = isDni ? contactInput : companyInput;
            const button = isDni ? searchDni : searchRuc;
            const number = numberInput.value.trim();
            const valid = isDni ? /^\d{8}$/.test(number) : /^\d{11}$/.test(number);
            if (!valid) {
                showMessage(isDni ? 'El DNI debe contener 8 dígitos.' : 'El RUC debe contener 11 dígitos.', true);
                numberInput.focus();
                return;
            }

            const oldText = button.textContent;
            button.disabled = true;
            button.textContent = 'Buscando...';
            showMessage(isDni ? 'Consultando DNI...' : 'Consultando RUC...', false);
            console.info('[COTIZACION JS] Iniciando consulta', kind);

            try {
                const response = await fetch('/copier_company/buscar_cliente', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: {
                            tipo_identificacion: isDni ? '1' : '6',
                            identificacion: number,
                        },
                        id: Date.now(),
                    }),
                });
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                const payload = await response.json();
                if (payload.error) {
                    console.error('[COTIZACION JS] Error JSON-RPC:', payload.error);
                    showMessage('No se pudo completar la consulta. Puede ingresar los datos manualmente.', true);
                    targetInput.readOnly = false;
                    return;
                }
                const result = payload.result || {};
                if (result.success && result.found && result.data && result.data.name) {
                    // No sobreescribir la respuesta si el usuario cambió el documento durante el fetch.
                    if (numberInput.value.trim() !== number) return;
                    targetInput.value = result.data.name;
                    targetInput.readOnly = true;
                    targetInput.dispatchEvent(new Event('input', { bubbles: true }));
                    showMessage(isDni ? 'Nombre encontrado correctamente.' : 'Razón social encontrada correctamente.', false);
                    console.info('[COTIZACION JS] Consulta correcta', kind);
                } else {
                    targetInput.readOnly = false;
                    showMessage(result.message || 'No se encontraron datos. Ingrese el nombre manualmente.', !result.success);
                    targetInput.focus();
                    console.warn('[COTIZACION JS] Consulta sin resultados', kind);
                }
            } catch (error) {
                console.error('[COTIZACION JS] Falló consulta ' + kind + ':', error);
                targetInput.readOnly = false;
                showMessage('Error de conexión. Escriba el nombre manualmente.', true);
            } finally {
                button.disabled = Boolean(isDni && manualCheck.checked);
                button.textContent = oldText;
            }
        }

        searchDni.addEventListener('click', () => lookup('dni'));
        searchRuc.addEventListener('click', () => lookup('ruc'));

        manualCheck.addEventListener('change', () => {
            const manual = manualCheck.checked;
            dniInput.disabled = manual;
            dniInput.required = !manual;
            searchDni.disabled = manual;
            contactInput.readOnly = false;
            if (manual) {
                dniInput.value = '';
                contactInput.value = '';
                contactInput.focus();
            }
            showMessage('', false);
        });

        [dniInput, rucInput].forEach((input) => {
            input.addEventListener('input', () => {
                const target = input === dniInput ? contactInput : companyInput;
                target.value = '';
                target.readOnly = false;
                showMessage('', false);
            });
        });

        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                form.reportValidity();
                return;
            }
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando solicitud...';
        });

        console.info('[COTIZACION JS] Formulario inicializado correctamente (Odoo 19).');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();
