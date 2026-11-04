/* Copier Company | Portal de descargas Odoo 19. Script simple para web.assets_frontend. */
(function () {
  'use strict';
  function ready() {
    const root = document.getElementById('cc-drive');
    if (!root || root.dataset.ready === '1') return;
    root.dataset.ready = '1';
    const $ = (s) => root.querySelector(s);
    const items = $('#cc-items'), count = $('#cc-count'), empty = $('#cc-empty');
    const input = $('#cc-search'), status = $('#cc-search-status'), form = $('#cc-search-form');
    const modal = $('#cc-modal'), preview = $('#cc-preview'), title = $('#cc-modal-name');
    let searchTimer, activeRequest, requestNumber = 0;
    const startingMarkup = items.innerHTML;
    let view = 'list';
    try { view = localStorage.getItem('cc_drive_view') || 'list'; } catch (_) {}
    function setView(next) {
      view = next === 'grid' ? 'grid' : 'list';
      items.classList.toggle('cc-grid-mode', view === 'grid');
      items.classList.toggle('cc-list-mode', view === 'list');
      $('#cc-grid-button').classList.toggle('active', view === 'grid');
      $('#cc-list-button').classList.toggle('active', view === 'list');
      try { localStorage.setItem('cc_drive_view', view); } catch (_) {}
    }
    $('#cc-grid-button').addEventListener('click', () => setView('grid'));
    $('#cc-list-button').addEventListener('click', () => setView('list'));
    setView(view);
    const normalized = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const fileUrl = (id, previewMode) => (previewMode ? '/soporte/vista-previa' : '/soporte/descarga') + '?file_id=' + encodeURIComponent(id);
    function refreshCount() {
      const n = items.querySelectorAll('.cc-entry').length;
      count.textContent = n + (n === 1 ? ' elemento' : ' elementos');
      empty.hidden = n !== 0;
    }
    const create = (tag, cls, text) => {
      const el = document.createElement(tag);
      if (cls) el.className = cls;
      if (text !== undefined) el.textContent = text;
      return el;
    };
    function draw(data) {
      items.replaceChildren();
      data.forEach((item) => {
        if (item.id === null || item.id === undefined) return;
        const row = create('div', 'cc-entry');
        Object.assign(row.dataset, { id: String(item.id), folder: item.isfolder ? '1' : '0', name: item.name || '', modified: item.modified || '', size: item.size || '', path: item.path || '' });
        const main = create('button', 'cc-entry-main'); main.type = 'button';
        const symbol = create('span', 'cc-file-symbol ' + (item.isfolder ? 'cc-is-folder' : 'cc-is-file'));
        symbol.appendChild(create('i', 'fa ' + (item.isfolder ? 'fa-folder' : 'fa-file-o')));
        const info = create('span', 'cc-entry-info');
        const name = create('strong', '', item.name || ''); name.title = item.name || '';
        info.append(name, create('small', '', item.path || (item.isfolder ? 'Carpeta' : 'Archivo')));
        main.append(symbol, info);
        const date = create('span', 'cc-entry-date', item.modified || '');
        const size = create('span', 'cc-entry-size', item.size || '—');
        const actions = create('span', 'cc-entry-actions');
        if (item.isfolder) { actions.appendChild(create('i', 'fa fa-angle-right')); }
        else {
          const a = create('a', 'cc-download-link'); a.href = fileUrl(item.id, false); a.title = 'Descargar';
          a.appendChild(create('i', 'fa fa-download')); actions.appendChild(a);
        }
        row.append(main, date, size, actions); items.appendChild(row);
      });
      refreshCount();
    }
    function closeModal() {
      modal.hidden = true; preview.replaceChildren(); document.body.style.overflow = '';
    }
    function showMessage(message) { preview.replaceChildren(create('p', '', message)); }
    async function openFile(row) {
      const id = row.dataset.id, name = row.dataset.name || 'Archivo';
      title.textContent = name;
      $('#cc-modal-detail').textContent = [row.dataset.size, row.dataset.modified].filter(Boolean).join(' · ');
      $('#cc-modal-download').href = fileUrl(id, false);
      modal.hidden = false; document.body.style.overflow = 'hidden';
      showMessage('Preparando vista previa…');
      const ext = name.split('.').pop().toLowerCase();
      const type = ['png','jpg','jpeg','gif','webp'].includes(ext) ? 'image' : ext === 'pdf' ? 'pdf' : ['txt','log','csv'].includes(ext) ? 'text' : ['mp4','webm','ogg'].includes(ext) ? 'video' : 'other';
      if (type === 'other') { showMessage('No hay vista previa para este formato. Puedes descargar el archivo.'); return; }
      const url = fileUrl(id, true);
      try {
        const response = await fetch(url, { method: 'HEAD', credentials: 'same-origin', cache: 'no-store' });
        if (!response.ok) throw Error('Vista previa no disponible');
        if (modal.hidden || $('#cc-modal-download').href !== new URL(fileUrl(id, false), location.href).href) return;
        preview.replaceChildren();
        if (type === 'image') {
          const img = create('img'); img.alt = name; img.src = url;
          img.onerror = () => showMessage('No se pudo mostrar la imagen. Puedes descargar el archivo.'); preview.appendChild(img);
        } else if (type === 'pdf') {
          const frame = create('iframe'); frame.title = name; frame.src = url; preview.appendChild(frame);
        } else if (type === 'video') {
          const video = create('video'); video.controls = true; video.src = url; preview.appendChild(video);
        } else {
          const res = await fetch(url, { credentials: 'same-origin' });
          if (!res.ok) throw Error('Vista previa no disponible');
          const text = await res.text(); preview.appendChild(create('pre', '', text.slice(0, 100000)));
        }
      } catch (err) { showMessage('No se pudo obtener una vista previa. Puedes descargar el archivo.'); }
    }
    items.addEventListener('click', (event) => {
      if (event.target.closest('.cc-download-link')) return;
      const main = event.target.closest('.cc-entry-main');
      if (!main) return;
      const row = main.closest('.cc-entry');
      if (row.dataset.folder === '1') {
        location.href = '/soporte/descargas?folder_id=' + encodeURIComponent(row.dataset.id);
      } else openFile(row);
    });
    $('#cc-close').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => { if (e.target.dataset.close === '1') closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.hidden) closeModal(); });
    function localFilter(term) {
      items.querySelectorAll('.cc-entry').forEach((row) => {
        row.hidden = !normalized(row.dataset.name).includes(normalized(term));
      });
      const visible = items.querySelectorAll('.cc-entry:not([hidden])').length;
      count.textContent = visible + (visible === 1 ? ' elemento' : ' elementos');
      empty.hidden = visible !== 0;
    }
    function reset() { items.innerHTML = startingMarkup; status.textContent = ''; refreshCount(); }
    async function remoteSearch(term, number) {
      activeRequest?.abort();
      const controller = new AbortController(); activeRequest = controller;
      status.textContent = 'Buscando en todas las carpetas…';
      try {
        const response = await fetch('/soporte/descargas/buscar?search=' + encodeURIComponent(term), {
          credentials: 'same-origin', signal: controller.signal, headers: { Accept: 'application/json' }
        });
        if (!response.ok) throw Error('HTTP ' + response.status);
        const result = await response.json();
        if (number !== requestNumber || input.value.trim() !== term) return;
        if (!Array.isArray(result.items)) throw Error('Respuesta inválida');
        draw(result.items);
        status.textContent = result.truncated ? 'Resultados parciales: búsqueda interrumpida.' : 'Búsqueda global finalizada';
        $('#cc-heading').textContent = 'Resultados de búsqueda';
      } catch (error) {
        if (error.name !== 'AbortError') status.textContent = 'No se pudo completar la búsqueda. Inténtalo nuevamente.';
      }
    }
    function onSearch() {
      clearTimeout(searchTimer); activeRequest?.abort(); const number = ++requestNumber;
      const term = input.value.trim();
      if (!term) { $('#cc-heading').textContent = 'Contenido'; reset(); return; }
      localFilter(term);
      status.textContent = 'Buscando…';
      searchTimer = setTimeout(() => remoteSearch(term, number), 400);
    }
    input.addEventListener('input', onSearch);
    $('#cc-clear').addEventListener('click', () => { input.value = ''; onSearch(); input.focus(); });
    form.addEventListener('submit', (event) => { event.preventDefault(); onSearch(); });
    refreshCount();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready, { once: true });
  else ready();
})();
