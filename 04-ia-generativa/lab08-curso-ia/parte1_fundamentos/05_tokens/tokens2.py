# Import necessary library (assuming a client similar to OpenAI's API)
import openai

# Set your API key
openai.api_key = 'your-api-key-here'

# Define your input prompt
prompt = "Explain the significance of blockchain technology."

# Set the maximum number of tokens for the output
max_output_tokens = 150

try:
    # Generate content with token limit
    response = openai.Completion.create(
        engine="text-davinci-003",  # Specify the model engine
        prompt=prompt,
        max_tokens=max_output_tokens  # Limit on output tokens
    )

    # Print generated response
    print("Generated Response:")
    print(response.choices[0].text.strip())

    # Display total tokens used in response
    total_tokens = response.usage.total_tokens
    print(f"Total tokens used: {total_tokens}")

except Exception as e:
    print(f"An error occurred: {e}")
