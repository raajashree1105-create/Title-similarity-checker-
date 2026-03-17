
import re

def normalize_title(text):
    if not text:
        return ""
    # convert to lowercase
    text = text.lower()
    # remove extra spaces
    text = " ".join(text.split())
    # split camel case words
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return text

def enhance_title(text):
    if not text:
        return ""
    # 1. Detect CamelCase words and split them into separate words
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # 2. Case Normalization
    text = text.lower()
    return text

test_title = "SmartWatchApplication"
normalized = normalize_title(test_title)
enhanced = enhance_title(test_title)

print(f"Original: {test_title}")
print(f"Normalized: '{normalized}'")
print(f"Enhanced: '{enhanced}'")

# In calculate_similarity:
# new_title = normalize_title(new_title)
# processed_new_title = preprocess_text(new_title) -> calls enhance_title(normalized)
combined = enhance_title(normalized)
print(f"Combined (as in app.py): '{combined}'")
