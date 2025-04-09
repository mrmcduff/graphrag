"""
Automated tests for the GraphRAG Text Adventure Game API.

This module provides automated tests for the API endpoints.
"""
import unittest
import requests
import time
import threading
import json
import sys
import os
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the API server
from src.api.server import create_app


class APITestCase(unittest.TestCase):
    """Test case for the GraphRAG API."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test case by starting the API server."""
        # Create the Flask app
        cls.app = create_app({'TESTING': True})
        
        # Start the server in a separate thread
        cls.server_thread = threading.Thread(target=cls.app.run, 
                                            kwargs={'host': 'localhost', 'port': 5555, 'debug': False})
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for the server to start
        time.sleep(2)
        
        # Base URL for API requests
        cls.api_url = 'http://localhost:5555/api'
        
        # Session ID for tests
        cls.session_id = None
    
    def test_01_create_new_game(self):
        """Test creating a new game session."""
        response = requests.post(f"{self.api_url}/game/new", json={
            "game_data_dir": "data/output"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Save the session ID for other tests
        self.__class__.session_id = data.get('session_id')
        
        self.assertIsNotNone(self.__class__.session_id)
        self.assertIn('welcome_message', data)
        self.assertIn('player_location', data)
        self.assertIn('content', data)
        self.assertIn('metadata', data)
    
    def test_02_process_command(self):
        """Test processing a command."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.post(f"{self.api_url}/game/{self.__class__.session_id}/command", json={
            "command": "look around"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('success', data)
        self.assertIn('content', data)
        self.assertTrue(len(data['content']) > 0)
    
    def test_03_get_game_state(self):
        """Test getting the game state."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.get(f"{self.api_url}/game/{self.__class__.session_id}/state")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('player_location', data)
        self.assertIn('inventory', data)
        self.assertIn('npcs_present', data)
        self.assertIn('items_present', data)
        self.assertIn('combat_active', data)
        self.assertIn('metadata', data)
    
    def test_04_set_llm_provider(self):
        """Test setting the LLM provider."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.post(f"{self.api_url}/game/{self.__class__.session_id}/llm", json={
            "provider_id": 3  # OpenAI
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
    
    def test_05_save_game(self):
        """Test saving the game."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.post(f"{self.api_url}/game/{self.__class__.session_id}/save", json={
            "filename": f"test_save_{self.__class__.session_id}.json"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
    
    def test_06_load_game(self):
        """Test loading the game."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.post(f"{self.api_url}/game/{self.__class__.session_id}/load", json={
            "filename": f"test_save_{self.__class__.session_id}.json"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('player_location', data)
    
    def test_07_invalid_command(self):
        """Test sending an invalid command."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.post(f"{self.api_url}/game/{self.__class__.session_id}/command", json={
            "command": ""  # Empty command
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertIn('message', data)
    
    def test_08_invalid_session_id(self):
        """Test using an invalid session ID."""
        response = requests.get(f"{self.api_url}/game/invalid-session-id/state")
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertIn('message', data)
    
    def test_09_end_game_session(self):
        """Test ending the game session."""
        if not self.__class__.session_id:
            self.skipTest("No active session ID")
        
        response = requests.delete(f"{self.api_url}/game/{self.__class__.session_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        
        # Verify the session is really gone
        response = requests.get(f"{self.api_url}/game/{self.__class__.session_id}/state")
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
