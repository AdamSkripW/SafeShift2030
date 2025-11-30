from app import create_app
import os

# Use production config in Azure, development locally
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
