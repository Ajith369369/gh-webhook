"""
Flask application factory.
"""
from flask import Flask, render_template

from app.extensions import mongo
from app.webhook.routes import webhook


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    # Flask-PyMongo automatically uses MONGO_URI from config
    mongo.init_app(app)
    
    # Register blueprints
    app.register_blueprint(webhook)
    
    # Root route for UI
    @app.route('/')
    def index():
        """Serve the main UI page."""
        return render_template('index.html')
    
    return app
