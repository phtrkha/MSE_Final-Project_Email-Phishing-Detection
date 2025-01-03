from flask import Flask, request, jsonify
import json
import msal
# import time
import requests
from datetime import datetime, timedelta
from threading import Thread
from flask_cors import CORS
from config import Config
from gpt import gpt_classify_and_detect_phishing

# from email_logs_manager import EmailLogsManager
from email_logs_manager_v2 import EmailLogsManagerV2

from utils import clean_html
from lstm import lstm_predict_email
from naive_bayes import naive_bayes_predict
from gru import gru_predict_email


app = Flask(__name__)
# Allow all origins and specify other options
cors = CORS(app, resources={r"/*": {"origins": "*"}})

email_logs_manager_v2 = EmailLogsManagerV2(
        hostname='127.0.0.1',
        username='root',
        password='Abc@123456',
        database='appseed_db'
    )

@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' http://localhost:* http://127.0.0.1:*; "
        "script-src 'self' http://localhost:* http://127.0.0.1:* 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' http://localhost:* http://127.0.0.1:* 'unsafe-inline'; "
        "img-src 'self' http://localhost:* http://127.0.0.1:* data:; "
        "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
        "font-src 'self' http://localhost:* http://127.0.0.1:* data:; "
        "object-src 'none'; "
        "frame-ancestors 'self'; "
        "base-uri 'self';"
    )
    return response

# email_logs_manager = EmailLogsManager(
#         hostname='209.182.237.165',
#         username='user01',
#         password='mauFJcuf5dhRMQrjj1',
#         database='appseed_db'
#     )
# email_logs_manager.connect_to_mysql()

# Replace with your values
CLIENT_ID = 'dd2478d5-e723-4f0d-b8da-0e56e51b01bc'
CLIENT_SECRET = 'C6v8Q~f1eATY3Z-~xDgfyFsf0rMlpViYCMAGdbJk'
TENANT_ID = '40e92544-670c-4419-a374-fa36c7150276'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ['https://graph.microsoft.com/.default']
# notification_url = 'https://d2fc-118-69-183-236.ngrok-free.app/webhook'
notification_url = 'https://d81a-2405-4803-b174-b4d0-9496-7d9-1dd0-adcc.ngrok-free.app'

# Initialize the MSAL confidential client application
mail_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

def get_access_token():
    result = mail_app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire token: {result.get('error')}, {result.get('error_description')}")

# Function to delete all subscriptions
def delete_all_subscriptions(access_token):
    url = "https://graph.microsoft.com/v1.0/subscriptions"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Get list of subscriptions
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        subscriptions = response.json().get('value', [])
        for subscription in subscriptions:
            # print("=-=-=-=-=-subscription", subscription)
            subscription_id = subscription.get('id')
            delete_url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code == 204:
                print(f"Subscription {subscription_id} deleted successfully.")
            else:
                print(f"Failed to delete subscription {subscription_id}. Status code: {delete_response.status_code}, Error: {delete_response.text}")
    else:
        print(f"Failed to retrieve subscriptions. Status code: {response.status_code}, Error: {response.text}")


def label_email(message_id, user_id, label):
    token = get_access_token()
    update_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    update_data = {
        "categories": [label]
    }
    response = requests.patch(update_url, headers=headers, data=json.dumps(update_data))
    return response.json()


def update_email_content(user_id, email_id, phishing_info):
    access_token = get_access_token()
    url = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages/{email_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "body": {
            "contentType": "HTML",
            "content": phishing_info
        }
    }
    response = requests.patch(url, headers=headers, json=data)
    return response

def get_email_details(user_id, message_id):
    token = get_access_token()
    get_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(get_url, headers=headers)
    return response.json()

