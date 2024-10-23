# -*- coding: utf-8 -*-
# Coded by German Ponce Dominguez 
#     ▬▬▬▬▬.◙.▬▬▬▬▬  
#       ▂▄▄▓▄▄▂  
#    ◢◤█▀▀████▄▄▄▄▄▄ ◢◤  
#    █▄ █ █▄ ███▀▀▀▀▀▀▀ ╬  
#    ◥ █████ ◤  
#     ══╩══╩═  
#       ╬═╬  
#       ╬═╬ Dream big and start with something small!!!  
#       ╬═╬  
#       ╬═╬ You can do it!  
#       ╬═╬   Let's go...
#    ☻/ ╬═╬   
#   /▌  ╬═╬   
#   / \
# Cherman Seingalt - german.ponce@outlook.com

from odoo import api, tools, SUPERUSER_ID
from datetime import date
import logging
_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("### Actualizamos el tipo de Acuerdo >>>>>>>>> ")
    cr.execute("update purchase_requisition set type_of_agreement='standard';")
    cr.execute("""update purchase_requisition set department_id=hr_employee.department_id 
                    from hr_employee where hr_employee.user_id = purchase_requisition.user_id;""")
    