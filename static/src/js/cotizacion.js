
/** Copier Company SAC - formulario rápido (Odoo 19). */
(function () {
    'use strict';
    const form = document.getElementById('copier_form');
    if (!form) return;

    const $ = (id) => document.getElementById(id);
    const notice = $('cc_notice');
    const setNotice = (message, bad = false) => {
        notice.textContent = message || '';
        notice.hidden = !message;
        notice.className = 'cc-notice' + (bad ? ' cc-error' : '');
    };

    async function lookup(kind) {
        const dni = kind === 'dni';
        const numberInput = $(dni ? 'dni_contacto' : 'ruc_empresa');
        const target = $(dni ? 'contacto' : 'razon_social');
        const button = $(dni ? 'buscar_dni' : 'buscar_ruc');
        const number = numberInput.value.trim();
        const pattern = dni ? /^\d{8}$/ : /^\d{11}$/;
        if (!pattern.test(number)) {
            setNotice(dni ? 'El DNI debe tener 8 dígitos.' : 'El RUC debe tener 11 dígitos.', true);
            return;
        }
        button.disabled = true;
        setNotice('Buscando información...');
        try {
            const response = await fetch('/copier_company/buscar_cliente', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0', method: 'call', id: Date.now(),
                    params: {
                        tipo_identificacion: dni ? '1' : '6',
                        identificacion: number
                    },
                }),
            });
            if (!response.ok) throw new Error('Error de conexión');
            const payload = await response.json();
            const result = payload.result || {};
            if (result.found && result.data && result.data.name) {
                target.value = result.data.name;
                target.readOnly = true;
                setNotice('Datos encontrados correctamente.');
            } else {
                target.readOnly = false;
                target.focus();
                setNotice(result.message || 'No encontramos datos. Escriba el nombre manualmente.');
            }
        } catch (err) {
            target.readOnly = false;
            setNotice('No se pudo consultar el documento. Ingrese el nombre manualmente.', true);
        } finally {
            button.disabled = false;
        }
    }

    $('buscar_dni').addEventListener('click', () => lookup('dni'));
    $('buscar_ruc').addEventListener('click', () => lookup('ruc'));

    $('manual_contacto').addEventListener('change', function () {
        const manual = this.checked;
        $('dni_contacto').disabled = manual;
        $('dni_contacto').required = !manual;
        $('buscar_dni').disabled = manual;
        $('contacto').readOnly = false;
        if (manual) {
            $('dni_contacto').value = '';
            $('contacto').focus();
        }
        setNotice('');
    });

    ['dni_contacto', 'ruc_empresa'].forEach((id) => {
        $(id).addEventListener('input', function () {
            const target = $(id === 'dni_contacto' ? 'contacto' : 'razon_social');
            target.value = '';
            target.readOnly = false;
            setNotice('');
        });
    });

    form.addEventListener('submit', (event) => {
        if (!form.checkValidity()) {
            event.preventDefault();
            form.reportValidity();
            return;
        }
        $('enviar_solicitud').disabled = true;
        $('enviar_solicitud').textContent = 'Enviando solicitud...';
    });
})();
