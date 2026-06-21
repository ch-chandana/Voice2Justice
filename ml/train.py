"""
Training Script
================
Train the TF-IDF + Multinomial NB classifier and save model artifacts.

Usage:
    cd flask/
    python -m ml.train

Outputs:
    ml/saved_models/complaint_pipeline.pkl
    ml/saved_models/label_classes.pkl
"""
import sys
import os

# Ensure flask/ is on sys.path when run as `python -m ml.train`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.ml_model import ComplaintClassifier


def main():
    print('=' * 60)
    print('  Voice2Justice — ML Model Training')
    print('=' * 60)

    clf = ComplaintClassifier()

    # 1. Load training data
    print('\n[1/3] Loading training data...')
    texts, labels = clf.load_training_data()
    print(f'      Loaded {len(texts)} samples across {len(set(labels))} categories.')

    # Show class distribution
    from collections import Counter
    dist = Counter(labels)
    print('\n      Class distribution:')
    for label, count in sorted(dist.items()):
        print(f'        {label:20s} → {count} samples')

    # 2. Train
    print('\n[2/3] Training TF-IDF + MultinomialNB pipeline...')
    metrics = clf.train(texts, labels)

    print(f'\n      ✓ Hold-out Test Accuracy: {metrics["test_accuracy"]:.2%}')
    print(f'      ✓ Train size: {metrics["train_size"]} | Test size: {metrics["test_size"]}')
    print(f'      ✓ Classes: {metrics["n_classes"]}')
    print(f'      ✓ Total Samples: {metrics["n_samples"]}')
    print(f'\n      Classification Report (on test set):')
    for line in metrics['report'].split('\n'):
        print(f'      {line}')

    # 3. Save
    print('\n[3/3] Saving model to disk...')
    save_dir = clf.save()
    print(f'      ✓ Saved to: {save_dir}')

    # 4. Quick smoke test
    print('\n' + '=' * 60)
    print('  Smoke Test — Example Predictions')
    print('=' * 60)

    test_cases = [
        'someone stole my wallet from the bus',
        'I was beaten up by strangers near the park',
        'a woman was stalked and harassed on her way home',
        'there is a huge pothole on the main road',
        'garbage has not been collected for one week',
        'no electricity in our area since yesterday',
        'factory smoke is polluting the air near our school',
        'my child was kidnapped from outside the school',
        'they are demanding money and threatening my family',
        'I was cheated by an online seller',
        'water supply has been cut off for three days',
        'the traffic signal is not working at the junction',
    ]

    for text in test_cases:
        result = clf.predict(text)
        print(f'\n  Input:      "{text}"')
        print(f'  Predicted:  {result["label"]}')
        print(f'  Confidence: {result["confidence"]:.2%}')

    print('\n' + '=' * 60)
    print('  Training Complete ✓')
    print('=' * 60)


if __name__ == '__main__':
    main()
