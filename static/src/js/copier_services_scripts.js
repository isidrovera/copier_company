// copier_services_scripts.js - Controla el modal de servicios (Odoo 19 - frontend)
(function () {
  'use strict';

  function html(strings, ...vals){ return strings.map((s,i)=>s+(vals[i]??'')).join(''); }

  const CONTENT = {
    alquiler: html`
      <h3 class="h4 fw-bold text-primary mb-3"><i class="bi bi-handshake me-2"></i>Alquiler de Fotocopiadoras</h3>
      <p>Ideal para empresas que buscan <strong>cero inversión inicial</strong> y costos predecibles. Incluye instalación, mantenimiento, repuestos y tóner.</p>
      <ul class="list-unstyled mb-3">
        <li>• Equipos A3/A4, B/N y Color (Konica Minolta, Canon, Ricoh)</li>
        <li>• <strong>SLA</strong>: 4h on-site, 24/7 soporte</li>
        <li>• Reemplazo de equipo en 24h si aplica</li>
      </ul>
      <div class="alert alert-primary">Desde <strong>$149/mes</strong> según volumen y funciones.</div>
    `,
    venta: html`
      <h3 class="h4 fw-bold text-success mb-3"><i class="bi bi-cart3 me-2"></i>Venta de Equipos Nuevos/Seminuevos</h3>
      <p>Te ayudamos a elegir el equipo correcto y ofrecemos <strong>financiamiento</strong> y garantía oficial.</p>
      <div class="row g-2">
        <div class="col-6"><div class="d-flex align-items-center"><i class="bi bi-check-circle-fill text-success me-2"></i><small>Entrega e instalación</small></div></div>
        <div class="col-6"><div class="d-flex align-items-center"><i class="bi bi-check-circle-fill text-success me-2"></i><small>Capacitación</small></div></div>
        <div class="col-6"><div class="d-flex align-items-center"><i class="bi bi-check-circle-fill text-success me-2"></i><small>Garantía oficial</small></div></div>
        <div class="col-6"><div class="d-flex align-items-center"><i class="bi bi-check-circle-fill text-success me-2"></i><small>Soporte post-venta</small></div></div>
      </div>
    `,
    tecnico: html`
      <h3 class="h4 fw-bold text-warning mb-3"><i class="bi bi-tools me-2"></i>Servicio Técnico Especializado</h3>
      <p>Mantenimiento preventivo y correctivo por técnicos certificados. Reporte técnico y repuestos originales.</p>
      <div class="list-group">
        <div class="list-group-item d-flex justify-content-between"><span><i class="bi bi-calendar-check text-warning me-2"></i>Preventivo</span><strong>Mensual/Trimestral</strong></div>
        <div class="list-group-item d-flex justify-content-between"><span><i class="bi bi-wrench-adjustable text-warning me-2"></i>Correctivo</span><strong>4h on-site</strong></div>
        <div class="list-group-item d-flex justify-content-between"><span><i class="bi bi-cpu text-warning me-2"></i>Firmware & Calibración</span><strong>Incluido</strong></div>
      </div>
    `,
    repuestos: html`
      <h3 class="h4 fw-bold text-info mb-3"><i class="bi bi-box-seam me-2"></i>Repuestos y Tóner</h3>
      <p>Stock permanente de consumibles y repuestos para las principales marcas.</p>
      <ul class="mb-0">
        <li>Tóneres originales y compatibles certificados</li>
        <li>Unidades de imagen, fusores, rodillos, etc.</li>
        <li>Despacho el mismo día (según disponibilidad)</li>
      </ul>
    `,
    monitoreo: html`
      <h3 class="h4 fw-bold text-danger mb-3"><i class="bi bi-graph-up-arrow me-2"></i>Monitoreo de Flota (MPS)</h3>
      <p>Plataforma 24/7 para contadores, alertas y niveles de tóner. <strong>Reportes</strong> y <strong>automatización</strong> de reposición.</p>
      <div class="row g-2">
        <div class="col-6"><div class="badge bg-danger-subtle text-danger d-block py-2">Alertas proactivas</div></div>
        <div class="col-6"><div class="badge bg-danger-subtle text-danger d-block py-2">Panel en tiempo real</div></div>
      </div>
    `
  };

  document.addEventListener('click', function (ev) {
    const card = ev.target.closest('[data-service]');
    if (!card) return;
    const key = card.getAttribute('data-service');
    const titleMap = {
      alquiler: 'Alquiler de Fotocopiadoras',
      venta: 'Venta de Equipos',
      tecnico: 'Servicio Técnico',
      repuestos: 'Repuestos y Tóner',
      monitoreo: 'Monitoreo de Flota'
    };
    const title = titleMap[key] || 'Detalles del Servicio';
    const body = CONTENT[key] || '<p>Información no disponible.</p>';
    const label = document.getElementById('serviceModalLabel');
    const content = document.getElementById('serviceModalBody');
    if (label && content){
      label.innerHTML = '<i class=\"bi bi-info-circle me-2\"></i>' + title;
      content.innerHTML = body;
    }
  });
})();