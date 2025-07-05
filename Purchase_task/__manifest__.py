# -*- coding: utf-8 -*-
{
    'name': "Custom MRP Kit",
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': "Custom Kit Builder",
    'description': """
    Long description of module's purpose
    """,
    'author': "My Team",
    'depends': ['base','product','stock','sale_management','project','sale_timesheet','mrp'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/assembly_order.xml'
    ],
    'assets':{
        'web.assets_backend':[

        ]},
    'images':[],
    'installable':True,
    'application':True,
    'auto_install':False,
}

