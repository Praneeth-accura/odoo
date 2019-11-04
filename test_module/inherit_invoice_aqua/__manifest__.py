{
    'name': 'Inherit Invoice Aqua',
    'version': '1.0',
    'sequence': 0,
    'author': "Onestep Solutions",
    'website': 'https://onestep.lk/',
    'summary': 'Inherit Invoice',
    'description': """Inherit Invoice By Onestep""",
    'depends': ['sale', 'purchase', 'stock'],
    'data': [
            'tax_invoice.xml',
            'delivery_report_inherit.xml',
            'purchase_order.xml',
            'purchase_order_template_inherit.xml',
            'stock_inventory_view_inherit.xml',
            'report/report_with_value_diff.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
