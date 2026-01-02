import webbrowser
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from PyQt6.QtCore import QThread, pyqtSignal

# ==========================================
# GOOGLE AUTH WORKER
# ==========================================

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles the callback from Google after user logs in."""
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/callback":
            query = parse_qs(parsed_path.query)
            if 'code' in query:
                self.server.auth_code = query['code'][0]
                
                # Send a nice response to the browser
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <html><body style="font-family: sans-serif; text-align: center; background-color: #2b2b2b; color: white; padding-top: 50px;">
                    <h1>Login Successful</h1>
                    <p>You can close this window and return to NexaShield.</p>
                    <script>window.close()</script>
                </body></html>
                """
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_error(400, "Authorization code not found")
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        pass  # Suppress console logging

class GoogleAuthWorker(QThread):
    auth_success = pyqtSignal(dict)  # Returns user info (email, name, picture)
    auth_error = pyqtSignal(str)

    def __init__(self, client_id, client_secret, redirect_port=5000):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_port = redirect_port
        self.redirect_uri = f"http://127.0.0.1:{redirect_port}/callback"

    def run(self):
        try:
            # 1. Construct Auth URL
            auth_url = (
                f"https://accounts.google.com/o/oauth2/auth?"
                f"response_type=code&client_id={self.client_id}&"
                f"redirect_uri={self.redirect_uri}&"
                f"scope=openid%20email%20profile"
            )

            # 2. Start Local Server to listen for the callback
            server = HTTPServer(('127.0.0.1', self.redirect_port), OAuthCallbackHandler)
            server.auth_code = None

            # 3. Open System Browser
            webbrowser.open(auth_url)

            # 4. Wait for the callback (handle requests until we get the code)
            while not server.auth_code:
                server.handle_request()

            # 5. Exchange Code for Access Token
            token_data = {
                'code': server.auth_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post("https://oauth2.googleapis.com/token", data=token_data)
            tokens = response.json()

            if 'access_token' in tokens:
                # 6. Fetch User Info
                user_info_resp = requests.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    headers={'Authorization': f"Bearer {tokens['access_token']}"}
                )
                self.auth_success.emit(user_info_resp.json())
            else:
                self.auth_error.emit("Failed to retrieve access token.")

            server.server_close()

        except Exception as e:
            self.auth_error.emit(f"Authentication Error: {str(e)}")