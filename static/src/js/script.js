function searchFiles() {
    var input = document.getElementById("search");
    var filter = input.value;
    if (filter.trim()) { // Asegúrate de que la cadena no esté vacía
        var url = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter.trim());
        console.log(url); // Para depuración
        window.location = url;
    }
}
