import json
import random
import time
import pandas as pd
import tiktoken
import openai
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable.")
        self.client = openai.OpenAI(api_key=self.api_key, timeout=1900.0)
        self.token_usage = []

        # Default pricing per 1M tokens
        self.pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
        }
        
        # Load usage path and pricing from config
        self.token_usage_path = "data/usage.csv"

        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config:
                        if 'token_usage_path' in config:
                            self.token_usage_path = config['token_usage_path']
                        if 'model_pricing' in config:
                            self.pricing.update(config['model_pricing'])
            except Exception as e:
                print(f"Error reading config: {e}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.token_usage_path), exist_ok=True)
        
        # Preload usage dataframe
        if os.path.exists(self.token_usage_path):
            try:
                self.usage_df = pd.read_csv(self.token_usage_path)
            except Exception:
                self.usage_df = pd.DataFrame(columns=["model", "prompt", "input_token_count", "output_token_count", "price", "arguments"])
        else:
            self.usage_df = pd.DataFrame(columns=["model", "prompt", "input_token_count", "output_token_count", "price", "arguments"])

    def _calculate_tokens(self, text, model="gpt-4o"):
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def _save_usage(self, usage_record):
        new_row = pd.DataFrame([usage_record])
        # Ensure arguments is the last column
        cols = ["model", "prompt", "input_token_count", "output_token_count", "price", "arguments"]
        self.usage_df = pd.concat([self.usage_df, new_row], ignore_index=True)
        
        # Reorder columns before saving
        self.usage_df = self.usage_df[cols]
        
        try:
            self.usage_df.to_csv(self.token_usage_path, index=False)
        except Exception as e:
            print(f"Failed to save usage data: {e}")

    def prompt(self, model, prompts, arguments, constraints=None):
        """
        Generates a response from the LLM based on the provided prompts and arguments.

        Args:
            model (str): The model to use (e.g., "gpt-4-turbo", "gpt-3.5-turbo").
            prompts (dict): A dictionary containing "system_prompt" and "user_prompt".
                            These can be strings or lists of strings.
            arguments (dict): A dictionary of arguments to format the prompts.
            constraints (dict, optional): Constraints to enforce specific decoding (e.g., JSON schema).

        Returns:
            dict: The parsed JSON response from the LLM.
        """
        time.sleep(random.randint(1,3))
        system_prompt_template = prompts.get("system_prompt", "")
        user_prompt_template = prompts.get("user_prompt", "")

        if isinstance(system_prompt_template, list):
            system_prompt_template = "\n".join(system_prompt_template)
        if isinstance(user_prompt_template, list):
            user_prompt_template = "\n".join(user_prompt_template)
        try:
            system_prompt = system_prompt_template.format(**arguments)
            user_prompt = user_prompt_template.format(**arguments)
        except KeyError as e:
            raise ValueError(f"Missing argument for prompt formatting: {e}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Prepare API call arguments
        api_args = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"} # Enforce JSON output
        }
        
        # Use constraints passed as argument or from prompts dict if not passed
        if constraints is None:
            constraints = prompts.get("constraints", None)
            
        if constraints:
             # Use strict JSON schema enforcement if constraints are provided
             api_args["response_format"] = {
                 "type": "json_schema",
                 "json_schema": {
                     "name": "response_schema",
                     "strict": True,
                     "schema": constraints
                 }
             }

        # Calculate input tokens
        input_text = system_prompt + "\n" + user_prompt
        input_tokens = self._calculate_tokens(input_text, model)

        try:
            response = self.client.chat.completions.create(**api_args)
            content = response.choices[0].message.content
            
            output_tokens = self._calculate_tokens(content, model)
            
            price = 0.0
            if model in self.pricing:
                price = (input_tokens / 1000000 * self.pricing[model]["input"]) + \
                        (output_tokens / 1000000 * self.pricing[model]["output"])
            else:
                print(f"Warning: Model {model} not in pricing table. Price set to 0.")
            
            # Log usage
            usage_record = {
                "model": model,
                "prompt": user_prompt[:100] + "...", # Store truncated prompt
                "input_token_count": input_tokens,
                "output_token_count": output_tokens,
                "price": price,
                "arguments": str(arguments)
            }
            self._save_usage(usage_record)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != -1:
                     return json.loads(content[start:end])
                raise ValueError(f"Failed to parse JSON from LLM response: {content}")

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
