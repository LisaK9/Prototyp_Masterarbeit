from flask import Flask, request, Response, session
import random
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
import uuid
# Importiere beide Apps
from app import create_app as create_prototyp_app
from app_neutral import create_app as create_prototyp_neutral_app

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Erstelle die beiden Apps
app1 = create_prototyp_app()
app2 = create_prototyp_neutral_app()

# Dictionary zur Speicherung der Nutzer-zu-App-Zuordnung
user_app_mapping = {}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    # Überprüfe, ob der Nutzer bereits eine ID hat
    user_id = request.cookies.get('user_id')
    if not user_id:
        # Generiere eine neue Nutzer-ID
        user_id = str(uuid.uuid4())
        # Weise den Nutzer zufällig einer App zu
        user_app_mapping[user_id] = random.choice(['app1', 'app2'])
        print(f"New user: {user_id} assigned to {user_app_mapping[user_id]}")

    # Lade die zugewiesene App
    selected_app = app1 if user_app_mapping.get(user_id) == 'app1' else app2
    print(f"Selected App: {selected_app}")
    print(f"Request Path: {path}")

    # Wenn die Anfrage eine statische Datei betrifft, leite sie direkt an die ausgewählte App weiter
    if path.startswith('static/'):
        print(f"Handling static file: {path}")
        with selected_app.test_request_context(path=path, method=request.method, headers=dict(request.headers)):
            response = selected_app.full_dispatch_request()
        return Response(
            response=response.get_data(),
            status=response.status_code,
            headers=dict(response.headers),
        )

    # Kopiere die Header in ein veränderliches Dictionary
    headers = dict(request.headers)

    # Erstelle eine neue Umgebung für die ausgewählte App
    environ = create_environ(
        path=request.path,
        method=request.method,
        headers=headers,  # Verwende das veränderliche Dictionary
        data=request.get_data(),
        query_string=request.query_string,
        content_type=request.content_type,
    )

    # Erstelle ein Request-Objekt für die ausgewählte App
    with selected_app.request_context(environ):
        # Verarbeite die Anfrage mit der ausgewählten App
        response = selected_app.full_dispatch_request()

    # Erstelle eine Response und setze das Cookie
    flask_response = Response(
        response=response.get_data(),
        status=response.status_code,
        headers=dict(response.headers),
    )
    if not request.cookies.get('user_id'):
        flask_response.set_cookie('user_id', user_id)
    return flask_response
if __name__ == "__main__":
    app.run(debug=True)
