# -*- coding: utf-8 -*-
from odoo import models, fields

class PreacherSpecialization(models.Model):
    _name = 'preacher.specialization'
    _description = 'Preacher Specialization'
    _order = 'name'

    name = fields.Char(string='Specialization Name', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Specialization name must be unique!')
    ]
