from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EquipmentLoanExtensionRequest(models.Model):
    _name = 'equipment.loan.extension.request'
    _description = 'Equipment Loan Extension Request'
    _order = 'create_date desc'

    loan_id = fields.Many2one(
        'equipment.loan',
        string='Peminjaman',
        required=True,
        ondelete='cascade'
    )

    requested_due_date = fields.Date(
        string='Tanggal Jatuh Tempo Baru',
        required=True
    )

    reason = fields.Text(
        string='Alasan'
    )

    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='pending',
        required=True
    )

    reviewed_by = fields.Many2one(
        'res.users',
        string='Direview oleh',
        readonly=True
    )

    reviewed_date = fields.Datetime(
        string='Tanggal Review',
        readonly=True
    )

    @api.constrains('requested_due_date', 'loan_id')
    def _check_requested_due_date(self):
        for record in self:
            if (record.loan_id.loan_date
                    and record.requested_due_date < record.loan_id.loan_date):
                raise ValidationError(
                    'Tanggal jatuh tempo baru tidak boleh lebih awal '
                    'dari tanggal peminjaman.'
                )

    def action_approve(self):
        for record in self:
            if record.state != 'pending':
                raise ValidationError(
                    'Hanya request berstatus pending yang dapat diproses.'
                )

            record.loan_id.write({
                'due_date': record.requested_due_date,
            })

            record.write({
                'state': 'approved',
                'reviewed_by': self.env.user.id,
                'reviewed_date': fields.Datetime.now(),
            })

            template = self.env.ref(
                'equipment_loan_tracker.mail_template_extension_approved'
            )
            template.send_mail(record.id, force_send=True)

    def action_reject(self):
        for record in self:
            if record.state != 'pending':
                raise ValidationError(
                    'Hanya request berstatus pending yang dapat diproses.'
                )

            record.write({
                'state': 'rejected',
                'reviewed_by': self.env.user.id,
                'reviewed_date': fields.Datetime.now(),
            })

            template = self.env.ref(
                'equipment_loan_tracker.mail_template_extension_rejected'
            )
            template.send_mail(record.id, force_send=True)