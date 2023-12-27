function searchFiles() {
    var input = document.getElementById("search");
    var filter = input.value;
    window.location = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter);
}
