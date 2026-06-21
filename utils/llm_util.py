import openai

from orm.short_term_memory_orm import ShortTermMemoryORM

import logging
logger = logging.getLogger(__name__)




class Llm:
    def __init__(self, base_url, api_key, model_name):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def chat(self, conversation):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=conversation
        )
        return response.choices[0].message.content

        