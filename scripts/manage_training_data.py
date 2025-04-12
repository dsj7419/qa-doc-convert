"""
Script to manage training data and models.
"""
import os
import sys
import logging
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.learning_service import LearningService

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Manage training data and models")
    parser.add_argument('--stats', action='store_true', help="Show training data statistics")
    parser.add_argument('--train', action='store_true', help="Force model training")
    parser.add_argument('--clear', action='store_true', help="Clear all training data (caution!)")
    args = parser.parse_args()
    
    # Create learning service
    learning_service = LearningService()
    
    # Show stats
    if args.stats or not (args.train or args.clear):
        stats = learning_service.get_training_stats()
        print("\n=== Training Data Statistics ===")
        print(f"Total examples: {stats['total_examples']}")
        print("Examples by class:")
        for role, count in stats['by_class'].items():
            print(f"  - {role}: {count}")
        print(f"Model file exists: {stats['has_model']}")
        print(f"AI components available: {stats['ai_available']}")
        print()
    
    # Force training
    if args.train:
        if learning_service.has_enough_data_to_train():
            print("Training model...")
            success = learning_service.train_model(force=True)
            if success:
                print("Model training successful!")
            else:
                print("Model training failed. See log for details.")
        else:
            print("Not enough training data to train a reliable model.")
            print("Add more examples before training.")
    
    # Clear training data
    if args.clear:
        confirm = input("Are you sure you want to clear all training data? (yes/no): ")
        if confirm.lower() == 'yes':
            learning_service.training_data = {
                'question': [],
                'answer': [],
                'ignore': []
            }
            learning_service.data_changed = True
            learning_service._save_training_data()
            print("Training data cleared.")
        else:
            print("Operation cancelled.")

if __name__ == "__main__":
    main()