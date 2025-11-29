from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Backend is running'})

@main_bp.route('/api/', methods=['GET'])
def index():
    return jsonify({'message': 'Welcome to the API'})
