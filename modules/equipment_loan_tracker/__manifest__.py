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
- Pergerakan stok peminjaman lewat Inventory
- Denda kehilangan otomatis lewat Invoicing
""",
    'author': 'Xenna Magang',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/equipment_loan_sequence.xml',
        'data/equipment_loan_cron.xml',
        'data/mail_templates.xml',
        'data/stock_loan_data.xml',
        'views/borrower_views.xml',
        'views/product_template_views.xml',
        'report/equipment_loan_report.xml',
        'views/equipment_loan_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}