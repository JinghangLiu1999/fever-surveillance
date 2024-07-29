pip install -r requirements.txt
python aws_sns.py

For test
curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d "{\"temperature\": 38.5, \"fever_probability\": 0.8, \"rgb_image_id\": 1, \"thermal_image_id\": 2}"
