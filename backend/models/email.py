from app import db

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
