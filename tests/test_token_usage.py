import unittest
import os
import sys
import pandas as pd
import time

# Add src directory to sys.path to allow importing modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from llm_client import LLMClient, _cached_api_call

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
        # Use a unique prompt to avoid cache hits from previous runs if possible, 
        # or clear cache. But clearing cache might affect other tests or user data.
        # Let's use a timestamp in the prompt to ensure uniqueness for the first call.
        unique_arg = f"French_{time.time()}"
        
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
        arguments = {"language": unique_arg}

        # Construct messages to check cache state manually if needed
        system_prompt = prompts["system_prompt"].format(**arguments)
        user_prompt = prompts["user_prompt"].format(**arguments)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response_format = {"type": "json_schema", "json_schema": {"name": "response_schema", "strict": True, "schema": prompts["constraints"]}}

        # Verify it is NOT in cache initially
        is_cached_before = _cached_api_call.check_call_in_cache(model, messages, response_format, self.client.api_key, self.client.timeout)
        self.assertFalse(is_cached_before, "Prompt should not be in cache initially")
        
        # Make a real call - should be a cache miss
        response = self.client.prompt(model, prompts, arguments)
        
        self.assertIsNotNone(response)
        self.assertIn("message", response)
        
        # Reload the dataframe from disk to ensure it was saved
        if os.path.exists(self.client.token_usage_path):
            usage_df = pd.read_csv(self.client.token_usage_path)
            final_count = len(usage_df)
            
            # Expect count to increase by 1
            self.assertGreater(final_count, self.initial_count, "Token usage record should have been added for new prompt")
            
            # Check the last record
            last_record = usage_df.iloc[-1]
            self.assertEqual(last_record["model"], model)
            self.assertIn(f"Say hello in {unique_arg}", last_record["prompt"])
            self.assertGreater(last_record["input_token_count"], 0)
            self.assertGreater(last_record["output_token_count"], 0)
            self.assertGreater(last_record["price"], 0)
            
            # Verify it IS in cache now
            is_cached_after = _cached_api_call.check_call_in_cache(model, messages, response_format, self.client.api_key, self.client.timeout)
            self.assertTrue(is_cached_after, "Prompt should be in cache after first call")

            # Now make the SAME call again - should be a cache hit
            response_cached = self.client.prompt(model, prompts, arguments)
            self.assertEqual(response, response_cached)
            
            # Reload usage again
            usage_df_cached = pd.read_csv(self.client.token_usage_path)
            final_count_cached = len(usage_df_cached)
            
            # Expect count to remain the same
            self.assertEqual(final_count_cached, final_count, "Token usage record should NOT be added for cached prompt")
            
            print(f"Token usage test passed. Price: ${last_record['price']:.6f}")
        else:
            self.fail("Usage file was not created")

if __name__ == '__main__':
    unittest.main()