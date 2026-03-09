import unittest
import os
import sys
import pandas as pd

# Add src directory to sys.path to allow importing modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from llm_client import LLMClient

class TestTokenUsage(unittest.TestCase):

    def setUp(self):
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set, skipping real LLM test")
        self.client = LLMClient()
        
        # Ensure we start with a clean slate or know the initial state if possible, 
        # but since LLMClient loads from disk, we might be appending.
        # We can check the length of the dataframe before and after.
        self.initial_count = len(self.client.usage_df)

    def test_token_usage_tracking(self):
        model = "gpt-4o"
        prompts = {
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "Say hello in {language}.",
            "constraints": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"],
                "additionalProperties": False
            }
        }
        arguments = {"language": "French"}
        
        # Make a real call
        response = self.client.prompt(model, prompts, arguments)
        
        self.assertIsNotNone(response)
        self.assertIn("message", response)
        
        # Reload the dataframe from disk to ensure it was saved
        if os.path.exists(self.client.token_usage_path):
            usage_df = pd.read_csv(self.client.token_usage_path)
            final_count = len(usage_df)
            
            self.assertGreater(final_count, self.initial_count, "Token usage record should have been added")
            
            # Check the last record
            last_record = usage_df.iloc[-1]
            self.assertEqual(last_record["model"], model)
            self.assertIn("Say hello in French", last_record["prompt"])
            self.assertGreater(last_record["input_token_count"], 0)
            self.assertGreater(last_record["output_token_count"], 0)
            self.assertGreater(last_record["price"], 0)
            
            print(f"Token usage test passed. Price: ${last_record['price']:.6f}")
        else:
            self.fail("Usage file was not created")

if __name__ == '__main__':
    unittest.main()