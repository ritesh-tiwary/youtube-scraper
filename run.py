# Run a test server.
from app import app
app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)

