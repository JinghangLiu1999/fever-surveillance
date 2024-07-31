from aws_sns import create_app
import requests
import random
import threading
import time

url = 'http://localhost:5000/api/users'

def generate_test_data():
    return {
        'temperature': round(random.uniform(36.0, 40.0), 1),
        'fever_probability': round(random.uniform(0.0, 1.0), 2),
        'rgb_image_id': random.randint(1, 100),
        'thermal_image_id': random.randint(1, 100)
    }

def populate_test_data(num_entries=1):
    for _ in range(num_entries):
        data = generate_test_data()
        response = requests.post(url, json=data)
        if response.status_code == 201:
            print(f'Successfully added: {data}')
        else:
            print(f'Failed to add: {data} with response {response.status_code}')
    print('Test data population complete.')

def run_flask_app():
    app = create_app()
    app.run(port=5000, debug=False)  

if __name__ == "__main__":
    # Run Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    time.sleep(5)
    populate_test_data(1)
