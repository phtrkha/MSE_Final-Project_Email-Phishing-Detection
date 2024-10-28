import unittest
from app import app

class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_connection(self):
        response = self.app.get('/api/test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Connection successful!', response.data)

    if __name__ == '__main__':
      unittest.main()
