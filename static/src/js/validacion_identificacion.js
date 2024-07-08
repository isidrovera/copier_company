function validarIdentificacion() {
    var tipoIdentificacion = document.getElementById('tipo_identificacion').value;
    var identificacion = document.getElementById('identificacion').value;
    var errorMessage = document.getElementById('error_message');
    errorMessage.innerHTML = '';

    if (tipoIdentificacion === 'RUC' && identificacion.length === 8) {
        errorMessage.innerHTML = 'El número de RUC debe tener 11 dígitos. Seleccione DNI si corresponde.';
        return false;
    } else if (tipoIdentificacion === 'DNI' && identificacion.length === 11) {
        errorMessage.innerHTML = 'El número de DNI debe tener 8 dígitos. Seleccione RUC si corresponde.';
        return false;
    } else if (tipoIdentificacion === 'RUC' && identificacion.length !== 11) {
        errorMessage.innerHTML = 'El número de RUC debe tener 11 dígitos.';
        return false;
    } else if (tipoIdentificacion === 'DNI' && identificacion.length !== 8) {
        errorMessage.innerHTML = 'El número de DNI debe tener 8 dígitos.';
        return false;
    }
    return true;
}

document.getElementById('copier_form').addEventListener('submit', function(event) {
    if (!validarIdentificacion()) {
        event.preventDefault();
    }
});
