import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import yaml

# Add src directory to sys.path to allow importing modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from extractor import crawl_coursera_course

class TestAcquisition(unittest.TestCase):


    def test_crawl_coursera_course_live(self):
        """
        Test the crawl_coursera_course function with a real network request.
        """
        url = "https://www.coursera.org/learn/single-variable-calculus"
        
        # Load cookies from config.yaml
        cookies = None
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    cookies = config.get('cookies')
            except Exception as e:
                print(f"Error reading config file: {e}")
        
        # Execute the function with the real URL and cookies
        results = crawl_coursera_course(url, path=None, cookies=cookies)
        
        # Verify that the result is a list (content depends on page accessibility)
        self.assertIsInstance(results, dict)
        self.assertIn("modules", results)
        # If cookies are working, we should find some modules
        if cookies:
            print(f"Found {len(results['modules'])} modules with cookies.")
            self.assertGreater(len(results['modules']), 0, "Should find modules with valid cookies")
        self.assertEqual(len(results["modules"]), 4)
        lessons_count = 0
        for module in results["modules"]:
            lessons_count += len(module["lessons"])
        self.assertEqual(lessons_count, 10)
        last_modules_lessons = [lesson_item["title"] for lesson_item in results["modules"][-1]["lessons"]]
        self.assertIn("Orders of Growth", last_modules_lessons)
if __name__ == '__main__':
    # Create a standard TestSuite as requested
    print("hello")
    suite = unittest.TestSuite()

    suite.addTest(TestAcquisition('test_crawl_coursera_course_live'))

    runner = unittest.TextTestRunner()
    runner.run(suite)