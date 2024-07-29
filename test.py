import requests
import random


url = 'http://localhost:5000/api/users'


def generate_test_data():
    return {
        'temperature': round(random.uniform(36.0, 40.0), 1),
        'fever_probability': round(random.uniform(0.0, 1.0), 2),
        'rgb_image_id': random.randint(1, 100),
        'thermal_image_id': random.randint(1, 100)
    }


num_entries = 3

# Populate test data
for _ in range(num_entries):
    data = generate_test_data()
    response = requests.post(url, json=data)
    if response.status_code == 201:
        print(f'Successfully added: {data}')
    else:
        print(f'Failed to add: {data} with response {response.status_code}')

print('Test data population complete.')
