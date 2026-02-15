from dotenv import load_dotenv
from project import create_app

load_dotenv()

# Create the Flask app instance using the factory
app = create_app()

if __name__ == '__main__':
    # Run the app in debug mode
    app.run(debug =True)
