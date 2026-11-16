from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class OfficeAssetLoan(models.Model):
    _name = 'office.asset.loan'
    _description = 'Office Asset Loan'
    _order = 'id desc'

    name = fields.Char(
        string='Loan Number',
        readonly=True,
        copy=False,
        default='New',
    )
    asset_id = fields.Many2one(
        comodel_name='office.asset',
        string='Asset',
        required=True,
        ondelete='restrict',
    )
    borrower_id = fields.Many2one(
        comodel_name='res.users',
        string='Borrower',
        required=True,
        default=lambda self: self.env.user,
    )
    loan_date = fields.Date(
        string='Loan Date',
        required=True,
        default=fields.Date.context_today,
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        default=lambda self: (
            fields.Date.context_today(self) + timedelta(days=7)
        ),
    )
    return_date = fields.Date(
        string='Return Date',
        readonly=True,
        copy=False,
    )
    purpose = fields.Char(string='Purpose')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('borrowed', 'Borrowed'),
            ('returned', 'Returned'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
    )
    duration_days = fields.Integer(
        string='Duration (Days)',
        compute='_compute_duration_days',
    )
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
    )

    @api.depends('loan_date', 'due_date')
    def _compute_duration_days(self):
        for record in self:
            if record.loan_date and record.due_date:
                delta = record.due_date - record.loan_date
                record.duration_days = delta.days
            else:
                record.duration_days = 0

    @api.depends('state', 'due_date')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.state == 'borrowed'
                and record.due_date
                and record.due_date < today
            )

    # BR-2
    @api.constrains('loan_date', 'due_date')
    def _check_due_date(self):
        for record in self:
            if (
                record.loan_date
                and record.due_date
                and record.due_date < record.loan_date
            ):
                raise ValidationError(
                    "The due date cannot be earlier than the loan date."
                )

    # BR-8
    @api.onchange('loan_date')
    def _onchange_loan_date(self):
        for record in self:
            if record.loan_date and (
                not record.due_date or record.due_date < record.loan_date
            ):
                record.due_date = record.loan_date + timedelta(days=7)

    # BR-3
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('office.asset.loan')
                    or 'New'
                )
        return super().create(vals_list)

    # BR-7
    @api.ondelete(at_uninstall=False)
    def _unlink_except_borrowed_or_returned(self):
        for record in self:
            if record.state in ('borrowed', 'returned'):
                raise UserError(
                    "You cannot delete a loan that is Borrowed or Returned."
                )

    # BR-4
    def action_borrow(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("Only draft loans can be borrowed.")
            if record.asset_id.condition == 'damaged':
                raise UserError(
                    "Asset '%s' is damaged and cannot be borrowed."
                    % record.asset_id.display_name
                )
            other_loans = self.search_count([
                ('asset_id', '=', record.asset_id.id),
                ('state', '=', 'borrowed'),
                ('id', '!=', record.id),
            ])
            if other_loans:
                raise UserError(
                    "Asset '%s' is currently borrowed by another loan."
                    % record.asset_id.display_name
                )
            record.state = 'borrowed'

    # BR-5
    def action_return(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != 'borrowed':
                raise UserError("Only borrowed loans can be returned.")
            record.write({'return_date': today, 'state': 'returned'})

    # BR-6
    def action_cancel(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("Only draft loans can be cancelled.")
            record.state = 'cancelled'
