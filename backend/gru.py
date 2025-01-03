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
nltk.download('punkt_tab')
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
model = load_model('c:/Projects/MSE_Final-Project_Email-Phishing-Detection/backend/gru/GRU_model.h5')
# Load the tokenizer
with open('c:/Projects/MSE_Final-Project_Email-Phishing-Detection/backend/gru/GRU_tokenizer.pkl', 'rb') as handle:
    tokenizer = pickle.load(handle)
# Function to predict if an email is phishing or not
def gru_predict_email(text):
    preprocessed_text = preprocess_email(text)
    sequence = tokenizer.texts_to_sequences([preprocessed_text])
    padded_sequence = pad_sequences(sequence, maxlen=100)
    prediction = model.predict(padded_sequence)
    # return 'Phishing Email' if prediction > 0.5 else 'Safe Email'
    return prediction[0][0]

# # Example phishing email content for testing
# sample_phishing_email = """
# equistar deal tickets still available assist robert entering new deal tickets equistar talking bryan hull anita luong kyle decided need 1 additional sale ticket 1 additional buyback ticket set forwarded tina valadez hou ect 04 06 2000 12 56 pm robert e lloyd 04 06 2000 12 40 pm tina valadez hou ect ect cc subject equistar deal tickets may want run idea daren farmer normally add tickets sitara tina valadez 04 04 2000 10 42 robert e lloyd hou ect ect cc bryan hull hou ect ect subject equistar deal tickets kyle met bryan hull morning decided need 1 new sale ticket 1 new buyback ticket set time period tickets july 1999 forward pricing new sale ticket like tier 2 sitara 156337 pricing new buyback ticket like tier 2 sitara 156342 questions please let know thanks tina valadez 3 7548
# """

# # Make prediction on the sample phishing email
# print("Prediction:", gru_predict_email(sample_phishing_email))
