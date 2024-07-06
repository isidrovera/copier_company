function obtenerDatosCliente() {
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
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Datos procesados: ", data);
            if (data.result && data.result.success) {
                document.getElementById('cliente_name').value = data.result.name;
                document.getElementById('telefono').value = data.result.phone;
                document.getElementById('correo').value = data.result.email;
            } else {
                alert('No se encontraron datos para la identificación proporcionada.');
            }
        })
        .catch(error => {
            console.error('Error fetching data: ', error);
            alert('Error al procesar la solicitud.');
        });
    } else {
        alert('Por favor, ingrese el número de identificación.');
    }
}
