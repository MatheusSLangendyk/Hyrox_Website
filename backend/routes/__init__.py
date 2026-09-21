def register_routes(app):
    """Attach all route blueprints to the Flask app."""
    from .health import health_bp

    app.register_blueprint(health_bp)
