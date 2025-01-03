import joblib
import re
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from bs4 import BeautifulSoup
from nltk.corpus import wordnet

# Tải tài nguyên NLTK cần thiết
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Từ điển các từ viết tắt và dạng đầy đủ
CONTRACTION_MAP = {
    "don't": "do not",
    "can't": "can not",
    "it's": "it is",
    "i'm": "i am",
    "you're": "you are",
    "they're": "they are",
    "we're": "we are",
    "didn't": "did not",
    "hasn't": "has not",
    "haven't": "have not",
    "isn't": "is not",
    "wasn't": "was not",
    "weren't": "were not",
    "won't": "will not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "mightn't": "might not",
    "mustn't": "must not",
    "let's": "let us",
    "that's": "that is",
    "what's": "what is",
    "there's": "there is",
    "here's": "here is"
}

# Danh sách stop words từ NLTK
NLTK_STOP_WORDS = set(stopwords.words('english'))

# Thêm các từ tùy chỉnh
additional_stop_words = ["etc","ect","3d","nbsp", "one", "enron", "com"]
NLTK_STOP_WORDS.update(additional_stop_words)

KEY_PHRASES = {
    # Hành động tài khoản
    "log in to your account", "sign in to your account", "reset your password",
    "update your account settings", "verify your identity", "validate your credentials",
    "unlock your account", "confirm your email address",

    # Hành động khẩn cấp
    "take action immediately", "urgent attention required", "respond within 24 hours",
    "click here to continue", "review your information", "complete the verification process",

    # Thanh toán
    "payment confirmation required", "your payment was declined", "transaction failed",
    "payment is overdue", "pending payment status", "confirm your billing information",
    "please make a payment", "refund is being processed",

    # Bảo mật
    "security alert", "unauthorized login attempt", "suspicious activity detected",
    "your account has been compromised", "secure your account now", "password change required",
    "prevent unauthorized access",

    # Thông thường
    "thank you for your order", "order confirmation", "shipment tracking details",
    "delivery expected by", "contact us for support", "we value your feedback",
    "please let us know", "it team", "it department"

    # Thời gian
    "before the deadline", "within the next 48 hours", "by the end of the day",
    "at your earliest convenience", "no later than tomorrow", "due by next week",

    # Cụm với giới từ
    "access to your account", "update your profile", "information on your account",
    "locked because of suspicious activity", "pending review of your information",
    "verified by our team", "instructions for completing the process",
    "click on the link provided", "follow up with support", "due to an error in your information",
    "complete the process by following the link", "charge on your account",
    "refund for your payment", "payment due for your subscription",
    "billing address on file", "transaction on your credit card", "reply to this email",
    "contact us with any questions", "reach out to support", "help with resolving the issue",
    "assistance with your account", 
}

# Từ điển các từ trong cụm từ quan trọng
# KEY_PHRASE_WORDS = set(word for phrase in KEY_PHRASES for word in phrase.split())

# Stop words cần loại bỏ, trừ các từ trong cụm từ quan trọng
# STOP_WORDS_TO_REMOVE = NLTK_STOP_WORDS - KEY_PHRASE_WORDS

# Hàm mở rộng từ viết tắt
def expand_contractions(text, contraction_map):
    pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in contraction_map.keys()) + r')\b')
    return pattern.sub(lambda x: contraction_map[x.group()], text)


