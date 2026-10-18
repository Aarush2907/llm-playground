import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing. Check your .env file.")

client = OpenAI(api_key=api_key)

def call_llm(user_instruction, user_input, model_name="gpt-4o-mini"):
    user_input = user_input.strip()
    user_instruction = user_instruction.strip()

    if not user_input or not user_instruction:
        return "Error: Question and system instructions cannot be empty." , 0.0

    try:
        start_time = time.perf_counter()
        response = client.responses.create(
            model=model_name,
            instructions=user_instruction,
            input=user_input
        )

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        return response , elapsed_time

    except APITimeoutError:
        return "Error: The request timed out." , 0.0

    except APIConnectionError:
        return "Error: Could not connect to the OpenAI API." , 0.0

    except APIStatusError as e:
        return f"API error: HTTP status {e.status_code}" , 0.0 

    except OpenAIError:
        return "Error: An OpenAI SDK error occurred." , 0.0       


def calculate_cost(input_token_price , output_token_price , prompt_tokens , completion_tokens):
    input_price = (input_token_price * prompt_tokens) / 1000000
    output_price = (output_token_price * completion_tokens) / 1000000
    total_price = input_price + output_price
    return input_price , output_price , total_price



user_instruction = input("Enter your system instruction: ")
user_input = input("Enter your question:")
model_name = "gpt-4o-mini"
input_token_price = 0.15
output_token_price = 0.60
result , duration = call_llm(user_instruction , user_input , model_name)                                                       


if isinstance(result, str) and (result.startswith("Error") or result.startswith("API error")):
    print(f"There was an error : {result}")
else :
    prompt_tokens = result.usage.input_tokens
    completion_tokens = result.usage.output_tokens
    total_tokens = result.usage.total_tokens
    output = result.output_text
    input_price , output_price , total_price = calculate_cost(input_token_price , output_token_price , prompt_tokens , completion_tokens)
    print("LLM Request Report")
    print(f'''
    Model : {model_name}
    Latency : {duration} seconds
    Input Tokens : {prompt_tokens}
    Output Tokens : {completion_tokens}
    Total Tokens : {total_tokens}
    Input Cost : {input_price:.6f}$
    Output Cost : {output_price:.6f}$
    Total Cost : {total_price:.6f}$
    ''')

    print(f"Model Response : {output}")