{
    'name': 'Office Asset Loan',
    'version': '19.0.1.0.0',
    'summary': 'Record office assets and who borrows them',
    'description': """
Office Asset Loan
=================
Simple module to record shared office assets and their loans:
who borrows an item, prevent double booking, and track overdue loans.
    """,
    'category': 'Tools',
    'author': 'Muhammad Luthfi Aulia',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/office_asset_loan_sequence.xml',
        'views/office_asset_views.xml',
        'views/office_asset_loan_views.xml',
        'views/office_asset_menus.xml',
    ],
    'application': True,
    'installable': True,
}
