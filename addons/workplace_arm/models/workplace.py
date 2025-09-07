from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class Workplace(models.Model):
    _name = 'workplace.workplace'
    _description = 'Workplace'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char('Workplace Name', required=True)
    code = fields.Char('Workplace Code', required=True)
    description = fields.Text('Description')
    active = fields.Boolean(default=True, string='Active')
    location = fields.Char('Location')
    capacity = fields.Integer('Capacity', default=1)
    status = fields.Selection([  # pyright: ignore[reportArgumentType]
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive')
    ], 'Status', default='available', required=True)

    manufacturing_order_ids = fields.One2many('mrp.production', 'workplace_id', 'Manufacturing Orders')
    equipment_ids = fields.Many2many('maintenance.equipment', 'Equipment')
    task_ids = fields.One2many('workplace.task', 'workplace_id', 'Tasks')

    operator_ids = fields.Many2many('res.users', 'workplace_operator_rel', 
                                   string='Assigned Operators', 
                                   help='Users who can work on this workplace')
    current_operator_ids = fields.Many2many('res.users', 'workplace_current_operator_rel',
                                           string='Current Operators',
                                           help='Users currently working on this workplace')

    notes = fields.Text('Notes')

    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity <= 0:
                raise ValidationError(_('Capacity must be greater than 0.'))

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if record.code:
                duplicate = self.search([('code', '=', record.code), ('id', '!=', record.id)])
                if duplicate:
                    raise ValidationError(_('Workplace code must be unique.'))

    @api.constrains('current_operator_ids', 'capacity')
    def _check_current_operator_capacity(self):
        for record in self:
            if len(record.current_operator_ids) > record.capacity:
                raise ValidationError(_('Number of current operators cannot exceed workplace capacity.'))

    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_occupied(self):
        self.write({'status': 'occupied'})

    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})

    def action_set_inactive(self):
        self.write({'status': 'inactive'})
    
    

class WorkTask(models.Model):
    _name = 'workplace.task'
    _description = 'Work Task'
    _rec_name = 'name'
    _order = 'name'
    
    STATUS_READY = 'ready'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_DEFECT = 'defect'
    STATUS_CANCELLED = 'cancelled'
    
    
    

    name = fields.Char('Task Name', required=True)
    workplace_id = fields.Many2one('workplace.workplace', string='Workplace')
    operator_ids = fields.Many2many('res.users', 'workplace_task_operator_rel', 
                                   string='Operators')
    current_operator_ids = fields.Many2many('res.users', 'workplace_task_current_operator_rel',
                                           string='Current Operators')
    allowed_operators = fields.Many2many('res.users', 'workplace_task_allowed_operator_rel',
                                        string='Allowed Operators', required=True)
    
    customer_order_number = fields.Char('Customer Order Number')
    order_date = fields.Datetime('Order Date', default=lambda self: fields.Datetime.now())
    
    status = fields.Selection([  # pyright: ignore[reportArgumentType]
        ('ready', 'Ready to Work'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('defect', 'Defect'),
        ('cancelled', 'Cancelled')
    ], default=STATUS_READY, required=True)
    
    color = fields.Integer('Color', compute='_compute_color')
    
    @api.depends('status')
    def _compute_color(self):
        for record in self:
            if record.status == self.STATUS_READY:
                record.color = 0  
            elif record.status == self.STATUS_IN_PROGRESS:
                record.color = 1 
            elif record.status == self.STATUS_COMPLETED:
                record.color = 10  
            elif record.status == self.STATUS_DEFECT:
                record.color = 2  
            else:
                record.color = 3

    defect_reason = fields.Text('Defect Reason')
    notes = fields.Text('Notes')

    def action_start_work(self):
        if not self.workplace_id:
            raise ValidationError(_('Workplace is required to start work.'))
        
        if not self.allowed_operators or self.env.user not in self.allowed_operators:
            raise ValidationError(_('You are not allowed to work on this task.'))
        
        if len(self.workplace_id.current_operator_ids) >= self.workplace_id.capacity:  # pyright: ignore[reportAttributeAccessIssue]
            raise ValidationError(_('Workplace capacity is full. Cannot start work.'))
        
        self.workplace_id.write({'current_operator_ids': [(4, self.env.user.id)]})  # pyright: ignore[reportAttributeAccessIssue]
        
        self.write({
            'status': 'in_progress',
            'operator_ids': [(4, self.env.user.id)],
            'current_operator_ids': [(4, self.env.user.id)] 
        })

    def _clear_all_operators(self):
        workplace = self.workplace_id
        if workplace:
            workplace.write({'current_operator_ids': [(3, op.id) for op in self.current_operator_ids]})  # pyright: ignore[reportAttributeAccessIssue]
        self.write({'current_operator_ids': [(5, 0, 0)]})

    def action_complete(self):
        self.write({'status': self.STATUS_COMPLETED})
        self._clear_all_operators()
    
    def action_remove_operator(self):
        if self.env.user not in self.current_operator_ids:
            raise ValidationError(_('You are not currently working on this task.'))
        
        self.write({'current_operator_ids': [(3, self.env.user.id)]})
        
        workplace = self.workplace_id
        other_active_tasks = self.env['workplace.task'].search([
            ('workplace_id', '=', workplace.id),  # pyright: ignore[reportAttributeAccessIssue]
            ('current_operator_ids', 'in', self.env.user.id),
            ('status', '=', self.STATUS_IN_PROGRESS),
            ('id', '!=', self.id)
        ])
        
        if not other_active_tasks:
            workplace.write({'current_operator_ids': [(3, self.env.user.id)]})  # pyright: ignore[reportAttributeAccessIssue]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_defect(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Defect Reason'),
            'res_model': 'workplace.defect.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }

    def action_cancel(self):
        if self.status != self.STATUS_IN_PROGRESS:
            raise ValidationError(_('Task is not in progress. Cannot cancel.'))
        
        if self.env.user not in self.current_operator_ids:
            raise ValidationError(_('You are not currently working on this task.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Task'),
            'res_model': 'workplace.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }
    
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if groupby and groupby[0] == 'status':
            result = super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
            
            all_statuses = [self.STATUS_READY, self.STATUS_IN_PROGRESS, self.STATUS_COMPLETED, self.STATUS_DEFECT, self.STATUS_CANCELLED]
            existing_statuses = {group['status'] for group in result if 'status' in group}
            
            for status in all_statuses:
                if status not in existing_statuses:
                    result.append({
                        'status': status,
                        'status_count': 0,
                        '__domain': domain + [('status', '=', status)]
                    })
            
            result.sort(key=lambda x: all_statuses.index(x['status']))
            return result
        
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
    
