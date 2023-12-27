function searchFiles() {
    var input = document.getElementById("search");
    var filter = input.value;
    // Realiza la búsqueda solo si hay un término para buscar.
    if (filter.trim().length > 0) {
        var url = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter.trim());
        window.location.href = url;
    }
}
