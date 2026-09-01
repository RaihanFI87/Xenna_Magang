{
    'name': 'Equipment Loan Tracker',
    'version': '1.0.0',
    'category': 'Inventory',
    'summary': 'Equipment borrowing and loan tracking system',
    'description': """
Equipment Loan Tracker
======================

Module untuk mengelola:
- Data peminjam
- Data alat
- Transaksi peminjaman alat
- Status ketersediaan alat
- Status transaksi peminjaman
- Pengembalian alat
""",
    'author': 'Xenna Magang',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/equipment_item_sequence.xml',
        'data/equipment_loan_sequence.xml',
        'data/equipment_loan_cron.xml',
        'views/borrower_views.xml',
        'views/equipment_item_views.xml',
        'report/equipment_loan_report.xml',
        'views/equipment_loan_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}