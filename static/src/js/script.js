function searchFiles() {
    var input = document.getElementById("search");
    var filter = input.value;
    var url = '/descarga/archivos?page=1&search=' + encodeURIComponent(filter);
    console.log(url); // Agrega esto para depuración
    window.location = url;
}
