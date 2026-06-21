"""
ML Model — Complaint Classifier
=================================
TF-IDF Vectorizer + Multinomial Naive Bayes pipeline for classifying
citizen complaints into crime/civic sub-categories.

Usage:
    from ml.ml_model import ComplaintClassifier

    clf = ComplaintClassifier()
    clf.load()                           # loads saved model from disk
    result = clf.predict("pothole on road")
    # → {'label': 'roads', 'confidence': 0.87, 'all_probabilities': {...}}
"""
import json
import os
import pickle

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

# Directory where trained model artifacts are persisted
_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_models')
_PIPELINE_PATH = os.path.join(_MODEL_DIR, 'complaint_pipeline.pkl')
_LABELS_PATH = os.path.join(_MODEL_DIR, 'label_classes.pkl')
_TRAINING_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training_data.json')


class ComplaintClassifier:
    """TF-IDF + Multinomial Naive Bayes complaint classifier."""

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self.labels: list[str] | None = None
        self.is_loaded = False

    # ── Training ──────────────────────────────────────────────────────────

    def train(self, texts: list[str], labels: list[str]) -> dict:
        """
        Train the model on (text, label) pairs.

        Returns a dict with:
            accuracy      — mean cross-validated accuracy
            cv_scores     — per-fold accuracy scores
            report        — sklearn classification_report as a string
            n_samples     — number of training samples
            n_classes     — number of unique classes
        """
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),       # unigrams + bigrams
                stop_words='english',
                sublinear_tf=True,        # apply log normalization
                min_df=1,
                max_df=0.95,
            )),
            ('clf', MultinomialNB(alpha=0.1)),  # Laplace smoothing
        ])

        # Train/test split (80% train, 20% test)
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # Train on training set for evaluation
        self.pipeline.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred = self.pipeline.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, zero_division=0)

        # Final fit on ALL data for production readiness
        self.pipeline.fit(texts, labels)
        self.labels = list(self.pipeline.classes_)
        self.is_loaded = True

        return {
            'test_accuracy': float(test_accuracy),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'report': report,
            'n_samples': len(texts),
            'n_classes': len(self.labels),
        }

    # ── Prediction ────────────────────────────────────────────────────────

    def predict(self, text: str) -> dict:
        """
        Predict the category for a single complaint text.

        Returns:
            label          — predicted category key (e.g. 'theft', 'roads')
            confidence     — probability of the top prediction (0.0–1.0)
            all_probs      — dict mapping every class → its probability
        """
        if not self.is_loaded or self.pipeline is None:
            raise RuntimeError('Model not loaded. Call .load() or .train() first.')

        proba = self.pipeline.predict_proba([text])[0]
        top_idx = int(np.argmax(proba))
        label = self.labels[top_idx]
        confidence = float(proba[top_idx])

        all_probs = {
            cls: round(float(p), 4)
            for cls, p in zip(self.labels, proba)
        }

        return {
            'label': label,
            'confidence': round(confidence, 4),
            'all_probs': all_probs,
        }

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self) -> str:
        """Save trained pipeline + label list to disk. Returns the save directory."""
        if self.pipeline is None:
            raise RuntimeError('No trained model to save.')

        os.makedirs(_MODEL_DIR, exist_ok=True)

        with open(_PIPELINE_PATH, 'wb') as f:
            pickle.dump(self.pipeline, f)
        with open(_LABELS_PATH, 'wb') as f:
            pickle.dump(self.labels, f)

        print(f'[ML] Model saved to {_MODEL_DIR}')
        return _MODEL_DIR

    def load(self) -> bool:
        """
        Load a previously trained model from disk.

        Returns True if loaded successfully, False if model files missing.
        """
        if not os.path.exists(_PIPELINE_PATH) or not os.path.exists(_LABELS_PATH):
            print('[ML] No saved model found — falling back to keyword classifier.')
            self.is_loaded = False
            return False

        with open(_PIPELINE_PATH, 'rb') as f:
            self.pipeline = pickle.load(f)
        with open(_LABELS_PATH, 'rb') as f:
            self.labels = pickle.load(f)

        self.is_loaded = True
        print(f'[ML] Model loaded — {len(self.labels)} classes ready.')
        return True

    # ── Convenience ───────────────────────────────────────────────────────

    @staticmethod
    def load_training_data(path: str | None = None) -> tuple[list[str], list[str]]:
        """Load training_data.json and return (texts, labels) lists."""
        path = path or _TRAINING_DATA_PATH
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        texts = [item['text'] for item in data]
        labels = [item['label'] for item in data]
        return texts, labels


# ── Module-level singleton ────────────────────────────────────────────────
# Used by services/classifier.py — created once, loaded once on first import.
classifier_instance = ComplaintClassifier()
