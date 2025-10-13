# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json

def _get_image_url(record, field_name):
    """Helper function to create a public URL for an image field."""
    if record[field_name]:
        return f'/web/image/{record._name}/{record.id}/{field_name}'
    return None

class SermonAPIController(http.Controller):
     
    @http.route('/api/v1/mosques', auth='public', methods=['GET'], type='http', cors='*')
    def get_mosques(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua masjid."""
        try:
            mosques_raw = request.env['mosque.mosque'].search_read(
                [],
                ['id', 'name', 'code', 'area_id', 'image']
            )
            mosques_data = [{
                'id': m['id'],
                'name': m['name'],
                'code': m['code'],
                'area': m['area_id'][1] if m.get('area_id') else 'N/A',
                'image_url': f'/web/image/mosque.mosque/{m["id"]}/image' if m.get('image') else None
            } for m in mosques_raw]

            response_data = {
                'status': 'success',
                'count': len(mosques_data),
                'data': mosques_data
            }
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

    @http.route('/api/v1/preachers', auth='public', methods=['GET'], type='http', cors='*')
    def get_preachers(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua pendakwah."""
        try:
            preachers_raw = request.env['preacher.preacher'].search_read(
                [],
                ['id', 'name', 'code', 'specialization_id', 'area_id', 'image']
            )
            preachers_data = [{
                'id': p['id'],
                'name': p['name'],
                'code': p['code'],
                'specialization': p['specialization_id'][1] if p.get('specialization_id') else 'N/A',
                'area': p['area_id'][1] if p.get('area_id') else 'N/A',
                'image_url': f'/web/image/preacher.preacher/{p["id"]}/image' if p.get('image') else None
            } for p in preachers_raw]

            response_data = {
                'status': 'success',
                'count': len(preachers_data),
                'data': preachers_data
            }
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

    @http.route('/api/v1/mosques/<int:mosque_id>', auth='public', methods=['GET'], type='http', cors='*')
    def get_mosque_detail(self, mosque_id, **kwargs):
        """Endpoint untuk mendapatkan detail satu masjid beserta jadwalnya."""
        mosque = request.env['mosque.mosque'].browse(mosque_id)
        if not mosque.exists():
            error_response = {'status': 'error', 'message': 'Mosque not found'}
            return Response(json.dumps(error_response), content_type='application/json', status=404)
        
        schedules = request.env['sermon.schedule'].search_read(
            [('mosque_id', '=', mosque_id), ('state', '=', 'confirmed')],
            ['id', 'topic', 'start_time', 'preacher_id']
        )
        
        mosque_data = {
            'id': mosque.id,
            'name': mosque.name,
            'code': mosque.code,
            'area': mosque.area_id.name if mosque.area_id else None,
            'full_address': mosque.full_address,
            'description': mosque.description,
            'image_url': _get_image_url(mosque, 'image'),
            'schedules': [
                {
                    'id': s['id'],
                    'topic': s['topic'],
                    'start_time': s['start_time'].isoformat() if s.get('start_time') else None,
                    'preacher_id': s['preacher_id'][0],
                    'preacher_name': s['preacher_id'][1],
                } for s in schedules
            ]
        }
        response_data = {'status': 'success', 'data': mosque_data}
        return Response(json.dumps(response_data), content_type='application/json', status=200)

    @http.route('/api/v1/preachers/<int:preacher_id>', auth='public', methods=['GET'], type='http', cors='*')
    def get_preacher_detail(self, preacher_id, **kwargs):
        """Endpoint untuk mendapatkan detail satu pendakwah beserta jadwalnya."""
        preacher = request.env['preacher.preacher'].browse(preacher_id)
        if not preacher.exists():
            error_response = {'status': 'error', 'message': 'Preacher not found'}
            return Response(json.dumps(error_response), content_type='application/json', status=404)

        schedules = request.env['sermon.schedule'].search_read(
            [('preacher_id', '=', preacher_id), ('state', '=', 'confirmed')],
            ['id', 'topic', 'start_time', 'mosque_id']
        )
        
        preacher_data = {
            'id': preacher.id,
            'name': preacher.name,
            'code': preacher.code,
            'specialization': preacher.specialization_id.name if preacher.specialization_id else None,
            'area': preacher.area_id.name if preacher.area_id else None,
            'bio': preacher.bio,
            'image_url': _get_image_url(preacher, 'image'),
            'schedules': [
                 {
                    'id': s['id'],
                    'topic': s['topic'],
                    'start_time': s['start_time'].isoformat() if s.get('start_time') else None,
                    'mosque_id': s['mosque_id'][0],
                    'mosque_name': s['mosque_id'][1],
                } for s in schedules
            ]
        }
        response_data = {'status': 'success', 'data': preacher_data}
        return Response(json.dumps(response_data), content_type='application/json', status=200)

    @http.route('/api/v1/areas', auth='public', methods=['GET'], type='http', cors='*')
    def get_areas(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua area."""
        try:
            areas = request.env['area.area'].search_read([], ['id', 'name'])
            response_data = {'status': 'success', 'data': areas}
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

    @http.route('/api/v1/specializations', auth='public', methods=['GET'], type='http', cors='*')
    def get_specializations(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua spesialisasi."""
        try:
            specializations = request.env['preacher.specialization'].search_read([], ['id', 'name'])
            response_data = {'status': 'success', 'data': specializations}
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

