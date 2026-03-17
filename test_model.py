print("Importing sentence_transformers...")
try:
    from sentence_transformers import SentenceTransformer
    print("Successfully imported SentenceTransformer")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Successfully loaded model")
except Exception as e:
    print(f"Error: {e}")
