from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestWorkplaceTask(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Workplace = self.env['workplace.workplace']
        self.WorkTask = self.env['workplace.task']
        self.User = self.env['res.users']
        
        self.user1 = self.User.create({
            'name': 'Test User 1',
            'login': 'testuser1',
            'email': 'test1@example.com',
        })
        
        self.user2 = self.User.create({
            'name': 'Test User 2',
            'login': 'testuser2', 
            'email': 'test2@example.com',
        })
        
        self.workplace = self.Workplace.create({
            'name': 'Test Workplace',
            'code': 'WP_TEST_TASK_001',
            'capacity': 2,
            'status': 'available',
            'operator_ids': [(4, self.user1.id), (4, self.user2.id)],
        })

    def test_task_creation(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
            'customer_order_number': '12345',
        })
        
        self.assertEqual(task.name, 'Test Task')
        self.assertEqual(task.workplace_id, self.workplace)
        self.assertEqual(task.status, 'ready')
        self.assertIn(self.user1, task.allowed_operators)

    def test_task_status_constants(self):
        self.assertEqual(self.WorkTask.STATUS_READY, 'ready')
        self.assertEqual(self.WorkTask.STATUS_IN_PROGRESS, 'in_progress')
        self.assertEqual(self.WorkTask.STATUS_COMPLETED, 'completed')
        self.assertEqual(self.WorkTask.STATUS_DEFECT, 'defect')
        self.assertEqual(self.WorkTask.STATUS_CANCELLED, 'cancelled')

    def test_task_color_computation(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        task.write({'status': 'ready'})
        task._compute_color()
        self.assertEqual(task.color, 0)
        
        task.write({'status': 'in_progress'})
        task._compute_color()
        self.assertEqual(task.color, 1)
        
        task.write({'status': 'completed'})
        task._compute_color()
        self.assertEqual(task.color, 10)
        
        task.write({'status': 'defect'})
        task._compute_color()
        self.assertEqual(task.color, 2)
        
        task.write({'status': 'cancelled'})
        task._compute_color()
        self.assertEqual(task.color, 3)

    def test_action_start_work(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        task.with_user(self.user1).action_start_work()
        
        self.assertEqual(task.status, 'in_progress')
        self.assertIn(self.user1, task.operator_ids)
        self.assertIn(self.user1, task.current_operator_ids)
        self.assertIn(self.user1, self.workplace.current_operator_ids)

    def test_action_start_work_validation(self):
        task1 = self.WorkTask.create({
            'name': 'Test Task 1',
            'allowed_operators': [(4, self.user1.id)],
        })
        
        with self.assertRaises(ValidationError):
            task1.action_start_work()

        task2 = self.WorkTask.create({
            'name': 'Test Task 2',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user2.id)],
        })
        
        with self.assertRaises(ValidationError):
            task2.action_start_work()
        
        self.workplace.write({'current_operator_ids': [(4, self.user2.id)]})
        
        task3 = self.WorkTask.create({
            'name': 'Test Task 3',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        with self.assertRaises(ValidationError):
            task3.action_start_work()

    def test_action_complete(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        task.with_user(self.user1).action_start_work()
        self.assertEqual(task.status, 'in_progress')
        
        task.action_complete()
        
        self.assertEqual(task.status, 'completed')
        self.assertEqual(len(task.current_operator_ids), 0)
        self.assertEqual(len(self.workplace.current_operator_ids), 0)

    def test_action_remove_operator(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        task.with_user(self.user1).action_start_work()
        self.assertIn(self.user1, task.current_operator_ids)
        
        task.with_user(self.user1).action_remove_operator()
        
        self.assertNotIn(self.user1, task.current_operator_ids)
        self.assertNotIn(self.user1, self.workplace.current_operator_ids)

    def test_action_remove_operator_not_working(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        with self.assertRaises(ValidationError):
            task.action_remove_operator()

    def test_action_wizards(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        action = task.action_defect()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'workplace.defect.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['active_id'], task.id)
        
        task.with_user(self.user1).action_start_work()
        action = task.with_user(self.user1).action_cancel()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'workplace.cancel.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['active_id'], task.id)
        
        task2 = self.WorkTask.create({
            'name': 'Test Task 2',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
            'status': 'ready',
        })
        
        with self.assertRaises(ValidationError):
            task2.action_cancel()

    def test_clear_all_operators(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        task.with_user(self.user1).action_start_work()
        self.assertIn(self.user1, task.current_operator_ids)
        self.assertIn(self.user1, self.workplace.current_operator_ids)
        
        task._clear_all_operators()
        
        self.assertEqual(len(task.current_operator_ids), 0)
        self.assertNotIn(self.user1, self.workplace.current_operator_ids)

    def test_task_workflow(self):
        task = self.WorkTask.create({
            'name': 'Test Task',
            'workplace_id': self.workplace.id,
            'allowed_operators': [(4, self.user1.id)],
        })
        
        self.assertEqual(task.status, 'ready')
        self.assertEqual(len(task.current_operator_ids), 0)
        
        task.with_user(self.user1).action_start_work()
        self.assertEqual(task.status, 'in_progress')
        self.assertIn(self.user1, task.current_operator_ids)
        
        task.action_complete()
        self.assertEqual(task.status, 'completed')
        self.assertEqual(len(task.current_operator_ids), 0)
