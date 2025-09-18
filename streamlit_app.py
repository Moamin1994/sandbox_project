import os
from some_dalle_library import DalleClient  # Assuming you have a DALL-E client library

# Configuration
DALLE_API_KEY = os.getenv("DALLE_API_KEY")  # Read the DALL-E API key from environment variables

# Initialize DALL-E client
dalle_client = DalleClient(api_key=DALLE_API_KEY)

def generate_architectural_image(prompt):
    # Use the DALL-E API key for image generation
    response = dalle_client.generate_image(prompt)
    return response
