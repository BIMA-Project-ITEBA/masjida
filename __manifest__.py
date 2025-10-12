# gym_management/__manifest__.py
{
    'name': 'Masjida',
    'version': '1.0',
    'summary': 'Masjida, Companies, Reviews, and Galleries for a mobile app.',
    'author': 'Anda',
    'website': '',
    'category': 'Services/masjid',
    'depends': ['base', 'web'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        # --- Load views ---
        'views/menu.xml', # Muat menu utama dulu
        'views/mosque_views.xml',
        'views/preacher_views.xml',
        'views/board_views.xml',
        'views/area_views.xml', # Tambahkan ini
         'views/specialization_views.xml',   
        'views/schedule_views.xml',
        'views/content_views.xml',
        
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}