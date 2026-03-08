import json
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable.")
        self.client = openai.OpenAI(api_key=self.api_key)

    def prompt(self, model, prompts, arguments,):
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


        try:
            response = self.client.chat.completions.create(**api_args)
            content = response.choices[0].message.content
            
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
