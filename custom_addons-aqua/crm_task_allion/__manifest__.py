{
    'name': 'Create Task from Lead',
    'version': '11.0.0.1',
    'category': 'CRM',
    'description': """
    Task on Lead, Add Task from lead, Task Lead, Create Project Task from Lead, Add task from mail, Create task from mail.Task on lead, add task on lead, tasks on lead, lead tasks, automated task by lead, Generate task from lead.
""",
    'author': "Allion Technologies PVT Ltd",
    'website': 'www.alliontechnologies.com',
    'images': [],
    'depends': ['base', 'crm', 'sale', 'project'],

    'data': [
        'views/crm_lead_view.xml',
        'views/project_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    "images": [],
}
