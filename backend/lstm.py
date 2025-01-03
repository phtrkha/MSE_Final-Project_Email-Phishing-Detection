import os
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import string
import nltk
nltk.download('punkt')
nltk.download('stopwords')
# Improved preprocessing function
def preprocess_email(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Tokenize the text
    text = word_tokenize(text)
    # Define stop-words in English
    ENGLISH_STOP_WORDS = set(stopwords.words('english'))
    # Remove stop words
    text = [word for word in text if word not in ENGLISH_STOP_WORDS]
    # Rejoin words for further processing
    text = ' '.join(text)
    # Remove hyperlinks
    text = re.sub(r"http\S+", "", text)
    return text
# Load the model
model = load_model('c:/Projects/MSE_Final-Project_Email-Phishing-Detection/backend/lstm/LSTM_model.h5')
# Load the tokenizer
with open('c:/Projects/MSE_Final-Project_Email-Phishing-Detection/backend/lstm/LSTM_tokenizer.pkl', 'rb') as handle:
    tokenizer = pickle.load(handle)
# Function to predict if an email is phishing or not
def lstm_predict_email(text):
    preprocessed_text = preprocess_email(text)
    sequence = tokenizer.texts_to_sequences([preprocessed_text])
    padded_sequence = pad_sequences(sequence, maxlen=100)
    prediction = model.predict(padded_sequence)
    # return 'Phishing Email' if prediction > 0.5 else 'Safe Email'
    return prediction[0][0]

# Example phishing email content for testing
# sample_phishing_email = """
# Dear Customer,

# We have detected some suspicious activity in your account. As a precaution, we have temporarily locked your account to protect your personal information.

# To restore access to your account, please click the link below and follow the instructions to verify your identity:
# [Click here to verify your account](http://example.com/verify)

# Failure to verify your account within 24 hours may result in permanent suspension of your account.

# Thank you for your prompt attention to this matter.

# Sincerely,
# Your Bank's Security Team
# """

# Make prediction on the sample phishing email
# print("Prediction:", lstm_predict_email(sample_phishing_email))
