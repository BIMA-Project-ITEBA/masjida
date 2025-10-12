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
            mosques_raw = request.env['mosque.mosque'].search_read(
                [],
                ['id', 'name','city', 'code', 'area_id', 'image']
            )
            # Mengonversi gambar base64 ke URL agar lebih efisien
             # Memformat data agar lebih ramah untuk frontend
            mosques_data = [{
                'id': m['id'],
                'name': m['name'],
                'city':m['city'],
                'code': m['code'], # Menambahkan kode ke JSON
                'area': m['area_id'][1] if m.get('area_id') else 'N/A',
                'image_url': f'/web/image/mosque.mosque/{m["id"]}/image' if m.get('image') else None
            } for m in mosques_raw]

            return {
                'status': 'success',
                'count': len(mosques_data),
                'data': mosques_data
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
            # Menambahkan 'code' ke daftar field yang diambil
            preachers_raw = request.env['preacher.preacher'].search_read(
                [],
                ['id', 'name', 'code', 'specialization_id', 'area_id', 'image']
            )
            preachers_data = [{
                'id': p['id'],
                'name': p['name'],
                'code': p['code'], # Menambahkan kode ke JSON
                'specialization': p['specialization_id'][1] if p.get('specialization_id') else 'N/A',
                'area': p['area_id'][1] if p.get('area_id') else 'N/A',
                'image_url': f'/web/image/preacher.preacher/{p["id"]}/image' if p.get('image') else None
            } for p in preachers_raw]

            return {
                'status': 'success',
                'count': len(preachers_data),
                'data': preachers_data
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/v1/mosques/<int:mosque_id>', auth='public', methods=['GET'], type='json', cors='*')
    def get_mosque_detail(self, mosque_id, **kwargs):
        mosque = request.env['mosque.mosque'].browse(mosque_id)
        if not mosque.exists():
            return {'status': 'error', 'message': 'Mosque not found'}
        
        schedules = request.env['sermon.schedule'].search_read(
            [('mosque_id', '=', mosque_id), ('state', '=', 'confirmed')],
            ['id', 'topic', 'start_time', 'preacher_id']
        )
        
        mosque_data = {
            'id': mosque.id,
            'name': mosque.name,
            'code': mosque.code, # Menambahkan kode ke JSON
            'area': mosque.area_id.name if mosque.area_id else None,
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
            'code': preacher.code, # Menambahkan kode ke JSON
            'specialization': preacher.specialization_id.name if preacher.specialization_id else None,
            'area': preacher.area_id.name if preacher.area_id else None,
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

    @http.route('/api/v1/areas', auth='public', methods=['GET'], type='json', cors='*')
    def get_areas(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua area."""
        try:
            areas = request.env['area.area'].search_read([], ['id', 'name'])
            return {'status': 'success', 'data': areas}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/v1/specializations', auth='public', methods=['GET'], type='json', cors='*')
    def get_specializations(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua spesialisasi."""
        try:
            specializations = request.env['preacher.specialization'].search_read([], ['id', 'name'])
            return {'status': 'success', 'data': specializations}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

