function searchFiles() {
    var input = document.getElementById("search");
    var filter = input.value;
    // Solo realiza la búsqueda si hay un término para buscar.
    if (filter.trim().length > 0) {
        var url = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter.trim());
        console.log(url); // Para depuración
        window.location.href = url; // Asegúrate de usar window.location.href
    }
}
