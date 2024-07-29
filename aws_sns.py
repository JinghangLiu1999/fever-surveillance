from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from datetime import datetime
import boto3
from flask_cors import CORS  # Import CORS
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = 5000
DATABASE = "sqlite:///Fever-Surveillance.db"  # Ensure the correct database file name

# AWS SNS configuration
topic_arn = 'arn:aws:sns:ap-southeast-2:975049897672:Fever-Surveillance'
session = boto3.Session(
    aws_access_key_id='your_access_key_id',
    aws_secret_access_key='your_secret_access_key',
)
sns_client = session.client('sns', region_name='ap-southeast-2',)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for the app
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    temperature = db.Column(db.Float, nullable=False)
    fever_probability = db.Column(db.Float, nullable=False)
    rgb_image_id = db.Column(db.Integer, nullable=False)
    thermal_image_id = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.Date, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.id}>'

@event.listens_for(User, 'after_insert')
def after_insert_listener(mapper, connection, target):
    message = (
        f'New data added: ID={target.id}, Temperature={target.temperature}, '
        f'Fever Probability={target.fever_probability}, RGB Image ID={target.rgb_image_id}, '
        f'Thermal Image ID={target.thermal_image_id}, Date Created={target.date_created}'
    )
    logger.info(message)

    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject="Fever-Surveillance"
    )
    logger.info(f'SNS publish response: {response}')

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Fever Surveillance API!"

@app.route("/api/users", methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(
        temperature=data.get('temperature'),
        fever_probability=data.get('fever_probability'),
        rgb_image_id=data.get('rgb_image_id'),
        thermal_image_id=data.get('thermal_image_id'),
        date_created=datetime.utcnow()
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User added"}), 201

@app.route("/api/users", methods=['GET'])
def get_users():
    users = User.query.all()
    users_list = [{'id': user.id, 'temperature': user.temperature, 'fever_probability': user.fever_probability, 'rgb_image_id': user.rgb_image_id, 'thermal_image_id': user.thermal_image_id, 'date_created': user.date_created} for user in users]
    return jsonify(users_list)

if __name__ == "__main__":
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()  # Create database tables if they don't exist
        logger.info("Database tables created.")
    app.run(port=PORT, debug=True)
