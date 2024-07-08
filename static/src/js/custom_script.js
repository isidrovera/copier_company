function obtenerDatosCliente() {
    var errorElement = document.getElementById('error_message');
    var clienteName = document.getElementById('cliente_name');
    var telefono = document.getElementById('telefono');
    var correo = document.getElementById('correo');

    // Verificar que los elementos existen en el DOM
    if (!errorElement || !clienteName || !telefono || !correo) {
        console.error('Uno o más elementos del DOM no se encontraron.');
        return; // Detener ejecución si algún elemento esencial falta
    }

    // Limpiar mensaje de error previo
    errorElement.innerText = '';

    var tipoIdentificacion = document.getElementById('tipo_identificacion').value;
    var identificacion = document.getElementById('identificacion').value;
    console.log("Tipo de Identificación: ", tipoIdentificacion);
    console.log("Identificación: ", identificacion);

    if (identificacion) {
        fetch('/copier_company/get_customer_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    tipo_identificacion: tipoIdentificacion,
                    identificacion: identificacion
                },
                id: null
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Datos procesados: ", data);
            if (data.result && data.result.result && data.result.result.success) {
                console.log("Cliente encontrado: ", data.result.result.name);
                clienteName.value = data.result.result.name;
                telefono.value = data.result.result.phone;
                correo.value = data.result.result.email;
                errorElement.innerText = '';  // Limpiar cualquier mensaje de error previo
            } else {
                console.warn('No se encontraron datos:', data);
                errorElement.innerText = 'No se encontraron datos para la identificación proporcionada.';
            }
        })
        .catch(error => {
            console.error('Error al procesar la solicitud:', error);
            errorElement.innerText = 'Error al procesar la solicitud.';
        });
    } else {
        errorElement.innerText = 'Por favor, ingrese el número de identificación.';
    }
}
