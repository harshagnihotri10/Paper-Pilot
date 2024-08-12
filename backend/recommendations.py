from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def recommend_articles(user_id, cursor):
    # Fetch user interaction data
    cursor.execute(
        'SELECT article_id FROM article_views WHERE user_id = %s', (user_id,)
    )
    viewed_articles = cursor.fetchall()

    # Placeholder: Actual logic to fetch and compare article vectors
    # Example similarity calculation
    recommendations = []
    for article in all_articles:
        similarity = cosine_similarity(user_vector, article_vector)
        recommendations.append((article, similarity))

    recommendations.sort(key=lambda x: x[1], reverse=True)
    return recommendations[:5]
