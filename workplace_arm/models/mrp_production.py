from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    workplace_id = fields.Many2one('workplace.workplace', string='Workplace')
