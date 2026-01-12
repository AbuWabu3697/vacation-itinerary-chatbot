from openai import OpenAI

class OpenAPI: 
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate_response(self, prompt):
        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        return response.output_text

