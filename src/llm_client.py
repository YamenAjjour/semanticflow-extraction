import json
import random
import time
import pandas as pd
import tiktoken
import openai
import os
import yaml
from dotenv import load_dotenv
from joblib import Memory

load_dotenv()

# --- Module-level Cache Setup ---
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
cache_dir = "data/cache" # Default
if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config and 'cache' in config:
                cache_dir = config['cache']
    except Exception as e:
        print(f"Error reading config for cache path: {e}")

os.makedirs(cache_dir, exist_ok=True)
memory = Memory(cache_dir, verbose=0)

@memory.cache
def _cached_api_call(model, messages, response_format, api_key, timeout):
    """
    A pure, cached function to make the OpenAI API call.
    This is at the module level to avoid issues with caching instance methods.
    :param model: The model to use.
    :param messages: The list of messages for the chat completion.
    :param response_format: The format of the response (e.g., json_object).
    :param api_key: The OpenAI API key.
    :param timeout: The timeout for the API call.
    :return: The content of the response message.
    """
    print("Cache miss. Calling OpenAI API...")
    time.sleep(random.randint(0,2))
    client = openai.OpenAI(api_key=api_key, timeout=timeout)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format
    )
    return response.choices[0].message.content

# --- LLMClient Class ---
class LLMClient:
    """
    A client for interacting with the OpenAI API, with support for caching and token usage tracking.
    """
    def __init__(self, api_key=None):
        """
        Initializes the LLMClient.
        :param api_key: The OpenAI API key. If not provided, it will be read from the OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable.")
        self.timeout = 1900.0
        
        # Default pricing per 1M tokens
        self.pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
        }
        
        # Load usage path and pricing from config
        self.token_usage_path = "data/usage.csv"
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
        """
        Calculates the number of tokens in a text string for a given model.
        :param text: The text to calculate tokens for.
        :param model: The model name.
        :return: The number of tokens.
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def _save_usage(self, usage_record):
        """
        Saves a usage record to the usage CSV file.
        :param usage_record: A dictionary containing usage details.
        """
        new_row = pd.DataFrame([usage_record])
        cols = ["model", "prompt", "input_token_count", "output_token_count", "price", "arguments"]
        self.usage_df = pd.concat([self.usage_df, new_row], ignore_index=True)
        self.usage_df = self.usage_df[cols]
        try:
            self.usage_df.to_csv(self.token_usage_path, index=False)
        except Exception as e:
            print(f"Failed to save usage data: {e}")

    def prompt(self, model, prompts, arguments, constraints=None):
        """
        Generates a response from the LLM based on the provided prompts and arguments.
        :param model: The model to use (e.g., "gpt-4-turbo", "gpt-3.5-turbo").
        :param prompts: A dictionary containing "system_prompt" and "user_prompt".
        :param arguments: A dictionary of arguments to format the prompts.
        :param constraints: Constraints to enforce specific decoding (e.g., JSON schema).
        :return: The parsed JSON response from the LLM.
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

        response_format = {"type": "json_object"}
        if constraints is None:
            constraints = prompts.get("constraints", None)
        if constraints:
             response_format = {
                 "type": "json_schema",
                 "json_schema": {
                     "name": "response_schema",
                     "strict": True,
                     "schema": constraints
                 }
             }

        try:
            # Check cache before calling
            is_cached = _cached_api_call.check_call_in_cache(model, messages, response_format, self.api_key, self.timeout)
            
            content = _cached_api_call(model, messages, response_format, self.api_key, self.timeout)
            
            if not is_cached:
                input_text = system_prompt + "\n" + user_prompt
                input_tokens = self._calculate_tokens(input_text, model)
                output_tokens = self._calculate_tokens(content, model)
                
                price = 0.0
                if model in self.pricing:
                    price = (input_tokens / 1000000 * self.pricing[model]["input"]) + \
                            (output_tokens / 1000000 * self.pricing[model]["output"])
                else:
                    print(f"Warning: Model {model} not in pricing table. Price set to 0.")
                
                usage_record = {
                    "model": model,
                    "prompt": user_prompt[:100] + "...",
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
