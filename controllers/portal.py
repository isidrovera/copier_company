from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR, AND

class CopierCompanyPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        if 'equipment_count' in counters:
            equipment_count = request.env['copier.company'].search_count([
                ('cliente_id', '=', partner.id)
            ])
            values['equipment_count'] = equipment_count
            
        return values
        
    @http.route(['/my/copier/equipments', '/my/copier/equipments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipment(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='name', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        CopierCompany = request.env['copier.company']
        
        domain = [('cliente_id', '=', partner.id)]
        
        # Búsqueda
        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Máquina')},
            'serie': {'input': 'serie_id', 'label': _('Serie')},
        }
        
        # Filtros
        searchbar_filters = {
            'all': {'label': _('Todos'), 'domain': domain},
            'active': {'label': _('Contratos Activos'), 'domain': AND([domain, [('estado_renovacion', 'in', ['vigente', 'por_vencer'])]])},
            'color': {'label': _('Impresoras Color'), 'domain': AND([domain, [('tipo', '=', 'color')]])},
            'bw': {'label': _('Impresoras B/N'), 'domain': AND([domain, [('tipo', '=', 'monocroma')]])},
        }
        
        # Ordenamiento
        searchbar_sortings = {
            'date': {'label': _('Fecha'), 'order': 'create_date desc'},
            'name': {'label': _('Máquina'), 'order': 'name'},
            'estado': {'label': _('Estado'), 'order': 'estado_renovacion'},
        }
        
        # Valor por defecto
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']
        
        # Búsqueda
        if search and search_in:
            search_domain = []
            if search_in == 'name':
                search_domain = [('name.name', 'ilike', search)]
            elif search_in == 'serie':
                search_domain = [('serie_id', 'ilike', search)]
            domain = AND([domain, search_domain])
        
        # Contar equipos
        equipment_count = CopierCompany.search_count(domain)
        
        # Paginación
        pager = portal_pager(
            url="/my/copier/equipments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=equipment_count,
            page=page,
            step=self._items_per_page
        )
        
        # Obtener equipos
        equipments = CopierCompany.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'equipments': equipments,
            'page_name': 'equipment',
            'pager': pager,
            'default_url': '/my/copier/equipments',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'filterby': filterby,
        })
        
        return request.render("copier_company.portal_my_copier_equipments", values)
        
    @http.route(['/my/copier/equipment/<int:equipment_id>'], type='http', auth="user", website=True)
    def portal_my_equipment_detail(self, equipment_id, **kw):
        try:
            equipment_sudo = self._document_check_access('copier.company', equipment_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'equipment': equipment_sudo,
            'page_name': 'equipment_detail',
        })
        
        return request.render("copier_company.portal_my_copier_equipment", values)
        
    @http.route(['/my/copier/equipment/<int:equipment_id>/ticket'], type='http', auth="user", website=True)
    def portal_create_equipment_ticket(self, equipment_id, **kw):
        try:
            equipment_sudo = self._document_check_access('copier.company', equipment_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        # Redirect to helpdesk ticket creation with pre-filled values
        return request.redirect(f'/helpdesk/ticket/submit?equipment_id={equipment_id}')
        
    @http.route(['/my/copier/equipment/<int:equipment_id>/counters'], type='http', auth="user", website=True)
    def portal_equipment_counters(self, equipment_id, **kw):
        try:
            equipment_sudo = self._document_check_access('copier.company', equipment_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = self._prepare_portal_layout_values()
        counters = request.env['copier.counter'].search([
            ('maquina_id', '=', equipment_id)
        ], order='fecha_lectura desc')
        
        values.update({
            'equipment': equipment_sudo,
            'counters': counters,
            'page_name': 'equipment_counters',
        })
        
        return request.render("copier_company.portal_my_copier_counters", values)