from odoo import models, fields, api

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
        required=True,
        readonly=True,
        copy=False,
        default='New'
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code(
                    'equipment.item'
                ) or 'New'

        return super().create(vals_list)