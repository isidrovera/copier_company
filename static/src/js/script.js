function searchFiles() {
    var searchTerm = document.getElementById("search").value;

    // Redirigir a la URL con el término de búsqueda
    window.location.href = '/descarga/archivos?page=1&search=' + encodeURIComponent(searchTerm);
}




