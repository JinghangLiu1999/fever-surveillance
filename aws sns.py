from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from datetime import datetime
import boto3


PORT = 5000
DATABASE = "sqlite:///Fever-Surveillance.db"  

# AWS SNS configuration
topic_arn = 'arn:aws:sns:ap-southeast-2:975049897672:Fever-Surveillance'  
session = boto3.Session(
    aws_access_key_id='AKIA6GBMAW3EBBMO3YHZ',
    aws_secret_access_key='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',
)
sns_client = session.client('sns', region_name='ap-southeast-2', )


app = Flask("Intellinodes")
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


# Event listener for after insert and send emai
@event.listens_for(User, 'after_insert')
def after_insert_listener(mapper, connection, target):
    message = (
        f'New data added: ID={target.id}, Temperature={target.temperature}, '
        f'Fever Probability={target.fever_probability}, RGB Image ID={target.rgb_image_id}, '
        f'Thermal Image ID={target.thermal_image_id}, Date Created={target.date_created}'
    )
    print(message)
    
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject="Fever-Surveillance"
    )
    print(f'SNS publish response: {response}')


@app.route("/")
def home():
    return "Welcome to the Fever-Surveillance!"

@app.route("/api/search")
def search():
    from_date = request.values.get("fromDate", None)
    to_date = request.values.get("toDate", None)
    sort = request.values.get("sort")
    return jsonify({"fromDate": from_date, "toDate": to_date, "sort": sort})

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
    db.sess1ion.add(new_user)
    db.session.commit()
    return jsonify({"message": "User added"}), 201

@app.route("/api/users", methods=['GET'])
def get_users():
    users = User.query.all()
    users_list = [{'id': user.id, 'temperature': user.temperature, 'fever_probability': user.fever_probability, 'rgb_image_id': user.rgb_image_id, 'thermal_image_id': user.thermal_image_id, 'date_created': user.date_created} for user in users]
    return jsonify(users_list)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
    app.run(port=PORT, debug=True)