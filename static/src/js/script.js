function searchFiles() {
    var searchTerm = document.getElementById("search").value;
    window.location.href = '/descarga/archivos?page=1&search=' + encodeURIComponent(searchTerm);
}
