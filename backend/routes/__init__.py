def register_routes(app):
    """Attach all route blueprints to the Flask app."""
  
    from .health import health_bp
    from .readiness import readiness_bp

    # Merges each blueprint's routes into the main app
    app.register_blueprint(health_bp)
    app.register_blueprint(readiness_bp)
