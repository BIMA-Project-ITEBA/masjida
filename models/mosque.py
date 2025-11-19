# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Mosque(models.Model):
    _name = 'mosque.mosque'
    _description = 'Mosque Master Data Model'

    code = fields.Char(string='code', required=True)
    name = fields.Char(string='Mosque Name', required=True)
    image = fields.Image(string='Mosque Photo', max_width=1024, max_height=1024)
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    province = fields.Char(string='Province')
    zip_code = fields.Char(string='Zip Code')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.id'))
    
    # FIELD BARU: Relasi ke Area
    area_id = fields.Many2one('area.area', string='Area', required=True)
    
    # Computed field yang diperbarui
    full_address = fields.Text(string='Full Address', compute='_compute_full_address', store=True)
    
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    description = fields.Html(string='Description/Mosque Profile')
    
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    
    # Relation to Mosque Admins (Backend Users)
    board_member_ids = fields.One2many('mosque.board', 'mosque_id', string='Board Members')
    
    # # Relation to view all schedules in this mosque
    schedule_ids = fields.One2many('sermon.schedule', 'mosque_id', string='Sermon Schedules')
    
    # # Relation to view incoming proposals for this mosque
    proposal_ids = fields.One2many('sermon.proposal', 'mosque_id', string='Incoming Sermon Proposals')
    
    @api.depends('street', 'area_id', 'zip_code', 'country_id')
    def _compute_full_address(self):
        """Menggabungkan field alamat dengan menggunakan data dari area."""
        for record in self:
            parts = [record.street, record.area_id.name, record.zip_code, record.country_id.name]
            record.full_address = ', '.join(part for part in parts if part)

    # --- METODE BARU: Override name_get ---
    @api.depends('name', 'code', 'area_id')
    def name_get(self):
        """Menampilkan format: [CODE] Nama Masjid (Area)"""
        result = []
        for mosque in self:
            name = f"[{mosque.code or 'N/A'}] {mosque.name or 'N/A'}"
            if mosque.area_id.name:
                name += f" ({mosque.area_id.name})"
            result.append((mosque.id, name))
        return result