from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EquipmentLoan(models.Model):
    _name = 'equipment.loan'
    _description = 'Equipment Loan'
    _order = 'loan_date desc, id desc'

    name = fields.Char(
        string='Nomor Peminjaman',
        required=True,
        readonly=True,
        copy=False,
        default='New'
    )

    borrower_id = fields.Many2one(
        'res.partner',
        string='Peminjam',
        required=True,
        ondelete='restrict'
    )

    type = fields.Selection(
        selection=[
            ('internal', 'Internal Staff'),
            ('external', 'Eksternal'),
        ],
        string='Tipe',
    )

    loan_line_ids = fields.One2many(
        'equipment.loan.line',
        'loan_id',
        string='Daftar Alat'
    )

    borrower_email = fields.Char(
        string='Email',
        related='borrower_id.email',
        readonly=True
    )

    borrower_phone = fields.Char(
        string='Phone',
        related='borrower_id.phone',
        readonly=True
    )

    loan_duration = fields.Integer(
        string='Durasi Peminjaman (Hari)',
        compute='_compute_loan_duration'
    )

    loan_date = fields.Date(
        string='Tanggal Peminjaman',
        required=True,
        default=fields.Date.context_today
    )

    due_date = fields.Date(
        string='Tanggal Jatuh Tempo',
        required=True
    )

    return_date = fields.Date(
        string='Tanggal Pengembalian'
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('ongoing', 'Ongoing'),
            ('returned', 'Returned'),
            ('late', 'Late'),
        ],
        string='Status',
        default='draft',
        required=True
    )

    line_notes = fields.Text(
        string='Catatan'
    )
    equipment_names = fields.Char(
        string='Daftar Alat',
        compute='_compute_equipment_names'
    )



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'equipment.loan'
                ) or 'New'

        return super().create(vals_list)

    @api.constrains('loan_date', 'due_date')
    def _check_due_date(self):
        for record in self:
            if record.loan_date and record.due_date:
                if record.due_date < record.loan_date:
                    raise ValidationError(
                        'Tanggal jatuh tempo tidak boleh lebih awal '
                        'dari tanggal peminjaman.'
                    )

    @api.constrains('return_date', 'loan_date')
    def _check_return_date(self):
        for record in self:
            if record.return_date and record.loan_date:
                if record.return_date < record.loan_date:
                    raise ValidationError(
                        'Tanggal pengembalian tidak boleh lebih awal '
                        'dari tanggal peminjaman.'
                    )

    @api.constrains('equipment_id', 'state')
    @api.constrains('loan_line_ids', 'state')
    def _check_double_booking(self):
        for record in self:
            if record.state not in ('ongoing', 'late'):
                continue

            for line in record.loan_line_ids:
                existing_lines = self.env['equipment.loan.line'].search([
                    ('id', '!=', line.id),
                    ('equipment_id', '=', line.equipment_id.id),
                    ('loan_id.state', 'in', ('ongoing', 'late')),
                ], limit=1)

                if existing_lines:
                    raise ValidationError(
                        f'Alat "{line.equipment_id.name}" sedang dipinjam '
                        'dan tidak dapat dipinjam kembali.'
                    )

    def action_confirm(self):
        for record in self:

            if not record.loan_line_ids:
                raise ValidationError(
                    'Minimal harus ada satu alat yang dipinjam.'
                )

            if record.due_date < record.loan_date:
                raise ValidationError(
                    'Tanggal jatuh tempo tidak boleh lebih awal '
                    'dari tanggal peminjaman.'
                )

            for line in record.loan_line_ids:

                if line.equipment_id.state == 'damaged':
                    raise ValidationError(
                        f'Alat "{line.equipment_id.name}" '
                        'dalam kondisi rusak dan tidak dapat dipinjam.'
                    )

                if line.equipment_id.state == 'on_loan':
                    raise ValidationError(
                        f'Alat "{line.equipment_id.name}" '
                        'sedang dipinjam dan tidak dapat dipinjam kembali.'
                    )

            record.write({
                'state': 'ongoing',
            })

            for line in record.loan_line_ids:
                line.equipment_id.write({
                    'state': 'on_loan',
                })

    def action_return(self):
        for record in self:

            if record.state not in ('ongoing', 'late'):
                raise ValidationError(
                    'Hanya peminjaman yang sedang berlangsung '
                    'atau terlambat yang dapat dikembalikan.'
                )

            today = fields.Date.context_today(self)

            if today > record.due_date:
                new_state = 'late'
                note = (
                    'Peminjaman dikembalikan setelah '
                    'tanggal jatuh tempo.'
                )
            else:
                new_state = 'returned'
                note = False

            record.write({
                'state': new_state,
                'return_date': today,
                'line_notes': note,
            })

            for line in record.loan_line_ids:
                line.equipment_id.write({
                    'state': 'available',
                })

    @api.model
    def _cron_check_overdue(self):
        today = fields.Date.context_today(self)

        loans = self.search([
            ('state', '=', 'ongoing'),
            ('due_date', '<', today),
        ])

        if loans:
            loans.write({
                'state': 'late',
                'line_notes':'kamu sudah terlambat'
            })

    @api.depends('loan_date', 'return_date')
    def _compute_loan_duration(self):
        today = fields.Date.context_today(self)

        for record in self:
            if not record.loan_date:
                record.loan_duration = 0
                continue

            end_date = record.return_date or today
            duration = (end_date - record.loan_date).days

            record.loan_duration = max(duration, 0)

    @api.depends('loan_line_ids.equipment_id')
    def _compute_equipment_names(self):
        for record in self:
            record.equipment_names = ', '.join(
                record.loan_line_ids.mapped('equipment_id.name')
            )

class EquipmentLoanLine(models.Model):
    _name = 'equipment.loan.line'
    _description = 'Equipment Loan Line'

    loan_id = fields.Many2one(
        'equipment.loan',
        string='Peminjaman',
        required=True,
        ondelete='cascade'
    )

    equipment_id = fields.Many2one(
        'equipment.item',
        string='Alat',
        required=True,
        ondelete='restrict'
    )


