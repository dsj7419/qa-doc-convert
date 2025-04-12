"""
Script to train and export a Q&A classifier model using pickle.
"""
import os
import pickle
import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_and_export_model():
    """Train and export a QA classifier model."""
    logger.info("Training Q&A classifier model...")
    
    try:
        # Import scikit-learn components
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        logger.error("scikit-learn not installed. Cannot train model.")
        return
    
    # Sample data (in production, we would use a larger dataset)
    data = {
        'text': [
            "What is jurisdiction?",
            "Name the types of jurisdiction.",
            "How many factors are there?",
            "What are the 3 requirements?",
            "1. There are 2 kinds of jurisdiction. What are they?",
            "List the types of jurisdiction.",
            "Identify the 4 factors used to determine the course of action.",
            "When is personal jurisdiction traditionally based?",
            "Under long arm statutes, name 5 theories that permit a court to exercise jurisdiction.",
            "Subject matter jurisdiction relates only to federal courts.",
            "The relationship between compulsory counterclaims and res judicata is...",
            "A crossclaim is never compulsory.",
            "Answer: It's the power of a court to hear a case.",
            "The court uses 4 factors to determine...",
            "Venue is proper in 3 scenarios where:",
            "1. Personal\n\n2. Subject matter",
            "1. Diversity\n\n2. Federal question",
            "**PC**",
            "CIVIL PROCEDURE (50 questions)",
            "JW Bar Method CA Bar Essay Quizzes"
        ],
        'label': [
            'question', 'question', 'question', 'question', 'question',
            'question', 'question', 'question', 'question',
            'answer', 'answer', 'answer', 'answer', 'answer',
            'answer', 'answer', 'answer',
            'ignore', 'ignore', 'ignore'
        ]
    }

    # Create a dataframe
    df = pd.DataFrame(data)
    logger.info(f"Training data: {len(df)} examples")

    # Create vectorizer
    vectorizer = CountVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words='english'
    )

    # Fit and transform
    X = vectorizer.fit_transform(df['text']).toarray()
    logger.info(f"Feature matrix shape: {X.shape}")

    # Create resources directory if it doesn't exist
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
    os.makedirs(resources_dir, exist_ok=True)

    # Save vocabulary for inference
    np.save(os.path.join(resources_dir, "vocabulary.npy"), vectorizer.vocabulary_)
    logger.info(f"Vocabulary saved with {len(vectorizer.vocabulary_)} features")

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['label'])
    # Save label encoder mapping for reference
    label_mapping = {i: label for i, label in enumerate(le.classes_)}
    logger.info(f"Label mapping: {label_mapping}")

    # Train a simple model
    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    logger.info("Model training complete")

    # Save the model using pickle
    with open(os.path.join(resources_dir, "qa_classifier.pkl"), "wb") as f:
        pickle.dump(model, f)

    logger.info(f"Model exported to {os.path.join(resources_dir, 'qa_classifier.pkl')}")
    logger.info(f"Vocabulary exported to {os.path.join(resources_dir, 'vocabulary.npy')}")

if __name__ == "__main__":
    train_and_export_model()