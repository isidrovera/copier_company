# -*- coding: utf-8 -*-
# from odoo import http


# class CopierCompany(http.Controller):
#     @http.route('/copier_company/copier_company', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/copier_company/copier_company/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('copier_company.listing', {
#             'root': '/copier_company/copier_company',
#             'objects': http.request.env['copier_company.copier_company'].search([]),
#         })

#     @http.route('/copier_company/copier_company/objects/<model("copier_company.copier_company"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('copier_company.object', {
#             'object': obj
#         })
