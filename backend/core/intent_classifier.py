import json
import os
import sys
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline


class IntentClassifier:
    def __init__(self):

        # ==========================================
        # RUTA DE LOS RECURSOS INCLUIDOS
        # ==========================================
        if getattr(sys, 'frozen', False):
            # Ejecutándose como .exe de PyInstaller
            base_dir = sys._MEIPASS
        else:
            # Ejecutándose normalmente con Python
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.dataset_path = os.path.join(
            base_dir,
            'data',
            'dataset.json'
        )

        # ==========================================
        # RUTA PERSISTENTE PARA EL MODELO
        # ==========================================
        if getattr(sys, 'frozen', False):
            # Guardamos el modelo fuera del directorio temporal de PyInstaller
            app_data = os.path.join(
                os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                'Eco',
                'data'
            )

            os.makedirs(app_data, exist_ok=True)

            self.model_path = os.path.join(
                app_data,
                'eco_brain.pkl'
            )

        else:
            # Desarrollo
            self.model_path = os.path.join(
                base_dir,
                'data',
                'eco_brain.pkl'
            )

        self.model = None

    def train(self):
        print("Entrenando el cerebro de Eco (v3 - Calibrado)...")

        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        texts = []
        labels = []

        for intent in data['intents']:
            for pattern in intent['patterns']:
                texts.append(pattern)
                labels.append(intent['tag'])

        # Pipeline calibrado
        base_model = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('clf', LogisticRegression(max_iter=1000))
        ])

        # Calibrar las probabilidades
        self.model = CalibratedClassifierCV(
            base_model,
            method='sigmoid',
            cv=3
        )

        self.model.fit(texts, labels)

        joblib.dump(self.model, self.model_path)

        print("Cerebro v3 calibrado y guardado.")

    def load(self):
        if os.path.exists(self.model_path):
            print(f"Cargando modelo: {self.model_path}")
            self.model = joblib.load(self.model_path)
        else:
            self.train()

    def predict(self, text):
        if self.model is None:
            self.load()

        prediction = self.model.predict([text])[0]
        probabilities = self.model.predict_proba([text])[0]
        confidence = max(probabilities) * 100

        return prediction, confidence


if __name__ == "__main__":
    classifier = IntentClassifier()

    test_phrases = [
        "hola eco",
        "buenos días",
        "hola buenos días",
        "abre spotify",
        "qué tiempo hace",
        "cuál es el sentido de la vida"
    ]

    for phrase in test_phrases:
        intent, confidence = classifier.predict(phrase)

        print(f"\n🗣️ '{phrase}'")
        print(f"   🎯 Intención: {intent} | Confianza: {confidence:.2f}%")