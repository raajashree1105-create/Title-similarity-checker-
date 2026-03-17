from flask import Flask, render_template, request, redirect, url_for, session, flash  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore
import re
import string
import nltk  # type: ignore
from nltk.tokenize import word_tokenize  # type: ignore
from nltk.stem import WordNetLemmatizer, PorterStemmer  # type: ignore
from nltk.corpus import stopwords, wordnet  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore

# Ensure necessary NLTK datasets are downloaded
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)

app = Flask(__name__)
app.secret_key = 'super_secret_academic_key'

# Load SentenceTransformer model once at startup
print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

# ==========================================
# DATABASE CONFIGURATION (MySQL)
# ==========================================
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='title_similarity',
            user='root',
            password='raji@123'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Helper function to fetch all titles from database
def fetch_all_titles():
    conn = get_db_connection()
    titles = []
    if conn:
        cursor = conn.cursor()
        # Fetching all existing titles
        cursor.execute("SELECT title FROM project_titles")
        results = cursor.fetchall()
        titles = [row[0] for row in results]
        cursor.close()
        conn.close()
    return titles

# ==========================================
# NLP LOGIC FOR TITLE SIMILARITY
# ==========================================

def normalize_title(text):
    """
    Core normalization: lowercase, remove punctuation, and split CamelCase.
    """
    if not text:
        return ""
        
    # 1. Split CamelCase (SmartWatch -> Smart Watch)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
    # 2. Convert to lowercase
    text = text.lower()
    
    # 3. Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # 4. Remove extra spaces
    text = " ".join(text.split()).strip()
    
    return text

def remove_spaces(text):
    """
    Removes all spaces for strict duplicate checking.
    """
    return text.replace(" ", "")

def enhance_title(text):
    """
    Enhancement layer that runs BEFORE the existing NLP pipeline.
    Addresses CamelCase splitting, case normalization, space variations,
    abbreviations, and programming language neutralization.
    """
    if not text:
        return ""
        
    # 1. Detect CamelCase words and split them into separate words
    # Handle acronym followed by capitalized word (e.g., AIFeatured -> AI Featured)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    # Handle lowercase followed by uppercase (e.g., SmartWatch -> Smart Watch)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
    # 2. Case Normalization
    text = text.lower()
    
    # 3. Abbreviation Expansion
    abbreviations = {
        r'\bai\b': 'artificial intelligence',
        r'\bml\b': 'machine learning',
        r'\bnlp\b': 'natural language processing',
        r'\biot\b': 'internet of things'
    }
    for abbr, expansion in abbreviations.items():
        text = re.sub(abbr, expansion, text)
        
    # 4. Programming Language Neutralization (and connector words like 'using')
    languages_and_connectors = [
        r'\bpython\b', r'\bjava\b', r'\bphp\b', r'\bc\+\+\b', 
        r'\bjavascript\b', r'\bc#\b', r'\busing\b', r'\bin\b', r'\bwith\b'
    ]
    for word in languages_and_connectors:
        text = re.sub(word, '', text)
        
    # 5. Space Normalization
    # Handles specific concatenated words like 'groceryshop'
    exact_space_fixes = {
        r'\bgroceryshop\b': 'grocery shop'
    }
    for no_space, spaced in exact_space_fixes.items():
        text = re.sub(no_space, spaced, text)
        
    # Remove any extra spaces that might have been created by the removals
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_text(text):
    if not text:
        return ""
        
    # --- ENHANCEMENT LAYER APPLIED HERE (Cleaning) ---
    text = enhance_title(text)
    
    # 1. Convert to lowercase
    text = text.lower()
    # 2. Remove punctuation
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    # 3. Tokenization
    tokens = word_tokenize(text)
    
    # 4. Stopword Removal (Requested Step 1)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    # 5. Synonym Detection (Requested Step 3)
    # Map words to canonical synonyms using WordNet
    synonym_tokens = []
    for token in tokens:
        synsets = wordnet.synsets(token)
        if synsets:
            # Map to the first lemma of the first synset as a representative
            canonical = synsets[0].lemmas()[0].name().lower().replace('_', ' ')
            synonym_tokens.append(canonical)
        else:
            synonym_tokens.append(token)
    tokens = synonym_tokens

    # 6. Stemming (Requested Step 2)
    # Use PorterStemmer to convert words to root form
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    
    # 7. Filter out project-specific noise words
    noise_words = {
        'system', 'application', 'platform', 'project', 'approach', 
        'implementation', 'design', 'development', 'using', 'based', 
        'software', 'framework', 'management', 'analysis', 'tool',
        'web', 'mobile', 'app', 'online', 'module', 'architecture',
        'technique', 'study', 'evaluation', 'model', 'method'
    }
    tokens = [word for word in tokens if word not in noise_words]
    
    return " ".join(tokens)

