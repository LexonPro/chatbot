import json
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem import WordNetLemmatizer
import os

# Download required NLTK data (silently)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

lemmatizer = WordNetLemmatizer()

class ChatbotModel:
    def __init__(self, intents_file="intents.json"):
        self.intents_file = intents_file
        self.vectorizer = TfidfVectorizer()
        self.corpus = []
        self.tags = []
        self.intents_data = []
        self.is_trained = False
        
        self.load_data()
        self.train_model()

    def preprocess_text(self, text):
        # Tokenize and lemmatize
        tokens = nltk.word_tokenize(text.lower())
        lemmatized_tokens = [lemmatizer.lemmatize(word) for word in tokens]
        return " ".join(lemmatized_tokens)

    def load_data(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, self.intents_file)
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.intents_data = data["intents"]
            
            for intent in self.intents_data:
                for pattern in intent["patterns"]:
                    preprocessed_pattern = self.preprocess_text(pattern)
                    self.corpus.append(preprocessed_pattern)
                    self.tags.append(intent["tag"])

    def train_model(self):
        if not self.corpus:
            print("No training data found.")
            return
            
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)
        self.is_trained = True
        print("Chatbot model trained successfully.")

    def preprocess_user_input(self, text):
        import difflib
        tokens = nltk.word_tokenize(text.lower())
        lemmatized_tokens = [lemmatizer.lemmatize(word) for word in tokens]
        
        if self.is_trained:
            try:
                vocab = self.vectorizer.get_feature_names_out()
                corrected_tokens = []
                for word in lemmatized_tokens:
                    if word not in vocab and word.isalnum():
                        matches = difflib.get_close_matches(word, vocab, n=1, cutoff=0.6)
                        if matches:
                            corrected_tokens.append(matches[0])
                        else:
                            corrected_tokens.append(word)
                    else:
                        corrected_tokens.append(word)
                return " ".join(corrected_tokens)
            except Exception:
                pass
                
        return " ".join(lemmatized_tokens)

    def get_response(self, user_input):
        if not self.is_trained:
            return "Sorry, my brain isn't fully loaded yet."

        preprocessed_input = self.preprocess_user_input(user_input)
        input_vector = self.vectorizer.transform([preprocessed_input])
        
        # Calculate cosine similarity between user input and all patterns
        similarities = cosine_similarity(input_vector, self.tfidf_matrix)
        
        # Find the most similar pattern
        max_sim_idx = np.argmax(similarities)
        max_sim_score = similarities[0][max_sim_idx]
        
        # Threshold for understanding
        if max_sim_score > 0.3:
            matched_tag = self.tags[max_sim_idx]
            # Find responses for the matched tag
            for intent in self.intents_data:
                if intent["tag"] == matched_tag:
                    return random.choice(intent["responses"])
        
        return "I'm sorry, I don't quite understand that. Could you rephrase?"

# Singleton instance to be used by the Flask app
chatbot_model = ChatbotModel()

def get_bot_response(message):
    return chatbot_model.get_response(message)
