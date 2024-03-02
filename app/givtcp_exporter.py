from prometheus_client import start_http_server, Gauge, Counter
import requests
import yaml
import os
import http.server
import socketserver
from datetime import datetime

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            # Perform work when triggered
            # For example, incrementing the work_metric
            fetch_data(api_url, metric_prefix, metrics)
            response = requests.get('http://localhost:'+str(http_port + 1))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.content)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'bye')

def load_config():
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            return config
    except FileNotFoundError:
        print("Config file not found. Trying environment variables.")
        return {}

def convert_to_unix_timestamp(value):
    try:
        if not isinstance(value, str):
            value = str(value)

        dt_object = datetime.fromisoformat(value)
        return int(dt_object.timestamp())
    except (ValueError, TypeError):
        return None

def create_metrics(prefix, json_data, metric_dict):
    for key, value in json_data.items():
        metric_name = f"{prefix}_{key}"

        if isinstance(value, dict):
            create_metrics(metric_name, value, metric_dict)
        else:
            if isinstance(value, (int, float)):
                if metric_name not in metric_dict:
                    metric_dict[metric_name] = Gauge(metric_name, f'Gauge metric for {key}')
                metric_dict[metric_name].set(value)
            else:
                timestamp_value = convert_to_unix_timestamp(value)
                if timestamp_value is not None:
                    if metric_name not in metric_dict:
                        metric_dict[metric_name] = Gauge(metric_name, f'Unix timestamp metric for {key}')
                    metric_dict[metric_name].set(timestamp_value)
                else:
                    # Check if the gauge metric already has labels
                    if metric_name not in metric_dict or not metric_dict[metric_name]._labelnames:
                        metric_dict[metric_name] = Gauge(metric_name, f'Gauge metric for {key}', [key])
                    metric_dict[metric_name].labels(str(value)).set(1)

def fetch_data(api_url, metric_prefix, metrics):
    try:
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        create_metrics(metric_prefix, data, metrics)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

if __name__ == '__main__':
    config = load_config()

    http_port = int(os.environ.get('HTTP_PORT', config.get('http_port', 9132)))
    api_url = os.environ.get('API_URL', config.get('api_url', 'https://example.com/api/data'))
    metric_prefix = os.environ.get('METRIC_PREFIX', config.get('metric_prefix', 'example'))

    print(f"Using port: {http_port}\nUsing url: {api_url}\nUsing prefix: {metric_prefix}\n")
    start_http_server(http_port + 1)
    metrics = {}
    # Create a custom server using the RequestHandler
    with socketserver.TCPServer(('0.0.0.0', http_port), RequestHandler) as httpd:
        print(f"Prometheus exporter is running on port {http_port}")
        httpd.serve_forever()
