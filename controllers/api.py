# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging  # <-- 1. Impor library logging

_logger = logging.getLogger(__name__)  # <-- 2. Inisialisasi logger


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

    @http.route('/api/register_user', type='json', auth='public', methods=['POST'], csrf=False)
    def register_user(self, **kw):
        """
        Menerima data dari form registrasi dan membuat record
        res.users dan preacher.preacher baru.
        """
        _logger.info(f"Menerima permintaan registrasi: {kw}")
        required_fields = ['name', 'email', 'password', 'phone', 'user_type']

        # Cek apakah semua field yang dibutuhkan ada
        if not all(field in kw for field in required_fields):
            return {'status': 'error', 'message': 'Missing required fields.'}

        try:
            # Cek apakah email (login) sudah ada
            existing_user = request.env['res.users'].sudo().search([('login', '=', kw.get('email'))])
            if existing_user:
                return {'status': 'error', 'message': 'Email already exists.'}

            if kw.get('user_type') == 'preacher':
                # Dapatkan referensi grup Portal
                portal_group_id = request.env.ref('base.group_portal').id

                # 1. Buat record di res.users terlebih dahulu
                new_user_vals = {
                    'name': kw.get('name'),
                    'login': kw.get('email'),
                    'password': kw.get('password'),
                    # Tambahkan pengguna ke grup Portal
                    'groups_id': [(6, 0, [portal_group_id])]
                }
                new_user = request.env['res.users'].sudo().create(new_user_vals)
                
                # 2. Buat record di preacher.preacher
                new_preacher_vals = {
                    'user_id': new_user.id,
                    'name': kw.get('name'),
                    'phone': kw.get('phone'),
                    'email': kw.get('email'),
                    # Tambahkan field lain jika ada dari form registrasi
                    # 'date_of_birth': kw.get('date_of_birth'),
                    # 'gender': kw.get('gender'),
                }
                request.env['preacher.preacher'].sudo().create(new_preacher_vals)

                return {'status': 'success', 'message': 'User registered successfully! Please log in.'}
            else:
                return {'status': 'error', 'message': 'Invalid user type.'}

        except Exception as e:
            _logger.error(f"Error during user registration: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}


     # --- FUNGSI BARU UNTUK MENGAMBIL PROFIL LENGKAP GYMNEST USER ---
    @http.route('/api/profile', type='http', auth='user', methods=['GET'], csrf=False)
    def get__user_profile(self, **kw):
        try:
            # Cari gymnest.user yang terhubung dengan res.users yang sedang login
            user = request.env['preacher.preacher'].search([('user_id', '=', request.uid)], limit=1)
            if not user:
                error_response = {'status': 'error', 'message': 'Profil pendakwah tidak ditemukan.'}
                return Response(json.dumps(error_response), content_type='application/json', status=404)

            # --- PERBAIKAN: Gunakan sudo() untuk melewati access rights ---
            user = user.sudo()
            schedules = request.env['sermon.schedule'].search_read(
            [('preacher_id', '=', user.id), ('state', '=', 'confirmed')],
            ['id', 'topic', 'start_time', 'mosque_id']
        )
            
            # Ambil semua data yang dibutuhkan
            profile_data = {
                'id': user.id,
                'name': user.name,
                'specialization': user.specialization_id.name if user.specialization_id else None,
                'email': user.email,
                'image_url': _get_image_url(user, 'image'),
                'user_type': 'preacher',
                'gender': user.gender,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'phone': user.phone,
                'education': user.education,
                 'area': user.area_id.name if user.area_id else None,
                'bio': user.bio,
                'code': user.code,
                'gender':user.gender,
                'period':user.period,
                'schedules': [
                 {
                    'id': s['id'],
                    'topic': s['topic'],
                    'start_time': s['start_time'].isoformat() if s.get('start_time') else None,
                    'mosque_id': s['mosque_id'][0],
                    'mosque_name': s['mosque_id'][1],
                } for s in schedules
            ],
                'state': user.state,
            }
            return request.make_json_response({'status': 'success', 'data': profile_data})
        except Exception as e:
            _logger.error(f"Error fetching gymnest user profile: {e}", exc_info=True)
            return request.make_response('Internal Server Error', status=500)

    # --- FUNGSI BARU UNTUK UPDATE PROFIL ---
    @http.route('/api/update_profile', type='json', auth='user', methods=['POST'], csrf=False)
    def update_gymnest_user_profile(self, **kw):
        """
        Hanya akan mengupdate field yang diizinkan
        """
        try:
            user = request.env['gymnest.user'].search([('user_id', '=', request.uid)], limit=1)
            if not user.exists():
                return {'status': 'error', 'message': 'Gymnest user not found.'}

            # Siapkan dictionary berisi field yang boleh diupdate
            allowed_fields = ['mobile_number', 'address', 'weight', 'height', 'geolocation']
            vals_to_update = {}
            for field in allowed_fields:
                if field in kw:
                    vals_to_update[field] = kw.get(field)
            
            if vals_to_update:
                user.write(vals_to_update)
            
            return {'status': 'success', 'message': 'Profile updated successfully.'}
        except Exception as e:
            _logger.error(f"Error updating gymnest user profile: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

# --- ENDPOINT BARU UNTUK NOTIFIKASI UNDANGAN ---

    @http.route('/api/v1/schedules/pending', auth='user', methods=['GET'], type='http', cors='*')
    def get_pending_schedules(self, **kwargs):
        """
        Mengambil daftar jadwal yang dikirim (sent) ke pendakwah yang sedang login.
        Membutuhkan user untuk login (auth='user').
        """
        try:
            # Cari profil pendakwah yang terhubung dengan user yang sedang login
            preacher = request.env['preacher.preacher'].search([('user_id', '=', request.uid)], limit=1)
            if not preacher:
                return Response(json.dumps({'status': 'error', 'message': 'Profil pendakwah tidak ditemukan.'}), content_type='application/json', status=404)

            # Cari jadwal dengan status 'sent' untuk pendakwah tersebut
            schedules_raw = request.env['sermon.schedule'].search_read(
                [('preacher_id', '=', preacher.id), ('state', '=', 'sent')],
                ['id', 'topic', 'start_time', 'end_time', 'description', 'mosque_id']
            )

            schedules_data = [{
                'id': s['id'],
                'topic': s['topic'],
                'start_time': s['start_time'].isoformat() if s.get('start_time') else None,
                'end_time': s['end_time'].isoformat() if s.get('end_time') else None,
                'description': s['description'],
                'mosque_name': s['mosque_id'][1] if s.get('mosque_id') else 'N/A',
                'mosque_image_url': f"/web/image/mosque.mosque/{s['mosque_id'][0]}/image" if s.get('mosque_id') else None
            } for s in schedules_raw]

            response_data = {'status': 'success', 'data': schedules_data}
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            _logger.error(f"Error fetching pending schedules: {e}", exc_info=True)
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

    @http.route('/api/v1/schedules/<int:schedule_id>/confirm', auth='user', methods=['POST'], type='json', csrf=False)
    def confirm_schedule(self, schedule_id, **kwargs):
        """Menjalankan action_confirm pada sebuah jadwal."""
        try:
            schedule = request.env['sermon.schedule'].browse(schedule_id)
            # Validasi: Pastikan jadwal ada dan user-nya benar
            if not schedule.exists() or schedule.preacher_id.user_id.id != request.uid:
                return {'status': 'error', 'message': 'Jadwal tidak ditemukan atau Anda tidak berhak.'}
            
            schedule.action_confirm()
            return {'status': 'success', 'message': 'Jadwal berhasil diterima!'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/v1/schedules/<int:schedule_id>/reject', auth='user', methods=['POST'], type='json', csrf=False)
    def reject_schedule(self, schedule_id, **kwargs):
        """Menjalankan action_reject pada sebuah jadwal."""
        try:
            schedule = request.env['sermon.schedule'].browse(schedule_id)
            if not schedule.exists() or schedule.preacher_id.user_id.id != request.uid:
                return {'status': 'error', 'message': 'Jadwal tidak ditemukan atau Anda tidak berhak.'}

            schedule.action_reject()
            return {'status': 'success', 'message': 'Jadwal telah ditolak.'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}



