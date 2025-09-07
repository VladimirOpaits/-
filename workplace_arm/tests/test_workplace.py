from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestWorkplace(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Workplace = self.env['workplace.workplace']
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

    def test_workplace_creation(self):
        workplace = self.Workplace.create({
            'name': 'Test Workplace',
            'code': 'WP001',
            'location': 'Test Location',
            'capacity': 2,
            'status': 'available',
            'description': 'Test workplace description',
        })
        
        self.assertEqual(workplace.name, 'Test Workplace')
        self.assertEqual(workplace.code, 'WP001')
        self.assertEqual(workplace.capacity, 2)
        self.assertEqual(workplace.status, 'available')
        self.assertTrue(workplace.active)

    def test_workplace_code_unique(self):
        self.Workplace.create({
            'name': 'Workplace 1',
            'code': 'WP001',
            'capacity': 1,
        })
        
        with self.assertRaises(ValidationError): 
            self.Workplace.create({
                'name': 'Workplace 2',
                'code': 'WP001',
                'capacity': 1,
            })

    def test_workplace_capacity_validation(self):
        with self.assertRaises(ValidationError):
            self.Workplace.create({
                'name': 'Test Workplace',
                'code': 'WP001',
                'capacity': 0, 
            })
        
        with self.assertRaises(ValidationError):
            self.Workplace.create({
                'name': 'Test Workplace',
                'code': 'WP002',
                'capacity': -1,
            })

    def test_workplace_current_operators_capacity(self):
        workplace = self.Workplace.create({
            'name': 'Test Workplace',
            'code': 'WP001',
            'capacity': 1,
        })
        
        workplace.write({'current_operator_ids': [(4, self.user1.id)]})
        self.assertEqual(len(workplace.current_operator_ids), 1)
        
        with self.assertRaises(ValidationError):
            workplace.write({'current_operator_ids': [(4, self.user2.id)]})

    def test_workplace_status_actions(self):
        workplace = self.Workplace.create({
            'name': 'Test Workplace',
            'code': 'WP001',
            'capacity': 1,
            'status': 'available',
        })
        
        workplace.action_set_occupied()
        self.assertEqual(workplace.status, 'occupied')
        
        workplace.action_set_maintenance()
        self.assertEqual(workplace.status, 'maintenance')
        
        workplace.action_set_inactive()
        self.assertEqual(workplace.status, 'inactive')
        
        workplace.action_set_available()
        self.assertEqual(workplace.status, 'available')

    def test_workplace_operator_assignment(self):
        workplace = self.Workplace.create({
            'name': 'Test Workplace',
            'code': 'WP001',
            'capacity': 2,
        })
        
        workplace.write({
            'operator_ids': [(4, self.user1.id), (4, self.user2.id)],
            'current_operator_ids': [(4, self.user1.id)]
        })
        
        self.assertEqual(len(workplace.operator_ids), 2)
        self.assertEqual(len(workplace.current_operator_ids), 1)
        self.assertIn(self.user1, workplace.operator_ids)
        self.assertIn(self.user2, workplace.operator_ids)
        self.assertIn(self.user1, workplace.current_operator_ids)


    def test_workplace_search(self):
        workplace1 = self.Workplace.create({
            'name': 'Workplace A',
            'code': 'WPA',
            'capacity': 1,
            'status': 'available',
        })
        
        workplace2 = self.Workplace.create({
            'name': 'Workplace B',
            'code': 'WPB',
            'capacity': 2,
            'status': 'occupied',
        })
        
        results = self.Workplace.search([('name', 'ilike', 'Workplace A')])
        self.assertIn(workplace1, results)
        self.assertNotIn(workplace2, results)
        
        results = self.Workplace.search([('status', '=', 'available')])
        self.assertIn(workplace1, results)
        self.assertNotIn(workplace2, results)
        
        results = self.Workplace.search([('capacity', '>=', 2)])
        self.assertIn(workplace2, results)
        self.assertNotIn(workplace1, results)
