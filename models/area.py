# -*- coding: utf-8 -*-
from odoo import models, fields

class Area(models.Model):
    _name = 'area.area'
    _description = 'Geographical Area'
    _order = 'name'

    name = fields.Char(string='Area Name', required=True)
    parent_id = fields.Many2one('area.area', string='Parent Area', index=True, ondelete='cascade')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Area name must be unique!')
    ]

    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
