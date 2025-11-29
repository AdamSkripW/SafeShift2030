"""
SafeShift 2030 - Backend Flask Application
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db, User, Hospital, Shift

# Initialize extensions
jwt = JWTManager()

def create_app():
    """Create and configure Flask app"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    
    # Enable CORS
    CORS(app, origins=['http://localhost:4200', 'http://localhost:3000'])
    
    # ============================================
    # ROUTES - HEALTH CHECK
    # ============================================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Check if backend is running"""
        return jsonify({
            'status': 'ok',
            'message': 'SafeShift 2030 Backend is running ✓'
        }), 200
    
    # ============================================
    # ERROR HANDLERS
    # ============================================
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # ============================================
    # IMPORT & REGISTER BLUEPRINTS
    # ============================================
    
    from safeshift.routes.auth import auth_bp
    from safeshift.routes.shifts import shifts_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(shifts_bp)
    
    return app

# Create app instance for running
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created/verified")
        except Exception as e:
            print(f"⚠ Error creating tables: {str(e)}")
    
    print("🚀 Starting SafeShift 2030 Backend...")
    app.run(debug=True, host='0.0.0.0', port=5000)
