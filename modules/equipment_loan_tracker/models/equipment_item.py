from odoo import models, fields

class EquipmentItem(models.Model):
    _name = 'equipment.item'
    _description = 'Equipment Item'

    _sql_constraints = [
        (
            'equipment_code_unique',
            'UNIQUE(code)',
            'Kode inventaris alat harus unik.'
        ),
    ]

    name = fields.Char(
        string='Nama Alat',
        required=True
    )

    code = fields.Char(
        string='Kode Inventaris',
        required=True
    )

    category = fields.Selection(
        selection=[
            ('elektronik', 'Perangkat Elektronik'),
            ('kantor', 'Peralatan Kantor'),
            ('lainnya', 'Lainnya'),
        ],
        string='Kategori',
        required=True
    )

    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('on_loan', 'On Loan'),
            ('damaged', 'Damaged'),
        ],
        string='Status',
        default='available',
        required=True
    )

    notes = fields.Text(
        string='Catatan'
    )