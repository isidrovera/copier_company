# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Manual(models.Model):
    _name = 'secure_pdf_viewer.manual'
    _description = 'Manual PDF con visualización segura'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    pdf_file = fields.Binary(string='Archivo PDF', required=True, attachment=True)
    pdf_filename = fields.Char(string='Nombre del archivo')
    active = fields.Boolean(default=True)
    category_id = fields.Many2one('secure_pdf_viewer.category', string='Categoría')
    access_count = fields.Integer(string='Número de accesos', default=0, readonly=True)
    
    def increment_access_count(self):
        for record in self:
            record.access_count += 1
            
class Category(models.Model):
    _name = 'secure_pdf_viewer.category'
    _description = 'Categoría de manuales'
    
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    manual_ids = fields.One2many('secure_pdf_viewer.manual', 'category_id', string='Manuales')