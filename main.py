
import os
import time

from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAIError,
)

from database import create_table, save_request, get_recent_requests
from schemas import FeedbackAnalysis


# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing. Check your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Initialize database
create_table()

MODEL_NAME = "gpt-4o-mini"

# USD per million tokens; verify current pricing before relying on estimates.
INPUT_TOKEN_PRICE = 0.15
OUTPUT_TOKEN_PRICE = 0.60


def call_llm(user_instruction, user_input, model_name=MODEL_NAME):
    user_instruction = user_instruction.strip()
    user_input = user_input.strip()

    if not user_instruction or not user_input:
        return "Error: Question and system instructions cannot be empty.", 0.0

    try:
        start_time = time.perf_counter()

        response = client.responses.create(
            model=model_name,
            instructions=user_instruction,
            input=user_input,
        )

        elapsed_time = time.perf_counter() - start_time
        return response, elapsed_time

    except APITimeoutError:
        return "Error: The request timed out.", 0.0

    except APIConnectionError:
        return "Error: Could not connect to the OpenAI API.", 0.0

    except APIStatusError as e:
        return f"API error: HTTP status {e.status_code}", 0.0

    except OpenAIError:
        return "Error: An OpenAI SDK error occurred.", 0.0


def calculate_cost(
    input_token_price,
    output_token_price,
    prompt_tokens,
    completion_tokens,
):
    input_price = (input_token_price * prompt_tokens) / 1_000_000
    output_price = (output_token_price * completion_tokens) / 1_000_000
    total_price = input_price + output_price

    return input_price, output_price, total_price


def show_request_history(limit=10):
    rows = get_recent_requests(limit)

    if not rows:
        print("\nThere is no history yet.")
        return

    print(f"\nShowing {len(rows)} recent request(s)")
    print("=" * 60)

    for row in rows:
        print(f"""
ID: {row[0]}
Model: {row[1]}
Question: {row[3]}
Response: {row[4]}
Latency: {row[5]:.3f} seconds
Input Tokens: {row[6]}
Output Tokens: {row[7]}
Total Tokens: {row[8]}
Total Cost: ${row[11]:.8f}
Created At: {row[12]}
{"-" * 60}""")


def analyze_feedback(raw_feedback, model_name=MODEL_NAME):
    raw_feedback = raw_feedback.strip()

    if not raw_feedback:
        print("Please enter valid, non-empty feedback.")
        return None

    try:
        response = client.responses.parse(
            model=model_name,
            instructions=(
                "Analyze the customer feedback. Classify sentiment as positive, "
                "negative, or neutral. Assign low, medium, or high priority. "
                "Choose a concise category and provide a short summary."
            ),
            input=raw_feedback,
            text_format=FeedbackAnalysis,
        )

        analysis: FeedbackAnalysis = response.output_parsed

        if analysis is None:
            print("No structured analysis was returned.")
            return None

        print("\nFeedback Analysis")
        print(f"Sentiment: {analysis.sentiment}")
        print(f"Category:  {analysis.category}")
        print(f"Priority:  {analysis.priority}")
        print(f"Summary:   {analysis.summary}")

        return analysis

    except APITimeoutError:
        print("Error: The feedback analysis request timed out.")

    except APIConnectionError:
        print("Error: Could not connect to the OpenAI API.")

    except APIStatusError as e:
        print(f"API error: HTTP status {e.status_code}")

    except OpenAIError:
        print("Error: An OpenAI SDK error occurred.")

    return None


def make_llm_request():
    user_instruction = input("\nEnter your system instruction: ")
    user_input = input("Enter your question: ")

    result, duration = call_llm(
        user_instruction,
        user_input,
        MODEL_NAME,
    )

    if isinstance(result, str):
        print(f"\nThere was an error: {result}")
        return

    prompt_tokens = result.usage.input_tokens
    completion_tokens = result.usage.output_tokens
    total_tokens = result.usage.total_tokens
    output = result.output_text

    input_price, output_price, total_price = calculate_cost(
        INPUT_TOKEN_PRICE,
        OUTPUT_TOKEN_PRICE,
        prompt_tokens,
        completion_tokens,
    )

    print("\nLLM Request Report")
    print(f"""
Model: {MODEL_NAME}
Latency: {duration:.3f} seconds
Input Tokens: {prompt_tokens}
Output Tokens: {completion_tokens}
Total Tokens: {total_tokens}
Input Cost: ${input_price:.8f}
Output Cost: ${output_price:.8f}
Total Cost: ${total_price:.8f}
""")

    try:
        save_request(
            MODEL_NAME,
            user_instruction,
            user_input,
            output,
            duration,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            input_price,
            output_price,
            total_price,
        )
        print("Request saved successfully.")

    except Exception as e:
        print(f"Warning: The API request succeeded, but saving failed: {e}")

    print(f"\nModel Response:\n{output}")


def main():
    while True:
        print("""
========== LLM Engineering Playground ==========

1. Make a new LLM request
2. View recent request history
3. Analyze customer feedback (structured output)
4. Exit

================================================
""")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            make_llm_request()

        elif choice == "2":
            limit_input = input(
                "How many recent requests do you want to view? "
            ).strip()

            try:
                limit = int(limit_input)

                if limit <= 0:
                    print("Please enter a positive number.")
                    continue

                show_request_history(limit)

            except ValueError:
                print("Invalid input. Please enter a whole number.")

        elif choice == "3":
            raw_feedback = input("Enter customer feedback: ")
            analyze_feedback(raw_feedback)

        elif choice == "4":
            print("Exiting LLM Engineering Playground. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
