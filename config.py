import os
import json

# Statement for enabling the development environment
DEBUG = True

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection against *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

d = {
    'type': 'service_account',
    'project_id': os.environ['GCP_PROJECT_ID'],
    'private_key_id': os.environ['GCP_PRIVATE_KEY_ID'],
    'private_key': os.environ['GCP_PRIVATE_KEY'].replace("\\n", "\n"),
    'client_email': os.environ['GCP_CLIENT_EMAIL'],
    'client_id': os.environ['GCP_CLIENT_ID'],
    'auth_uri': os.environ['GCP_AUTH_URI'],
    'token_uri': os.environ['GCP_TOKEN_URI'],
    'auth_provider_x509_cert_url': os.environ['GCP_PROVIDER_CERT'],
    'client_x509_cert_url': os.environ['GCP_CLIENT_CERT']
}
with open("back-end-app-67f2d-e6e3ff20ca25.json", "w") as f:
    json.dump(d, f, indent=2)
    print(" * Service account info loaded")
