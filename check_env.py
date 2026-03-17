import sys
import os

print(f"Python version: {sys.version}")
try:
    import flask
    print("Flask is installed")
except ImportError:
    print("Flask is NOT installed")

try:
    import nltk
    print("NLTK is installed")
except ImportError:
    print("NLTK is NOT installed")

try:
    from sentence_transformers import SentenceTransformer
    print("SentenceTransformer is installed")
except ImportError:
    print("SentenceTransformer is NOT installed")

try:
    import mysql.connector
    print("MySQL connector is installed")
except ImportError:
    print("MySQL connector is NOT installed")
