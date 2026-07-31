"""
WSGI entry point for production deployment.
"""
from app import create_app
from config import ProductionConfig
import os

# Create application instance
app = create_app(ProductionConfig)

if __name__ == "__main__":
    app.run()
