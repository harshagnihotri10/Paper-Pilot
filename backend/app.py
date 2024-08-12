from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

app = Flask(__name__)

# Database connection helper function
def get_db_connection():
    conn = psycopg2.connect(
        dbname='paperpilot',
        user='paperpilot_user',
        password='userpaperpilot',
        host='localhost'
    )
    return conn

# Helper function to hash passwords
def hash_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')
    
# Helper function to check passwords
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# User registration endpoint
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password_hash = hash_password(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
            (username, email, password_hash)
        )
        conn.commit()
        return jsonify({"status": "User registered successfully"}), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# User login endpoint
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            'SELECT user_id, username, password_hash FROM users WHERE email = %s',
            (email,)
        )
        user = cursor.fetchone()
        
        if user and check_password(password, user['password_hash'].encode('utf-8')):
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s',
                (user['user_id'],)
            )
            conn.commit()

            user.pop('password_hash', None)

            return jsonify({"status": "Login successful", "user": user})
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# User profile update endpoint
@app.route('/user/profile', methods=['POST'])
def update_profile():
    data = request.get_json()
    user_id = data.get('user_id')
    new_email = data.get('email')
    new_username = data.get('username')
    profile_picture_url = data.get('profile_picture_url')
    bio = data.get('bio')
    
    if not user_id or not new_email or not new_username:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
             '''
            UPDATE users 
            SET email = %s, username = %s, profile_picture_url = %s, bio = %s 
            WHERE user_id = %s
            ''',
            (new_email, new_username, profile_picture_url, bio, user_id)
        )

        conn.commit()
        return jsonify({"status": "Profile updated successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Upload article endpoint
@app.route('/upload', methods=['POST'])
def upload_article():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        sql = '''
        INSERT INTO articles (title, abstract, authors, journal, publication_date, doi, keywords, summary, content, pdf_url, thumbnail_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING article_id
        '''
        cursor.execute(sql, (data.get('title'), data.get('abstract'), data.get('authors'), data.get('journal'), data.get('publication_date'), data.get('doi'), data.get('keywords'), data.get('summary'), data.get('content'), data.get('pdf_url'), data.get('thumbnail_url')))
        conn.commit()
        result = cursor.fetchone()
        article_id = result['article_id'] if result else None
        return jsonify({"status": "Article uploaded", "article_id": article_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Search endpoint
@app.route('/search', methods=['GET'])
def search_articles():
    query = request.args.get('query')
    user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Log the search query
        cursor.execute(
            'INSERT INTO search_logs (user_id, search_query) VALUES (%s, %s)',
            (user_id, query)
        )
        conn.commit()
        
        # Perform the search
        cursor.execute(
            "SELECT * FROM articles WHERE title ILIKE %s OR content ILIKE %s",
            ('%' + query + '%', '%' + query + '%')
        )
        results = cursor.fetchall()
        return jsonify({"articles": results})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Summarize article endpoint
@app.route('/summarize', methods=['POST'])
def summarize_article():
    data = request.get_json()
    article_id = data.get('article_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute('SELECT content FROM articles WHERE article_id = %s', (article_id,))
        article = cursor.fetchone()
        
        if not article:
            return jsonify({"error": "Article not found"}), 404
        
        # Assume we have a function to summarize content
        summary = summarize_text(article['content'])
        
        cursor.execute(
            'UPDATE articles SET summary = %s WHERE article_id = %s',
            (summary, article_id)
        )
        conn.commit()
        
        return jsonify({"status": "Article summarized", "summary": summary})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Feedback endpoint
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    user_id = data.get('user_id')
    article_id = data.get('article_id')
    comments = data.get('comments')
    rating = data.get('rating')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO feedback (user_id,  article_id, comments, rating) VALUES (%s, %s, %s, %s)',
            (user_id, article_id, comments, rating)
        )
        conn.commit()

        return jsonify({"status": "Feedback submitted"})
    except Exception as e:
        conn.rollback()

        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Notifications endpoint
@app.route('/notifications', methods=['GET'])
def get_notifications():
    user_id = request.args.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            'SELECT * FROM notifications WHERE user_id = %s AND read = FALSE ORDER BY created_date DESC',
            (user_id,)
        )
        notifications = cursor.fetchall()

        cursor.execute(
            'UPDATE notifications SET read = TRUE WHERE user_id = %s AND read = FALSE',
            (user_id,)
        )
        conn.commit()
        
        return jsonify({"notifications": notifications})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Article views endpoint
@app.route('/article/<int:article_id>/view', methods=['POST'])
def view_article(article_id):
    user_id = request.get_json().get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO article_views (user_id, article_id) VALUES (%s, %s)',
            (user_id, article_id)
        )
        cursor.execute(
            'UPDATE articles SET views = views + 1 WHERE article_id = %s',
            (article_id,)
        )
        conn.commit()
        return jsonify({"status": "Article viewed"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Article likes endpoint
@app.route('/article/<int:article_id>/like', methods=['POST'])
def like_article(article_id):
    user_id = request.get_json().get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO article_likes (user_id, article_id) VALUES (%s, %s)',
            (user_id, article_id)
        )
        cursor.execute(
            'UPDATE articles SET likes = likes + 1 WHERE article_id = %s',
            (article_id,)
        )
        conn.commit()
        return jsonify({"status": "Article liked"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# List all articles endpoint
@app.route('/articles', methods=['GET'])
def list_articles():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute('SELECT * FROM articles')
        articles = cursor.fetchall()
        return jsonify({"articles": articles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Filter articles endpoint
@app.route('/filter', methods=['GET'])
def filter_articles():
    author = request.args.get('author')
    date = request.args.get('date')
    tag = request.args.get('tag')
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        if author:
            query += " AND authors = %s"
            params.append(author)
        if date:
            query += " AND publication_date = %s"
            params.append(date)
        if tag:
            query += " AND keywords LIKE %s"
            params.append('%' + tag + '%')
        cursor.execute(query, params)
        filtered_articles = cursor.fetchall()
        return jsonify({"articles": filtered_articles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Recommendations endpoint
@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            'SELECT articles.* FROM articles '
            'JOIN recommendations ON articles.article_id = recommendations.article_id '
            'WHERE recommendations.user_id = %s',
            (user_id,)
        )
        recommendations = cursor.fetchall()
        return jsonify({"articles": recommendations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
    