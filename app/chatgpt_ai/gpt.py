import os

import openai
from dotenv import load_dotenv
import logging

load_dotenv()

openai.api_key = os.getenv("CHATGPT_API_KEY")


def chatgpt_response(msg):
    logging.info(msg)
    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=msg,
            # temperature=0.4,
            max_tokens=1000,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0.5,
            )
    # response_dict = response.get("choices")
    # if response_dict and len(response_dict) > 0:
    #     prompt_response = response_dict[0]['message']['content']
    logging.info(response)
    return response
