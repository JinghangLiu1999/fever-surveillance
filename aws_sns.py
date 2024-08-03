from flask import Flask, request, jsonify 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import event 
from datetime import datetime 
import boto3 
from flask_cors import CORS 
import logging 
from multiprocessing import Process, Queue 
from camera import MergeCamera 
import threading 
import time 

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__) 
PORT = 5000 
DATABASE = "sqlite:///Fever-Surveillance.db" 

# AWS SNS configuration 
topic_arn = 'arn:aws:sns:ap-southeast-2:975049897672:Fever-Surveillance' 
session = boto3.Session( 
    aws_access_key_id='AKIA6GBMAW3EBBMO3YHZ', 
    aws_secret_access_key='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', 
) 
sns_client = session.client('sns', region_name='ap-southeast-2') 

app = Flask(__name__) 
CORS(app) 
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app) 
video_feed = MergeCamera() 
queue = Queue() 
# User model definition 

class User(db.Model): 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    temperature = db.Column(db.Float, nullable=False) 
    image_data = db.Column(db.Text, nullable=False) 
    date_created = db.Column(db.DateTime, default=datetime.now) 
    file_name = db.Column(db.String(255), nullable=False) 
    def __repr__(self): 
        return f'<User {self.id}>' 

# Event listener for new User entries 
@event.listens_for(User, 'after_insert') 
def after_insert_listener(mapper, connection, target): 
    message = ( 
        f'New data added: ID={target.id}, Temperature={target.temperature}, ' 
        f'Date Created={target.date_created}' 
    ) 
    logger.info(message) 
    response = sns_client.publish( 
        TopicArn=topic_arn, 
        Message=message, 
        Subject="Fever-Surveillance" 
    ) 

    logger.info(f'SNS publish response: {response}') 

# Flask routes 
@app.route("/", methods=["GET"]) 
def home(): 
    return "Welcome" 

@app.route("/api/users", methods=['POST']) 
def add_user(): 
    data = request.get_json() 
    new_user = User( 
        temperature=data.get('temperature'), 
        image_data=data.get('image_data'), 
        file_name=data.get('file_name') 
    ) 
    db.session.add(new_user) 
    db.session.commit() 
    return jsonify({"message": "User added"}), 201 

@app.route("/api/users", methods=['GET']) 
def get_users(): 
    users = User.query.all() 
    users_list = [{'id': user.id, 'temperature': user.temperature,'image_data': user.image_data, 'date_created': user.date_created,'file_name': user.file_name} for user in users] 
    return jsonify(users_list) 

  
def create_app(): 
    with app.app_context(): 
        logger.info("Creating database tables...") 
        db.create_all() 
        logger.info("Database tables created.") 
    return app 

  
def run_flask_app(): 
    app = create_app() 
    app.run(port=5000, debug=False)   

if __name__ == "__main__": 
    # Run Flask app in a separate thread 
    flask_thread = threading.Thread(target=run_flask_app) 
    camera_thread = threading.Thread(target=video_feed.run, args=(queue,)) 
    flask_thread.start() 
    camera_thread.start() 

 