@app.route('/webhook', methods=['POST'])
def webhook():
    validation_token = request.args.get('validationToken')
    if validation_token:
    # Trả lại validationToken trong response
        return validation_token, 200
    
    # return jsonify({"message": "Notification received duplicate"}), 200

    if request.is_json:
        data = request.json
        # Xử lý dữ liệu nhận được
        # print(data)
        for notification in data.get('value', []):
            change_type = notification['changeType']
            # Xử lý thông báo tương ứng với change_type
            message_id = notification['resourceData']['id']
            if message_id is None:
                # continue
                return jsonify({"message": "Notification not found"}), 200

            user_id = notification['resource'].split('/')[1]
            email_details = get_email_details(user_id, message_id)
            # print(email_details)  # Bạn có thể sử dụng thông tin này để xác định nhãn
            if change_type == 'created':
                print(f"Email {message_id} created for user {user_id}")
                # Xử lý khi có email mới
                
                # email_logs_manager = EmailLogsManager(
                #     hostname='209.182.237.165',
                #     username='user01',
                #     password='mauFJcuf5dhRMQrjj1',
                #     database='appseed_db'
                # )
                # email_logs_manager.connect_to_mysql()
                emailExist = email_logs_manager_v2.get_email_by_mail_id(message_id)
                # print("emailExist=-=-=-=", emailExist)
                if emailExist:
                    # email_logs_manager.close_connection()
                    return jsonify({"message": "Notification received duplicate"}), 200

                # label = 'Phishing'
                label = 'Legit'
                subject = email_details.get('subject', '')
                sender_email_address = email_details.get('sender', {}).get('emailAddress', {}).get('address', '')
                body_content = clean_html(email_details.get('body', {}).get('content', ''))
                phishingDetect = None
                prediction_score = 0
                currentModel = Config.get_current_model()
                if currentModel == 'GPT-3.5-TURBO':
                    phishingDetect = gpt_classify_and_detect_phishing('gpt-3.5-turbo', sender_email_address, subject, body_content)
                    prediction_score = phishingDetect['confidence']
                    if phishingDetect['phishing']:
                        label = 'Phishing'
                        
                elif currentModel == 'GPT-4':
                    phishingDetect = gpt_classify_and_detect_phishing('gpt-4', sender_email_address, subject, body_content)
                    prediction_score = phishingDetect['confidence']
                    if phishingDetect['phishing']:
                        label = 'Phishing'
                        
                elif currentModel == 'LSTM':
                    phishingDetect = lstm_predict_email(body_content)
                    prediction_score = (0.5 - phishingDetect) / 0.5
                    
                    if phishingDetect > 0.5: 
                        label = 'Phishing'
                        prediction_score = phishingDetect

                elif currentModel == 'GRU':
                    phishingDetect = gru_predict_email(body_content)
                    prediction_score = (0.5 - phishingDetect) / 0.5
                    
                    if phishingDetect > 0.5: 
                        label = 'Phishing'
                        prediction_score = phishingDetect

                        
                elif currentModel == 'NAIVE-BAYES':
                    phishingDetect = naive_bayes_predict(body_content)
                    prediction_score = phishingDetect['phishing_probability']
                    if phishingDetect['phishing']:
                        label = 'Phishing'
                        
                        
                email_logs_manager_v2.insert_email_log(email_details, label, Config.get_current_model(), user_id)
                # email_logs_manager.close_connection()
                # # Xác định nhãn cho email, ví dụ: 'Phishing'
                
                result = label_email(message_id, user_id, label)
                # Cập nhật nội dung email với thông tin dự đoán
                phishing_info = f"""
                <div style="border: 1px solid #ddd; padding: 20px; font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2 style="color: #d9534f;">Email Classification Result</h2>
                    <p><strong>Prediction:</strong> <span style="color: {'#d9534f' if label == 'Phishing' else '#5cb85c'};">{label}</span></p>
                    <p><strong>Confidence:</strong> {prediction_score * 100:.1f}%</p>
                    <p><strong>Model:</strong> {currentModel}</p>
                    <h3>Processed Message:</h3>
                    <p>{phishingDetect['processed_email']}</p> 
                    <hr style="border-top: 1px solid #ddd;">
                    <h3>Original Message:</h3>
                    <p>{email_details.get('body', {}).get('content', '')}</p>
                </div>
                """
                update_response = update_email_content(user_id, message_id, phishing_info)
                print("update_response", update_response)

                # print('=================00000', result)
            elif change_type == 'updated':
                print(f"Email {message_id} updated for user {user_id}")

                # return jsonify({"message": "Notification received duplicate"}), 200

                # Xử lý khi có email được cập nhật
                # Kiểm tra nhãn của email
                # email_logs_manager = EmailLogsManager(
                #     hostname='209.182.237.165',
                #     username='user01',
                #     password='mauFJcuf5dhRMQrjj1',
                #     database='appseed_db'
                # )
                # print(f"Email {message_id} được gán nhãn là Phishing")
                # email_logs_manager.connect_to_mysql()
                emailExist = email_logs_manager_v2.get_email_by_mail_id(message_id)
                if emailExist:
                    if emailExist.get('classifyByManual') != 'ADMIN':
                        email_logs_manager_v2.update_email_log(message_id, email_details, emailExist, emailExist.get('classifyBy'), emailExist.get('classification'),)
                # else:
                #     email_logs_manager.insert_email_log(email_details)
                # email_logs_manager.close_connection()
                # Xử lý email bị gán nhãn Phishing tại đây
            
    return jsonify({"message": "Notification received"}), 200

