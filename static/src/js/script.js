function searchFiles() {
    var input = document.getElementById("search");
    var searchTerm = input.value;
    
    // Construir la URL para la solicitud
    var url = "/descarga/archivos?page=1&search=" + encodeURIComponent(searchTerm);

    // Realizar la solicitud al servidor
    window.location.href = url;
}





