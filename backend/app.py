from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Cấu hình kết nối đến MySQL từ biến môi trường
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql+mysqlconnector://root:Abc123456@mysql/email_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graph_id = db.Column(db.String(255), unique=True)
    action = db.Column(db.String(50))
    classify_by_ai = db.Column(db.String(50))
    model_predicted = db.Column(db.String(50))
    received_date_time = db.Column(db.DateTime)
    re_classify_by = db.Column(db.String(255))
    re_classify = db.Column(db.String(50))
    from_email = db.Column(db.String(255))
    to_email = db.Column(db.String(255))
    subject = db.Column(db.Text)
    body_preview = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/api/test', methods=['GET'])
def test_connection():
    return jsonify({"message": "Connection successful!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
