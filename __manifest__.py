# -*- coding: utf-8 -*-
{
    'name': 'Kardex Inventario Excel',
    'version': '10.0.0.1',
    'category': 'Custom',
    'sequence': 14,
    'summary': 'Kardex Inventario',
    'author': 'MCM',
    'depends': ['product',
                'account',
                'stock',
                'stock_account',
                'report_xlsx',
                'sale',
                'sales_team'],
    'data': [
        'report/report_xlsx.xml',
        'report/detalle_ventas_view.xml',
        'wizard/kardex_inventario_wizard_view.xml',
        'report/report_payment.xml',
        'report/report.xml',
        'security/ir.model.access.csv'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
