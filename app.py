"""
Hugging Face Spaces entry point for RequestPayment system.
This file serves as the main entry point for deployment on Hugging Face Spaces.
"""

import os
import sys

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import and launch Gradio app
try:
    from gradio_app import create_interface
    print("Successfully imported gradio_app")
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Create the Gradio interface
app = create_interface()

# For Hugging Face Spaces, we need to expose the app directly
if __name__ == "__main__":
    # Use environment variables for configuration
    port = int(os.environ.get("PORT", 7860))  # Hugging Face Spaces default port
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Launch the Gradio app
    app.launch(
        server_name=host,
        server_port=port,
        share=False,
        debug=False
    ) 