def extract_keywords(text):
    """
    Extracts high-value keywords from a title using tokenization and POS filtering.
    """
    if not text:
        return []
        
    # Standard cleanup first
    text_clean = enhance_title(text)
    text_clean = re.sub(f"[{re.escape(string.punctuation)}]", "", text_clean)
    tokens = word_tokenize(text_clean.lower())
    
    # POS Tagging (optional but helps identify nouns/adjectives)
    # We'll stick to a list-based approach as requested by "simple tokenization"
    # but enhanced with noise filtering.
    stop_words = set(stopwords.words('english'))
    noise_words = {
        'system', 'application', 'platform', 'project', 'approach', 
        'implementation', 'design', 'development', 'using', 'based', 
        'software', 'framework', 'management', 'analysis', 'tool',
        'web', 'mobile', 'app', 'online', 'module', 'architecture',
        'technique', 'study', 'evaluation', 'model', 'method'
    }
    
    keywords = [
        word for word in tokens 
        if isinstance(word, str) and word not in stop_words and word not in noise_words and len(word) > 2
    ]
    
    return sorted(list(set(keywords)))

def calculate_similarity(new_title, titles_list):
    if not titles_list or not new_title or not new_title.strip():
        return 0.0, "No existing titles to compare against."
    
    # --- Step 1: Normalize both for standard comparison ---
    new_title_clean = normalize_title(new_title)
    titles_list_clean = [normalize_title(t) for t in titles_list]
    
    # --- Step 2: Space-insensitive exact match check (100% similarity) ---
    new_title_no_space = remove_spaces(new_title_clean)
    titles_no_space = [remove_spaces(t) for t in titles_list_clean]
    
    if new_title_no_space in titles_no_space:
        match_index = titles_no_space.index(new_title_no_space)
        return 100.0, titles_list[match_index]  # Return original title from list
    
    # --- Step 3: Fallback to existing TF-IDF pipeline if not an exact space-less match ---
    # Preprocess all titles (this includes existing enhancement logic)
    processed_new_title = preprocess_text(new_title_clean)
    processed_titles_list = [preprocess_text(title) for title in titles_list_clean]
    
    # Add the preprocessed new title to the list to vectorize them all together
    all_titles = [processed_new_title] + processed_titles_list
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
    try:
        tfidf_matrix = vectorizer.fit_transform(all_titles)
    except ValueError:
        return 0.0, "Could not determine similarity (no significant words)."
    
    # Calculate cosine similarity of the new_title (index 0) with all others
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    # Find the maximum similarity score and the corresponding title
    max_sim_score = cosine_sim[0].max()
    max_sim_index = cosine_sim[0].argmax()
    
    most_similar_title = titles_list[max_sim_index]
    similarity_percentage = float(round(max_sim_score * 100, 2))
    
    return similarity_percentage, most_similar_title

def calculate_semantic_similarity(new_title, titles_list):
    """
    Calculates semantic similarity using SentenceTransformer (all-MiniLM-L6-v2).
    """
    if not titles_list or not new_title or not new_title.strip():
        return 0.0, "No existing titles to compare against."

    # Clean titles before embedding (Processing Flow: Text Cleaning)
    new_title_clean = enhance_title(new_title)
    titles_list_clean = [enhance_title(t) for t in titles_list]

    # Convert titles to embeddings
    new_embedding = semantic_model.encode([new_title_clean])
    existing_embeddings = semantic_model.encode(titles_list_clean)

    # Calculate cosine similarity
    similarities = cosine_similarity(new_embedding, existing_embeddings)[0]

    # Find the maximum similarity score and the corresponding title
    max_sim_score = similarities.max()
    max_sim_index = similarities.argmax()

    most_similar_title = titles_list[max_sim_index]
    similarity_percentage = float(f"{max_sim_score.item() * 100:.2f}")
    similarity_percentage = max(0.0, min(100.0, similarity_percentage))

    return similarity_percentage, most_similar_title

# ==========================================
# APP ROUTES
# ==========================================

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user:
                session['role'] = user['role']
                session['name'] = user['fullname']
                session['email'] = user['email']
                session['user_id'] = user['id']
                
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                flash("Invalid email or password.")
        else:
            flash("Database connection failed. Check your MySQL server.")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Insert the user. We assume new registered users are students.
                cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (%s, %s, %s, 'student')", 
                               (fullname, email, password))
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                if err.errno == 1062: # Duplicate entry
                    flash("Email already registered!")
                else:
                    flash(f"Database error: {err}")
            finally:
                cursor.close()
                conn.close()
        else:
            flash("Database connection failed. Check your MySQL server.")
            
    return render_template('register.html')