def preprocess_text(text):
    
    # Xử lý email, loại bỏ khoảng trắng không hợp lệ
    text = re.sub(r'([a-zA-Z0-9._%+-]+)\s*\.\s*([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})', r'\1.\2@\3.\4', text)
    
    # Xử lý khoảng trắng giữa ký hiệu đặc biệt và số
    text = re.sub(r'([€£¥$/\%.:])\s*(\d+)', r'\1\2', text)  # Ký hiệu trước số
    text = re.sub(r'(\d+)\s*([€£¥$/\%.:])', r'\1\2', text)  # Ký hiệu sau số

    # Xử lý loại bỏ khoảng trắng trong URL
    text = re.sub(r'(http)\s*:\s*/\s*/\s*([\w.-]+)\s*(/[\w./?=&-]*)?', r'\1://\2\3', text)

    # Chuyển thành chữ thường
    text = text.lower()

    # Loại bỏ HTML tags
    if '<' in text and '>' in text:
        text = BeautifulSoup(text, "html.parser").get_text()

    # Mở rộng từ viết tắt
    text = expand_contractions(text, CONTRACTION_MAP)

    # Loại bỏ các từ chứa dấu gạch dưới (ở đầu, giữa hoặc cuối)
    text = re.sub(r'\b[_a-zA-Z0-9]*_[a-zA-Z0-9_]*\b', '', text)

    # Nối cụm từ quan trọng thành token
    for phrase in KEY_PHRASES:
        phrase_pattern = re.escape(phrase)  # Escape để đảm bảo không lỗi ký tự đặc biệt
        text = re.sub(fr'\b{phrase_pattern}\b', phrase.replace(" ", "_"), text)

    # Thay thế URL và email
    text = re.sub(r"http\S+|www\S+", "URL", text)
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "EMAIL", text)

    # Thay thế DATE
    text = re.sub(r'\b\d{1,4}[-/]\d{1,4}[-/]\d{2,4}\b|\b\d{1,2}\s(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', 'DATE', text)

    # Thay thế giá trị tiền tệ
    text = re.sub(r'\$\d+(?:\.\d+)?|\d+\s?(usd|eur|vnd|gbp|cad|aud)\b', 'MONEY', text, flags=re.IGNORECASE)

    # Thay thế phần trăm
    text = re.sub(r'\b\d+%|\d+\s?(percent|percentage)\b', 'PERCENTAGE', text, flags=re.IGNORECASE)

    # Thay thế TIME bằng <TIME>
    text = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)?\b', 'TIME', text)

    # Loại bỏ số nguyên
    text = re.sub(r'\b\d+\b', ' ', text)

    # Thay thế các chuỗi số dài từ 20 chữ số trở lên bằng <CODE>
    text = re.sub(r'\b\d{20,}\b(?!\w*_)', 'CODE', text)

    # Loại bỏ tất cả ký tự không phải placeholder hoặc chữ, số
    text = re.sub(r'[^a-zA-Z0-9_\s]', ' ', text)

    # Loại bỏ chuỗi có nhiều hơn 2 gạch dưới liên tiếp
    text = re.sub(r'_{2,}', ' ', text)

    # 5. Tokenize văn bản
    tokens = word_tokenize(text)

    # Loại bỏ stop words trong quá trình xử lý
    tokens = [token for token in tokens if token not in NLTK_STOP_WORDS]

    # Loại bỏ từ có 1 chữ cái
    tokens = [token for token in tokens if len(token) > 1]

    # Ghép lại văn bản
    cleaned_text = ' '.join(tokens)

    return cleaned_text.strip()

# To load the model from the file
loaded_svm = joblib.load('c:/Projects/MSE_Final-Project_Email-Phishing-Detection/backend/naive-bayes/phishing_naive_bayes_model.pkl')
vectorizer = joblib.load('c:/Projects/MSE_Final-Project_Email-Phishing-Detection/backend/naive-bayes/phishing_naive_bayes_vectorizer.pkl')


def naive_bayes_predict(email_body):
    processed_email = preprocess_text(email_body)

    # In debug text (nếu muốn kiểm tra)
    print("[DEBUG] Text after preprocessing:")
    print(processed_email)

    X_email = vectorizer.transform([processed_email])


    predicted = loaded_svm.predict(X_email)
    probabilities = loaded_svm.predict_proba(X_email)
    return {
        "phishing": True if predicted[0] == 1 else False,
        "phishing_text": 'Phishing' if predicted[0] == 1 else 'Non-phishing',
        "phishing_probability": probabilities[0][1],
        "non_phishing_probability": probabilities[0][0],
        "processed_email": processed_email
    }

# Hàm liệt kê các từ và trọng số trong email
def list_words_weights_in_email(email_body):
    # Tiền xử lý email
    processed_email = preprocess_text(email_body)

    # Vector hóa nội dung email
    X_email = vectorizer.transform([email_body])

    # Lấy danh sách từ từ vectorizer
    feature_names = vectorizer.get_feature_names_out()

    # Lấy chỉ số các từ xuất hiện trong email
    non_zero_indices = X_email.nonzero()[1]

    # Lấy log xác suất từ mô hình
    log_probabilities = loaded_svm.feature_log_prob_
    probabilities = np.exp(log_probabilities)

    # Danh sách từ và trọng số
    words_weights = []
    for idx in non_zero_indices:
        word = feature_names[idx]
        non_phishing_prob = probabilities[0, idx]
        phishing_prob = probabilities[1, idx]
        words_weights.append((word, non_phishing_prob, phishing_prob))

    return words_weights

if __name__ == "__main__":
    # Nội dung email cần kiểm tra
    test_email = """
    Dear User, 
    Your account has been compromised. Please click on the link below to reset your password immediately:
    http://phishing-website.com/reset-password
    Thank you, IT Support
    """

     # Tiền xử lý và hiển thị nội dung đã xử lý
    processed_email = preprocess_text(test_email)
    print("\nNội dung sau khi tiền xử lý:")
    print(processed_email)

    # Gọi hàm dự đoán
    result = naive_bayes_predict(test_email)
    
    # In kết quả dự đoán
    print("Dự đoán kết quả:")
    print(f"Phishing: {result['phishing']}")
    print(f"Phishing Text: {result['phishing_text']}")
    print(f"Phishing Probability: {result['phishing_probability']:.2f}")
    print(f"Non-Phishing Probability: {result['non_phishing_probability']:.2f}")

    # Gọi hàm liệt kê từ và trọng số
    words_weights = list_words_weights_in_email(test_email)

    # In danh sách từ và trọng số
    print("\nDanh sách từ và trọng số trong email:")
    for word, non_phishing_prob, phishing_prob in words_weights:
        print(f"Word: {word}, Non-phishing Prob: {non_phishing_prob:.4f}, Phishing Prob: {phishing_prob:.4f}")