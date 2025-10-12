# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json

def _get_image_url(record, field_name):
    """Helper function to create a public URL for an image field."""
    if record[field_name]:
        # Creates a URL like /web/image/mosque.mosque/1/image
        return f'/web/image/{record._name}/{record.id}/{field_name}'
    return None

class SermonAPIController(http.Controller):
    
    def _json_response(self, data):
        """Helper to create a standard JSON response."""
        return Response(
            json.dumps(data, default=str),  # Use default=str to handle dates/datetimes
            content_type='application/json'
        )

    @http.route('/api/v1/mosques', auth='public', methods=['GET'], type='json', cors='*')
    def get_mosques(self, **kwargs):
        """
        Endpoint untuk mendapatkan daftar semua masjid.
        Digunakan di Tab Masjid.
        ---
        Contoh Panggilan: GET http://<odoo_url>/api/v1/mosques
        """
        try:
            mosques = request.env['mosque.mosque'].search_read(
                [],
                ['id', 'name', 'city', 'province', 'image']
            )
            # Mengonversi gambar base64 ke URL agar lebih efisien
            for mosque in mosques:
                if mosque.get('image'):
                    mosque['image_url'] = f'/web/image/mosque.mosque/{mosque["id"]}/image'
                del mosque['image'] # Hapus data base64 yang besar

            return {
                'status': 'success',
                'count': len(mosques),
                'data': mosques
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/v1/preachers', auth='public', methods=['GET'], type='json', cors='*')
    def get_preachers(self, **kwargs):
        """
        Endpoint untuk mendapatkan daftar semua pendakwah.
        Digunakan di Tab Pendakwah.
        ---
        Contoh Panggilan: GET http://<odoo_url>/api/v1/preachers
        """
        try:
            preachers = request.env['preacher.preacher'].search_read(
                [],
                ['id', 'name', 'specialization', 'image']
            )
            for preacher in preachers:
                 if preacher.get('image'):
                    preacher['image_url'] = f'/web/image/preacher.preacher/{preacher["id"]}/image'
                 del preacher['image']

            return {
                'status': 'success',
                'count': len(preachers),
                'data': preachers
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/v1/mosques/<int:mosque_id>', auth='public', methods=['GET'], type='json', cors='*')
    def get_mosque_detail(self, mosque_id, **kwargs):
        """
        Endpoint untuk mendapatkan detail satu masjid beserta jadwalnya.
        Digunakan di halaman Detail Masjid.
        ---
        Contoh Panggilan: GET http://<odoo_url>/api/v1/mosques/1
        """
        mosque = request.env['mosque.mosque'].browse(mosque_id)
        if not mosque.exists():
            return {'status': 'error', 'message': 'Mosque not found'}
        
        # Ambil data jadwal yang sudah dikonfirmasi
        schedules = request.env['sermon.schedule'].search_read(
            [('mosque_id', '=', mosque_id), ('state', '=', 'confirmed')],
            ['id', 'topic', 'start_time', 'preacher_id']
        )
        
        # Siapkan data untuk respons
        mosque_data = {
            'id': mosque.id,
            'name': mosque.name,
            'city': mosque.city,
            'province': mosque.province,
            'full_address': mosque.full_address,
            'description': mosque.description,
            'image_url': _get_image_url(mosque, 'image'),
            'schedules': [
                {
                    'id': s['id'],
                    'topic': s['topic'],
                    'start_time': s['start_time'],
                    'preacher_id': s['preacher_id'][0],
                    'preacher_name': s['preacher_id'][1],
                } for s in schedules
            ]
        }
        
        return {'status': 'success', 'data': mosque_data}


    @http.route('/api/v1/preachers/<int:preacher_id>', auth='public', methods=['GET'], type='json', cors='*')
    def get_preacher_detail(self, preacher_id, **kwargs):
        """
        Endpoint untuk mendapatkan detail satu pendakwah beserta jadwalnya.
        Digunakan di halaman Detail Pendakwah.
        ---
        Contoh Panggilan: GET http://<odoo_url>/api/v1/preachers/101
        """
        preacher = request.env['preacher.preacher'].browse(preacher_id)
        if not preacher.exists():
            return {'status': 'error', 'message': 'Preacher not found'}

        schedules = request.env['sermon.schedule'].search_read(
            [('preacher_id', '=', preacher_id), ('state', '=', 'confirmed')],
            ['id', 'topic', 'start_time', 'mosque_id']
        )
        
        preacher_data = {
            'id': preacher.id,
            'name': preacher.name,
            'specialization': preacher.specialization,
            'bio': preacher.bio,
            'image_url': _get_image_url(preacher, 'image'),
            'schedules': [
                 {
                    'id': s['id'],
                    'topic': s['topic'],
                    'start_time': s['start_time'],
                    'mosque_id': s['mosque_id'][0],
                    'mosque_name': s['mosque_id'][1],
                } for s in schedules
            ]
        }
        
        return {'status': 'success', 'data': preacher_data}
