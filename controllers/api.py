# -*- coding: utf-8 -*-
from odoo import http, fields # <-- 'fields' ditambahkan
from odoo.http import request, Response
import json
import logging 
from datetime import datetime # <-- 'datetime' ditambahkan

# Mengatur logger untuk debugging
_logger = logging.getLogger(__name__) 


def _get_image_url(record, field_name):
    """Fungsi helper untuk membuat URL gambar publik dari Odoo."""
    if record[field_name]:
        # Mengembalikan URL relatif. Klien (Flutter) akan menambahkan _baseUrl
        return f'/web/image/{record._name}/{record.id}/{field_name}'
    return None

class SermonAPIController(http.Controller):
     
    @http.route('/api/v1/mosques', auth='public', methods=['GET'], type='http', cors='*')
    def get_mosques(self, search=None, area_id=None, **kwargs):
        """
        Endpoint untuk mendapatkan daftar semua masjid.
        Mendukung pencarian berdasarkan 'name' dan 'area_id.name'.
        Mendukung filter berdasarkan 'area_id'.
        """
        try:
            # Domain adalah list untuk filter Odoo
            domain = []
            
            # 1. Logika Pencarian (Search)
            if search:
                # 'ilike' artinya case-insensitive search (tidak peduli huruf besar/kecil)
                # Domain OR: Cari berdasarkan nama masjid ATAU nama area
                domain += [
                    '|',
                    ('name', 'ilike', search),
                    ('area_id.name', 'ilike', search) 
                ]

            # 2. Logika Filter (Area)
            if area_id:
                try:
                    # Pastikan area_id adalah angka (integer)
                    area_id_int = int(area_id)
                    domain.append(('area_id', '=', area_id_int))
                except ValueError:
                    _logger.warning(f"Nilai area_id tidak valid diterima: {area_id}")
                    pass # Abaikan jika area_id tidak valid (misal: "null" atau string kosong)

            # Terapkan domain (filter) ke pencarian
            mosques_raw = request.env['mosque.mosque'].search_read(
                domain,
                ['id', 'name', 'code', 'area_id', 'image'],
                order='name ASC' # Urutkan berdasarkan nama
            )
            
            mosques_data = [{
                'id': m['id'],
                'name': m['name'],
                'code': m['code'],
                'area': m['area_id'][1] if m.get('area_id') else 'N/A', # Mengambil nama area
                'image_url': f'/web/image/mosque.mosque/{m["id"]}/image' if m.get('image') else None
            } for m in mosques_raw]

            response_data = {
                'status': 'success',
                'count': len(mosques_data),
                'data': mosques_data
            }
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        
        except Exception as e:
            _logger.error(f"Error saat get_mosques: {e}", exc_info=True)
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
                # Mengirim NAMA untuk tampilan
                'specialization': p['specialization_id'][1] if p.get('specialization_id') else 'N/A',
                'area': p['area_id'][1] if p.get('area_id') else 'N/A',
                # BARU: Mengirim ID untuk filtering
                'specialization_id': p['specialization_id'][0] if p.get('specialization_id') else None,
                'area_id': p['area_id'][0] if p.get('area_id') else None,
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

    # --- FUNGSI INI DIMODIFIKASI (UNTUK GOOGLE MAPS) ---
    @http.route('/api/v1/mosques/<int:mosque_id>', auth='public', methods=['GET'], type='http', cors='*')
    def get_mosque_detail(self, mosque_id, **kwargs):
        """Endpoint untuk mendapatkan detail satu masjid beserta jadwalnya."""
        
        # Gunakan .sudo() untuk bypass izin baca public user (untuk area, lat, lon)
        mosque = request.env['mosque.mosque'].sudo().browse(mosque_id)
        if not mosque.exists():
            error_response = {'status': 'error', 'message': 'Mosque not found'}
            return Response(json.dumps(error_response), content_type='application/json', status=404)
        
        # Jadwal (ir.rule publik sudah memperbolehkan ini)
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
            
            # --- TAMBAHAN BARU UNTUK GOOGLE MAPS ---
            'latitude': mosque.latitude,
            'longitude': mosque.longitude,
            # -------------------------------------
            
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
        # .sudo() untuk membaca relasi (area/specialization)
        preacher = request.env['preacher.preacher'].sudo().browse(preacher_id)
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
            areas = request.env['area.area'].search_read([], ['id', 'name'], order='name ASC')
            response_data = {'status': 'success', 'data': areas}
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            _logger.error(f"Error saat get_areas: {e}", exc_info=True)
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

    @http.route('/api/v1/specializations', auth='public', methods=['GET'], type='http', cors='*')
    def get_specializations(self, **kwargs):
        """Endpoint untuk mendapatkan daftar semua spesialisasi."""
        try:
            specializations = request.env['preacher.specialization'].search_read([], ['id', 'name'], order='name ASC')
            response_data = {'status': 'success', 'data': specializations}
            return Response(json.dumps(response_data), content_type='application/json', status=200)
        except Exception as e:
            _logger.error(f"Error saat get_specializations: {e}", exc_info=True)
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)

    # --- ENDPOINT BARU UNTUK HALAMAN JADWAL PUBLIK ---
    @http.route('/api/v1/schedules/public', auth='public', methods=['GET'], type='http', cors='*')
    def get_public_schedules(self, search=None, area_id=None, day_of_week=None, **kwargs):
        """
        Endpoint untuk mendapatkan daftar jadwal publik (confirmed & future).
        Mendukung pencarian (topik, pendakwah), filter area, dan filter hari (day_of_week).
        day_of_week: 0=Senin, 1=Selasa, ..., 6=Minggu (sesuai Python .weekday())
        """
        _logger.info(f"get_public_schedules dipanggil dengan search: {search}, area_id: {area_id}, day_of_week: {day_of_week}")
        
        try:
            # 1. Domain Awal (Confirmed & Future)
            domain = [
                ('state', '=', 'confirmed'),
                ('start_time', '>=', fields.Datetime.now())
            ]

            # 2. Filter Pencarian (Topik / Pendakwah)
            if search:
                domain += [
                    '|',
                    ('topic', 'ilike', search),
                    ('preacher_id.name', 'ilike', search)
                ]

            # 3. Filter Area (Area Masjid)
            if area_id:
                try:
                    domain.append(('mosque_id.area_id', '=', int(area_id)))
                except (ValueError, TypeError):
                    _logger.warning(f"Invalid area_id passed: {area_id}")
                    pass # Abaikan area_id yang tidak valid

            # 4. Ambil Field yang Diperlukan
            fields_to_read = ['id', 'topic', 'start_time', 'preacher_id', 'mosque_id']
            
            # 5. Search Odoo (tanpa filter hari)
            # .sudo() diperlukan agar public user bisa filter by preacher.name / mosque.area_id
            schedules_raw = request.env['sermon.schedule'].sudo().search_read(
                domain,
                fields_to_read,
                order='start_time ASC' # Urutkan dari yang paling dekat
            )

            # 6. Filter Hari (Python-side)
            final_schedules = []
            
            dow_filter = None
            if day_of_week:
                try:
                    dow_filter = int(day_of_week)
                except (ValueError, TypeError):
                    dow_filter = None

            for s in schedules_raw:
                # 'start_time' adalah objek datetime dari Odoo
                if not s.get('start_time'):
                    continue 
                
                # Filter berdasarkan Hari (jika ada)
                if dow_filter is not None:
                    # .weekday() -> Senin=0, Minggu=6
                    if s['start_time'].weekday() != dow_filter:
                        continue # Lewati jika harinya tidak cocok
                
                # 7. Format Data (Data yang lolos filter)
                final_schedules.append({
                    'id': s['id'],
                    'topic': s['topic'],
                    'start_time': s['start_time'].isoformat(),
                    'preacher_name': s['preacher_id'][1] if s.get('preacher_id') else 'N/A',
                    'mosque_name': s['mosque_id'][1] if s.get('mosque_id') else 'N/A',
                    'mosque_id': s['mosque_id'][0] if s.get('mosque_id') else None,
                    # (Kita tidak perlu mosque_area_name di list, mosque_name sudah cukup)
                })

            # 8. Kirim Respon
            response_data = {
                'status': 'success',
                'count': len(final_schedules),
                'data': final_schedules
            }
            # default=str digunakan untuk menangani objek datetime (meskipun sudah isoformat)
            return Response(json.dumps(response_data, default=str), content_type='application/json', status=200)

        except Exception as e:
            _logger.error(f"Error saat get_public_schedules: {e}", exc_info=True)
            error_response = {'status': 'error', 'message': str(e)}
            return Response(json.dumps(error_response), content_type='application/json', status=500)
    # --------------------------------------------------

    @http.route('/api/register_user', type='json', auth='public', methods=['POST'], csrf=False)
    def register_user(self, **kw):
        """
        Menerima data dari form registrasi dan membuat record
        res.users dan preacher.preacher baru.
        """
        _logger.info(f"Menerima permintaan registrasi: {kw}")
        required_fields = ['name', 'email', 'password', 'phone', 'user_type']

        if not all(field in kw for field in required_fields):
            return {'status': 'error', 'message': 'Missing required fields.'}

        try:
            existing_user = request.env['res.users'].sudo().search([('login', '=', kw.get('email'))])
            if existing_user:
                return {'status': 'error', 'message': 'Email already exists.'}

            if kw.get('user_type') == 'preacher':
                portal_group_id = request.env.ref('base.group_portal').id
                new_user_vals = {
                    'name': kw.get('name'),
                    'login': kw.get('email'),
                    'password': kw.get('password'),
                    'groups_id': [(6, 0, [portal_group_id])]
                }
                new_user = request.env['res.users'].sudo().create(new_user_vals)
                
                new_preacher_vals = {
                    'user_id': new_user.id,
                    'name': kw.get('name'),
                    'phone': kw.get('phone'),
                    'email': kw.get('email'),
                    'date_of_birth': kw.get('date_of_birth'),
                    'gender': kw.get('gender'),
                }
                request.env['preacher.preacher'].sudo().create(new_preacher_vals)

                return {'status': 'success', 'message': 'User registered successfully! Please log in.'}
            else:
                return {'status': 'error', 'message': 'Invalid user type.'}

        except Exception as e:
            _logger.error(f"Error during user registration: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/profile', type='http', auth='user', methods=['GET'], csrf=False)
    def get_preacher_profile(self, **kw):
        """Mengambil profil lengkap Pendakwah (preacher) yang sedang login."""
        try:
            user = request.env['preacher.preacher'].sudo().search([('user_id', '=', request.uid)], limit=1)
            if not user:
                error_response = {'status': 'error', 'message': 'Profil pendakwah tidak ditemukan.'}
                return Response(json.dumps(error_response), content_type='application/json', status=404)

            schedules = request.env['sermon.schedule'].search_read(
                [('preacher_id', '=', user.id), ('state', '=', 'confirmed')],
                ['id', 'topic', 'start_time', 'mosque_id']
            )
            
            profile_data = {
                'id': user.id,
                'name': user.name,
                
                'area_id': user.area_id.id or None,
                'area_name': user.area_id.name if user.area_id else None,
                
                'specialization_id': user.specialization_id.id or None,
                'specialization_name': user.specialization_id.name if user.specialization_id else None,
                
                'email': user.email,
                'image_url': _get_image_url(user, 'image'),
                'user_type': 'preacher',
                'gender': user.gender,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'phone': user.phone,
                'education': user.education,
                'bio': user.bio,
                'code': user.code,
                'period': user.period,
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
            _logger.error(f"Error fetching preacher profile: {e}", exc_info=True)
            return request.make_response('Internal Server Error', status=500)

    @http.route('/api/update_profile', type='json', auth='user', methods=['POST'], csrf=False)
    def update_preacher_profile(self, **kw):
        """
        Memperbarui profil Pendakwah (preacher.preacher) yang sedang login.
        Menerima 'image' sebagai string base64.
        """
        try:
            user = request.env['preacher.preacher'].sudo().search([('user_id', '=', request.uid)], limit=1)
            if not user.exists():
                return {'status': 'error', 'message': 'Profil Pendakwah (preacher.preacher) not found.'}

            allowed_fields = [
                'name', 
                'phone', 
                'bio', 
                'education', 
                'date_of_birth', 
                'gender', 
                'area_id', 
                'specialization_id',
                'period',
                'image' 
            ]
            
            vals_to_update = {}
            for field in allowed_fields:
                if field in kw:
                    value = kw.get(field)
                    
                    if field == 'period' and value is not None:
                        try:
                            vals_to_update[field] = float(value)
                        except (ValueError, TypeError):
                            pass 
                    elif field in ['area_id', 'specialization_id'] and (value is None or value is False):
                         vals_to_update[field] = False
                    elif value is not None:
                        vals_to_update[field] = value
            
            if vals_to_update:
                _logger.info(f"Updating profile for user {request.uid} with values: {list(vals_to_update.keys())}")
                user.write(vals_to_update) # user sudah .sudo()
            
            return {'status': 'success', 'message': 'Profile updated successfully.'}
        except Exception as e:
            _logger.error(f"Error updating preacher profile: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    # --- ENDPOINT NOTIFIKASI (TETAP SAMA) ---

    @http.route('/api/v1/schedules/pending', auth='user', methods=['GET'], type='http', cors='*')
    def get_pending_schedules(self, **kwargs):
        """
        Mengambil daftar jadwal yang dikirim (sent) ke pendakwah yang sedang login.
        """
        try:
            preacher = request.env['preacher.preacher'].search([('user_id', '=', request.uid)], limit=1)
            if not preacher:
                return Response(json.dumps({'status': 'error', 'message': 'Profil pendakwah tidak ditemukan.'}), content_type='application/json', status=404)

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
            schedule = request.env['sermon.schedule'].sudo().browse(schedule_id)
            if not schedule.exists() or schedule.preacher_id.user_id.id != request.uid:
                return {'status': 'error', 'message': 'Jadwal tidak ditemukan atau Anda tidak berhak.'}
            
            schedule.action_confirm()
            return {'status': 'success', 'message': 'Jadwal berhasil diterima!'}
        except Exception as e:
            _logger.error(f"Error confirming schedule: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/v1/schedules/<int:schedule_id>/reject', auth='user', methods=['POST'], type='json', csrf=False)
    def reject_schedule(self, schedule_id, **kwargs):
        """Menjalankan action_reject pada sebuah jadwal."""
        try:
            schedule = request.env['sermon.schedule'].sudo().browse(schedule_id)
            if not schedule.exists() or schedule.preacher_id.user_id.id != request.uid:
                return {'status': 'error', 'message': 'Jadwal tidak ditemukan atau Anda tidak berhak.'}

            schedule.action_reject()
            return {'status': 'success', 'message': 'Jadwal telah ditolak.'}
        except Exception as e:
            _logger.error(f"Error rejecting schedule: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/v1/proposals', auth='user', methods=['POST'], type='json', csrf=False)
    def create_proposal(self, **kw):
        """
        Membuat proposal dakwah (sermon.proposal) dari Pendakwah yang login.
        Endpoint ini memerlukan autentikasi (auth='user').
        preacher_id akan diisi otomatis berdasarkan user yang login (sesuai default model).
        """
        data = kw
        _logger.info(f"Menerima permintaan proposal: {data} oleh user {request.uid}")

        required_fields = ['mosque_id', 'proposed_topic', 'proposed_start_time']
        if not all(field in data for field in required_fields):
            _logger.warning("Permintaan proposal gagal: field tidak lengkap.")
            return {'status': 'error', 'message': 'Field tidak lengkap (mosque_id, proposed_topic, proposed_start_time).'}

        try:
            # Buat proposal baru. preacher_id akan diisi oleh default model
            proposal = request.env['sermon.proposal'].create({
                'mosque_id': data.get('mosque_id'),
                'proposed_topic': data.get('proposed_topic'),
                'proposed_start_time': data.get('proposed_start_time'),
                'notes': data.get('notes'),
                'full_description': data.get('full_description'), # Field baru
                'attachment_file': data.get('attachment_file'),   # Base64 string dari Flutter
                'attachment_filename': data.get('attachment_filename'), # Nama file asli
            })
            
            # Langsung ubah statusnya menjadi 'submitted'
            proposal.action_submit()
            
            _logger.info(f"Proposal {proposal.id} berhasil dibuat dan dikirim.")
            return {'status': 'success', 'message': 'Proposal berhasil diajukan.', 'proposal_id': proposal.id}

        except Exception as e:
            _logger.error(f"Gagal membuat proposal: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/help/types', type='json', auth='public', methods=['POST'], csrf=False)
    def get_help_types(self, **kwargs):
        """Mengambil daftar jenis bantuan yang dikonfigurasi di Odoo"""
        types = request.env['masjida.help.type'].sudo().search([('active', '=', True)])
        return {
            'status': 200,
            'data': [{'id': t.id, 'name': t.name} for t in types]
        }

    @http.route('/api/help/submit', type='json', auth='user', methods=['POST'], csrf=False)
    def submit_help_request(self, **kwargs):
        """Menyimpan permintaan bantuan dari aplikasi Flutter"""
        user = request.env.user
        help_type_id = kwargs.get('help_type_id')
        description = kwargs.get('description')

        if not help_type_id or not description:
            return {'status': 400, 'message': 'Missing required fields'}

        request.env['masjida.help.request'].sudo().create({
            'user_id': user.id,
            'help_type_id': int(help_type_id),
            'description': description,
        })
        return {'status': 200, 'message': 'Permintaan bantuan berhasil dikirim'}