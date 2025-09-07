from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CancelWizard(models.TransientModel):
    _name = 'workplace.cancel.wizard'
    _description = 'Cancel Task Wizard'

    task_id = fields.Many2one('workplace.task', string='Task', required=True)
    cancel_reason = fields.Text(string='Cancel Reason', required=True, 
                               help='Please describe the reason for cancelling this task')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'task_id' in fields_list and self.env.context.get('active_id'):
            res['task_id'] = self.env.context['active_id']
        return res
    
    def action_confirm_cancel(self):
        if not self.cancel_reason.strip():  # pyright: ignore[reportAttributeAccessIssue]
            raise ValidationError(_('Cancel reason is required.'))
        
        self.task_id.write({  # pyright: ignore[reportAttributeAccessIssue]
            'status': 'cancelled',
            'notes': f"Отменено: {self.cancel_reason}"
        })
        
        self.task_id._clear_all_operators()  # pyright: ignore[reportAttributeAccessIssue]
        
        return {'type': 'ir.actions.act_window_close'}