@app.route('/student_dashboard')
def student_dashboard():
    # Protection
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
        
    return render_template('student_dashboard.html', result=None)

@app.route('/submit', methods=['POST'])
def submit():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
        
    project_title = request.form.get('project_title')
    
    # Fetch existing titles from DB
    existing_titles = fetch_all_titles()
    
    # Calculate Similarity using existing TF-IDF function
    tfidf_score, tfidf_similar_title = calculate_similarity(project_title, existing_titles)
    
    # Calculate Semantic Similarity using new SentenceTransformer function
    semantic_score, semantic_similar_title = calculate_semantic_similarity(project_title, existing_titles)
    
    # --- COMBINE SCORES ---
    # We take the maximum of both to ensure no similarity is missed
    final_score = max(tfidf_score, semantic_score)
    final_similar_title = tfidf_similar_title if tfidf_score >= semantic_score else semantic_similar_title
    
    # Determine risk level based on the final combined score
    if final_score >= 70:
        score_class = 'score-high'
        status = 'Highly Similar'
    elif final_score >= 40:
        score_class = 'score-medium'
        status = 'Moderately Similar'
    else:
        score_class = 'score-low'
        status = 'Not Similar'
        
    result = {
        'submitted_title': project_title,
        'final_score': final_score,
        'similar_title': final_similar_title,
        'score_class': score_class,
        'status': status,
        'breakdown': {
            'tfidf': tfidf_score,
            'semantic': semantic_score
        }
    }
    
    # Save the new title and submission details to the MySQL database
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # We maintain the existing storage logic using the final combined status
            db_status = 'Duplicate' if final_score >= 70 else ('Moderately Similar' if final_score >= 40 else 'Unique')
            student_email = session.get('email', 'unknown')
            cursor.execute(
                "INSERT INTO project_titles (student_email, title, similar_title, similarity_score, status) VALUES (%s, %s, %s, %s, %s)",
                (student_email, project_title, result['similar_title'], result['final_score'], db_status)
            )
            
            conn.commit()
        except Exception as e:
            print(f"Error saving submission: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('student_dashboard.html', result=result)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='admin'", (email, password))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user:
                session['role'] = user['role']
                session['name'] = user['fullname']
                session['email'] = user['email']
                session['user_id'] = user['id']
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid admin credentials.")
        else:
            flash("Database connection failed.")
            
    return render_template('admin_login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email=%s AND role='admin'", (email,))
            user = cursor.fetchone()
            if user:
                cursor.execute("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
                conn.commit()
                flash("Password successfully reset.", 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_login'))
            else:
                flash("Admin account with that email not found.")
                cursor.close()
                conn.close()
        else:
            flash("Database connection failed.")
            
    return render_template('forgot_password.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    # Protection
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
        
    return render_template('admin_dashboard.html')

@app.route('/view_titles')
def view_titles():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
        
    conn = get_db_connection()
    titles = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM project_titles ORDER BY id DESC")
            titles = cursor.fetchall()
            if titles is None:
                titles = []
        except Exception as e:
            print(f"Failed pulling data: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('view_titles.html', titles=titles)

@app.route('/delete_title/<int:title_id>')
def delete_title(title_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM project_titles WHERE id = %s", (title_id,))
            conn.commit()
            flash("Title deleted successfully.", "success")
        except Exception as e:
            flash(f"Error deleting title: {e}", "danger")
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('view_titles'))

@app.route('/delete_all_titles', methods=['POST'])
def delete_all_titles():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM project_titles")
            conn.commit()
            flash("All titles have been cleared.", "success")
        except Exception as e:
            flash(f"Error clearing titles: {e}", "danger")
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('view_titles'))

@app.route('/reports')
def reports():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
        
    stats = { 'total': 0, 'unique': 0, 'moderate': 0, 'duplicate': 0 }
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM project_titles")
            stats['total'] = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM project_titles WHERE status='Unique'")
            stats['unique'] = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM project_titles WHERE status='Moderately Similar'")
            stats['moderate'] = cursor.fetchone()['cnt']
            
            cursor.execute("SELECT COUNT(*) as cnt FROM project_titles WHERE status='Duplicate'")
            stats['duplicate'] = cursor.fetchone()['cnt']
        except Exception as e:
            print(f"Failed pulling data: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('reports.html', stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
