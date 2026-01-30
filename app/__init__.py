"""
Flask application factory.
"""
import os
from flask import Flask, render_template

from app.extensions import mongo
from app.webhook.routes import webhook


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """

    # Get the base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
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
