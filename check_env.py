import sys
import os

print(f"Python version: {sys.version}")
try:
    import flask  # type: ignore
    print("Flask is installed")
except ImportError:
    print("Flask is NOT installed")

try:
    import nltk  # type: ignore
    print("NLTK is installed")
except ImportError:
    print("NLTK is NOT installed")

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    print("SentenceTransformer is installed")
except ImportError:
    print("SentenceTransformer is NOT installed")

try:
    import mysql.connector  # type: ignore
    print("MySQL connector is installed")
except ImportError:
    print("MySQL connector is NOT installed")