def get_all_users():
    token = get_access_token()
    users_url = 'https://graph.microsoft.com/v1.0/users'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(users_url, headers=headers)
    users = response.json().get('value', [])
    return users

def calculate_expiration_date(days=7):
    expiration_date = datetime.utcnow() + timedelta(days=days)
    return expiration_date.isoformat() + 'Z'  # ISO 8601 format with Z to indicate UTC time

def register_mail_webhook_for_user(user_id, changeType, days=7):
    token = get_access_token()
    # print(token)
    subscription_url = 'https://graph.microsoft.com/v1.0/subscriptions'
    expiration_date = calculate_expiration_date(days)
    subscription_data = {
        "changeType": changeType,
        "notificationUrl": notification_url,
        "resource": f"/users/{user_id}/mailFolders('Inbox')/messages",
        "expirationDateTime": expiration_date
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(subscription_url, headers=headers, data=json.dumps(subscription_data))
    return response.json()

def register_webhooks_for_all_users(days=7):
    users = get_all_users()
    for user in users:
        user_id = user['id']
        result = register_mail_webhook_for_user(user_id, 'created', days)
        print("register_mail_created_webhook_for_user", result)
        result = register_mail_webhook_for_user(user_id, 'updated', days)
        print("register_mail_updated_webhook_for_user", result)


def run_register_webhooks_for_all_users():
    days = 3  # Số ngày bạn muốn thêm
    token = get_access_token()
    # print(token)
    delete_all_subscriptions(token)
    register_webhooks_for_all_users(days)


@app.route('/api/email/<mail_id>', methods=['GET'])
def get_email_by_mail_id(mail_id):
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    # email_logs_manager.connect_to_mysql()
    email = email_logs_manager_v2.get_email_by_mail_id(mail_id)
    # email_logs_manager.close_connection()

    if email:
        # # print(email)  # In thông tin chi tiết email hoặc xử lý tiếp theo nếu cần
        return email, 200
    else:
        return jsonify({"message": f"Không tìm thấy email có mailId {mail_id}"}), 404

@app.route('/api/emails/ordered-by-received-datetime', methods=['GET'])
def get_emails_ordered_by_received_datetime():
    top = request.args.get('top')
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    # email_logs_manager.connect_to_mysql()
    emails = email_logs_manager_v2.get_emails_ordered_by_received_datetime(top)
    # email_logs_manager.close_connection()
    if emails:
        return json.dumps({"emails":emails}, default=str), 200
    else:
        return jsonify({"message": "Không có email nào trong bảng email_logs."}), 404

@app.route('/api/emails/count', methods=['GET'])
def count_total_emails():
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    # email_logs_manager.connect_to_mysql()
    total_emails = email_logs_manager_v2.count_total_emails()
    # print("total_emails", total_emails)
    total_phishing_emails = email_logs_manager_v2.count_total_phishing_emails()
    total_unlabeling_emails_by_user = email_logs_manager_v2.count_total_unlabeling_emails_by_user()
    total_emails_report_by_user = email_logs_manager_v2.count_total_phishing_emails_by_user()
    # email_logs_manager.close_connection()
    return jsonify({"total_emails": total_emails, "total_phishing_emails": total_phishing_emails, "total_unlabeling_emails_by_user": total_unlabeling_emails_by_user, "total_emails_report_by_user": total_emails_report_by_user}), 200

@app.route('/api/model/current', methods=['GET'])
def get_current_model():
    current_model = Config.get_current_model()
    return jsonify({"current_model": current_model}), 200

@app.route('/api/model/setup', methods=['POST'])
def set_current_model():
    data = request.json
    model_name = data.get("model_name")
    
    if model_name and Config.set_current_model(model_name):
        return jsonify({"message": f"Model hiện tại được thiết lập thành {model_name}"}), 200
    else:
        return jsonify({"message": "Giá trị model không hợp lệ. Vui lòng chọn 'LSTM', 'GPT-3.5-TURBO' hoặc 'GPT-4'."}), 400

@app.route('/api/emails/total-by-date', methods=['GET'])
def get_total_emails_by_date():
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    # email_logs_manager.connect_to_mysql()
    total_emails_by_date = email_logs_manager_v2.get_total_emails_by_date()
    total_phishing_emails_by_date = email_logs_manager_v2.get_phishing_emails_by_date()
    # email_logs_manager.close_connection()
    # return jsonify(total_emails_by_date), 200
    return json.dumps({"total_emails_by_date":total_emails_by_date, "total_phishing_emails_by_date": total_phishing_emails_by_date}, default=str), 200

@app.route('/api/emails/phishing-by-date', methods=['GET'])
def get_phishing_email_opens_by_date():
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    # email_logs_manager.connect_to_mysql()
    total_phishing_email_opens_by_date = email_logs_manager_v2.get_phishing_email_opens_by_date()
    total_reported_emails_by_date = email_logs_manager_v2.get_reported_emails_by_date()
    # email_logs_manager.close_connection()
    return json.dumps({"total_phishing_email_opens_by_date":total_phishing_email_opens_by_date, "total_reported_emails_by_date": total_reported_emails_by_date}, default=str), 200

@app.route('/api/emails/count-by-model', methods=['GET'])
def get_email_count_by_model():
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    # email_logs_manager.connect_to_mysql()
    email_count_by_model = email_logs_manager_v2.get_email_count_by_model()
    # email_logs_manager.close_connection()
    return jsonify(email_count_by_model), 200

@app.route('/api/emails/top-users-with-phishing', methods=['GET'])
def get_top_users_with_phishing_emails():
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )
    top_n = request.args.get('top_n', default=5, type=int)
    # email_logs_manager.connect_to_mysql()
    top_users = email_logs_manager_v2.get_top_users_with_phishing_emails(top_n)
    # email_logs_manager.close_connection()
    return jsonify(top_users), 200


