let debounceTimeout = null;

function searchFiles() {
    if (debounceTimeout) {
        clearTimeout(debounceTimeout);
    }
    
    debounceTimeout = setTimeout(function() {
        var input = document.getElementById("search");
        var filter = input.value;
        if (filter.length > 1) { // Asegúrate de tener al menos 2 caracteres antes de buscar
            var url = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter);
            console.log(url); // Para depuración
            window.location = url;
        }
    }, 500); // Espera 500 ms después de que el usuario haya dejado de escribir
}
