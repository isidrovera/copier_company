document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var filesList = document.getElementById('files-list');
    var listViewBtn = document.getElementById('list-view-btn');
    var kanbanViewBtn = document.getElementById('kanban-view-btn');
    var listView = document.getElementById('list-view');
    var kanbanView = document.getElementById('kanban-view');
    var viewMode = localStorage.getItem('viewMode') || 'list';
    var modifiedHeader = document.getElementById('modified-header');
    var sortIcon = document.getElementById('sort-icon');
    var ascending = true;

    function setViewMode(mode) {
        if (mode === 'list') {
            listView.classList.remove('d-none');
            kanbanView.classList.add('d-none');
            listViewBtn.classList.add('active');
            kanbanViewBtn.classList.remove('active');
        } else {
            listView.classList.add('d-none');
            kanbanView.classList.remove('d-none');
            listViewBtn.classList.remove('active');
            kanbanViewBtn.classList.add('active');
        }
        localStorage.setItem('viewMode', mode);
    }

    listViewBtn.addEventListener('click', function() {
        setViewMode('list');
    });

    kanbanViewBtn.addEventListener('click', function() {
        setViewMode('kanban');
    });

    searchInput.addEventListener('input', function() {
        var searchTerm = searchInput.value.toLowerCase();
        var rows = filesList.getElementsByTagName('tr');
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            var fileName = row.getElementsByTagName('td')[0].innerText.toLowerCase();
            if (fileName.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }

        var cards = kanbanView.getElementsByClassName('card');
        for (var i = 0; i < cards.length; i++) {
            var card = cards[i];
            var fileName = card.getElementsByClassName('card-title')[0].innerText.toLowerCase();
            if (fileName.includes(searchTerm)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        }
    });

    modifiedHeader.addEventListener('click', function() {
        var rows = Array.from(filesList.getElementsByTagName('tr'));
        rows.sort(function(a, b) {
            var dateA = new Date(a.getElementsByTagName('td')[2].innerText);
            var dateB = new Date(b.getElementsByTagName('td')[2].innerText);
            return ascending ? dateA - dateB : dateB - dateA;
        });

        ascending = !ascending;
        sortIcon.className = ascending ? 'fa fa-arrow-up' : 'fa fa-arrow-down';

        rows.forEach(function(row) {
            filesList.appendChild(row);
        });
    });

    setViewMode(viewMode);
});
