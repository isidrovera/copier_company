let debounceTimeout = null;

function searchFiles() {
    clearTimeout(debounceTimeout); // Cancela cualquier timeout anterior
    debounceTimeout = setTimeout(function () {
        var input = document.getElementById("search");
        var filter = input.value;
        var url = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter);
        console.log(url); // Para depuración
        window.location = url;
    }, 500); // Espera 500 ms después de la última tecla presionada para iniciar la búsqueda
}