@app.route('/api/classify_email', methods=['POST'])
def classify_email():
    classification = request.json['classification']  # Loại phân loại mà người dùng chọn
    email_id = request.json['email_id']  
    classify_by_user = request.json['classify_by_user']
    # email_logs_manager = EmailLogsManager(
    #     hostname='209.182.237.165',
    #     username='user01',
    #     password='mauFJcuf5dhRMQrjj1',
    #     database='appseed_db'
    # )  
    # email_logs_manager.connect_to_mysql()
    emailExist = email_logs_manager_v2.get_email_by_mail_id(email_id)
    # email_logs_manager.close_connection()

    if emailExist:
        # email_logs_manager = EmailLogsManager(
        #     hostname='209.182.237.165',
        #     username='user01',
        #     password='mauFJcuf5dhRMQrjj1',
        #     database='appseed_db'
        # )  
        # email_logs_manager.connect_to_mysql()
        email_logs_manager_v2.clasify_email(email_id, 'ADMIN', classify_by_user, classification)
        # email_logs_manager.close_connection()
        label_email(email_id, emailExist.get('userId'), classification)
        return jsonify({'message': 'Email classification updated successfully'}), 200
    else:
        # email_logs_manager.close_connection()
        return jsonify({'message': 'Email not found'}), 404


if __name__ == '__main__':
    # app.run(port=5000)
    Thread(target=run_register_webhooks_for_all_users).start()
    app.run(debug=True, host='0.0.0.0', port=5002)

