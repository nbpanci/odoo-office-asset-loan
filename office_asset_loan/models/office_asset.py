from odoo import api, fields, models


class OfficeAsset(models.Model):
    _name = 'office.asset'
    _description = 'Office Asset'
    _order = 'code'

    name = fields.Char(string='Asset Name', required=True)
    code = fields.Char(string='Asset Code', required=True)
    category = fields.Selection(
        selection=[
            ('electronics', 'Electronics'),
            ('furniture', 'Furniture'),
            ('vehicle', 'Vehicle'),
            ('other', 'Other'),
        ],
        string='Category',
        default='electronics',
        required=True,
    )
    purchase_date = fields.Date(string='Purchase Date')
    condition = fields.Selection(
        selection=[
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('damaged', 'Damaged'),
        ],
        string='Condition',
        default='good',
        required=True,
    )
    note = fields.Text(string='Note')
    active = fields.Boolean(default=True)
    loan_ids = fields.One2many(
        comodel_name='office.asset.loan',
        inverse_name='asset_id',
        string='Loans',
    )
    is_available = fields.Boolean(
        string='Available',
        compute='_compute_is_available',
        search='_search_is_available',
    )
    loan_count = fields.Integer(
        string='Loan Count',
        compute='_compute_loan_count',
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Asset code must be unique!',
    )

    @api.depends('loan_ids.state')
    def _compute_is_available(self):
        for record in self:
            record.is_available = not any(
                loan.state == 'borrowed' for loan in record.loan_ids
            )

    def _search_is_available(self, operator, value):
        """Allow filtering on the non-stored ``is_available`` field."""
        if operator not in ('=', '!=') or not isinstance(value, bool):
            return NotImplemented
        available = (operator == '=') == value
        return [(
            'loan_ids',
            'not any' if available else 'any',
            [('state', '=', 'borrowed')],
        )]

    @api.depends('loan_ids')
    def _compute_loan_count(self):
        for record in self:
            record.loan_count = len(record.loan_ids)
