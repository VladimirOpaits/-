from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DefectWizard(models.TransientModel):
    _name = 'workplace.defect.wizard'
    _description = 'Defect Reason Wizard'

    task_id = fields.Many2one('workplace.task', string='Task', required=True)
    defect_reason = fields.Text(string='Defect Reason', required=True, 
                               help='Please describe the reason for the defect')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'task_id' in fields_list and self.env.context.get('active_id'):
            res['task_id'] = self.env.context['active_id']
        return res
    
    def action_confirm_defect(self):
        if not self.defect_reason.strip():  # pyright: ignore[reportAttributeAccessIssue]
            raise ValidationError(_('Defect reason is required.'))
        
        self.task_id.write({  # pyright: ignore[reportAttributeAccessIssue]
            'status': 'defect',
            'defect_reason': self.defect_reason
        })
        
        self.task_id._clear_all_operators()  # pyright: ignore[reportAttributeAccessIssue]
        
        return {'type': 'ir.actions.act_window_close'}
