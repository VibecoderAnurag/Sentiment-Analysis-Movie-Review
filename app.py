from flask import Flask, render_template, request
from transformers import pipeline
from textblob import TextBlob
import matplotlib
matplotlib.use('Agg')  # Use a backend that doesn't require GUI
import matplotlib.pyplot as plt  # Now import matplotlib
 


app = Flask(__name__)

import sqlite3

# Function to create a database and table (if not exists)
def create_database():
    conn = sqlite3.connect("reviews.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie TEXT NOT NULL,
            review TEXT NOT NULL,
            sentiment TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Call this function when app starts
create_database()


# Load sentiment analysis model
sentiment_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

CUSTOM_LABELS = ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative", "Sarcastic"]

def classify_sentiment(review):
    result = sentiment_pipeline(review, CUSTOM_LABELS)
    scores = {label: score for label, score in zip(result["labels"], result["scores"])}

    highest_label = result["labels"][0]
    highest_confidence = result["scores"][0]

    # Use TextBlob for extra polarity check
    blob = TextBlob(review)
    polarity = blob.sentiment.polarity  # -1 (negative) to +1 (positive)

    # **Fix for Sarcasm Detection**
    if highest_label in ["Positive", "Very Positive"] and polarity < -0.1:
        highest_label = "Sarcastic"

    # **Fix for "Very Negative" Misclassification**
    if highest_label == "Negative" and scores["Very Negative"] > 0.55:
        highest_label = "Very Negative"

    # **Fix for "Very Positive" vs. "Positive"**
    if highest_label == "Positive" and scores["Very Positive"] > 0.6:
        highest_label = "Very Positive"

    # **Fix for "Negative" Being Misclassified as Neutral**
    if highest_label == "Neutral" and scores["Negative"] > 0.5:
        highest_label = "Negative"

    emoji_map = {
        "Very Positive": "😍✨",
        "Positive": "😊",
        "Neutral": "😐",
        "Negative": "😠",
        "Very Negative": "😡💔",
        
    }

    # **Store sentiment without emoji in DB**
    return highest_label  # ✅ Fix: Save only text, not emoji

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    movie = request.form["movie"]
    review = request.form["review"]
    sentiment = classify_sentiment(review)  # ✅ Already returns clean text

    # Store the review in database
    conn = sqlite3.connect("reviews.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO reviews (movie_name, review_text, sentiment) VALUES (?, ?, ?)", (movie, review, sentiment))

    conn.commit()
    conn.close()

    # ✅ Add emoji for display, but store clean text in DB
    emoji_map = {
        "Very Positive": "😍✨",
        "Positive": "😊",
        "Neutral": "😐",
        "Negative": "😠",
        "Very Negative": "😡💔",
    }
    sentiment_display = f"{emoji_map[sentiment]} {sentiment}"

    return render_template("results.html", review=review, result=sentiment_display)

@app.route('/view_reviews', methods=['POST'])
def view_reviews():
    movie_name = request.form['movie_name']
    
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT review_text, sentiment FROM reviews WHERE movie_name = ?", (movie_name,))

    reviews = [{'review_text': row[0], 'sentiment': row[1]} for row in cursor.fetchall()]
    
    conn.close()

    # 🟢 Fix case sensitivity & count properly
    sentiment_counts = {
        "Very Positive": 0,
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
        "Very Negative": 0,
    }

    for review in reviews:
        sentiment_text = review['sentiment']
        if sentiment_text in sentiment_counts:  # ✅ Ensure valid sentiment
            sentiment_counts[sentiment_text] += 1

    # 🟢 Generate Sentiment Breakdown Pie Chart (for individual reviews)
    labels = list(sentiment_counts.keys())
    sizes = list(sentiment_counts.values())

    import numpy as np

    # Convert NaN values to 0
    sizes = [0 if np.isnan(x) else x for x in sizes]

    # Ensure at least one value is non-zero
    if sum(sizes) == 0:
        sizes = [1] * len(sizes)  # ✅ Set dummy values to avoid errors

    # Sentiment Breakdown Pie Chart (this is for reviews only)
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"Sentiment Breakdown for {movie_name}")

    # Save plot as an image
    chart_path = "static/sentiment_breakdown_chart.png"
    plt.savefig(chart_path)
    plt.close()  # ✅ Prevent memory leaks

    # Return to the template without the overall sentiment chart
    return render_template('view_reviews.html', movie=movie_name, reviews=reviews, sentiment_counts=sentiment_counts, chart_path=chart_path)



if __name__ == "__main__":
    app.run(debug=True)
