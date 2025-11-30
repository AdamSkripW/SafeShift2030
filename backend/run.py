from app import create_app
import os
import logging

# Zapni logging
logging.basicConfig(level=logging.DEBUG)

# Use production config in Azure, development locally
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

# Pridaj error handler na globálne chyby
@app.errorhandler(Exception)
def handle_error(error):
    import traceback
    print(f"\n❌ GLOBAL ERROR CAUGHT:")
    print(f"Error: {str(error)}")
    print(f"Type: {type(error).__name__}")
    traceback.print_exc()
    return {"error": str(error), "success": False}, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
