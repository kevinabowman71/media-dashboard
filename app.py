
import os
import feedparser
from flask import Flask, render_template, request
from openai import OpenAI
import json

app = Flask(__name__)
client = OpenAI()
from flask import request, Response

USERNAME = "kevin"
PASSWORD = "Trudy2024$"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        "Authentication required", 401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )
    
def analyze_headlines_batch(articles):
    try:
        headlines = [article["title"] for article in articles]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": """
You are a media analysis engine.

For each headline provided, return a JSON list of objects with:

- sentiment (Positive, Neutral, Negative)
- intensity (Low, Moderate, High)
- framing_risk (Low, Moderate, High)
- summary (one short neutral sentence)

Return ONLY valid JSON array.
"""
                },
                {
                    "role": "user",
                    "content": json.dumps(headlines)
                }
            ],
            max_tokens=800
        )

        content = response.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []

    except Exception as e:
        print("AI ERROR:", e)
        return []
@app.before_request
def require_login():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
        
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

CATEGORIES = {
    "World": {
        "Reuters": "http://feeds.reuters.com/Reuters/worldNews",
        "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "Associated Press": "https://apnews.com/rss/apf-worldnews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "NPR": "https://feeds.npr.org/1004/rss.xml",
        "CBS News": "https://www.cbsnews.com/latest/rss/world",
        "ABC News": "https://abcnews.go.com/abcnews/internationalheadlines"
},
   
    "Politics": {
    "Reuters": "http://feeds.reuters.com/Reuters/politicsNews",
    "BBC": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "NPR": "https://feeds.npr.org/1014/rss.xml",
    "Politico": "https://www.politico.com/rss/politics08.xml",
    "The Hill": "https://thehill.com/rss/syndicator/19109",
    "Associated Press": "https://apnews.com/rss/apf-politics",
    
    "The Guardian": "https://www.theguardian.com/us-news/us-politics/rss"
},
    "Business": {
        "Reuters": "http://feeds.reuters.com/reuters/businessNews",
        "BBC": "http://feeds.bbci.co.uk/news/business/rss.xml"
    },
    "Technology": {
        "Reuters": "http://feeds.reuters.com/reuters/technologyNews",
        "BBC": "http://feeds.bbci.co.uk/news/technology/rss.xml"
    }
}
SOURCE_TRUST = {
    "Reuters": 9,
    "BBC": 9,
    "Associated Press": 9,
    "NPR": 8,
    "The Guardian": 7,
    "Politico": 7,
    "The Hill": 6,
    "Fox News": 6,
    "Al Jazeera": 7,
    "CBS News": 8,
    "ABC News": 8
}
def get_headlines(category):
    articles = []
    feeds = CATEGORIES.get(category, {})

    for source, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "source": source
                
            })

    return articles

def summarize_headline(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize this news headline in one short, clear sentence."},
                {"role": "user", "content": title}
            ],
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except:
        return None



from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_cross_confirmation(article, all_articles):
    similar_count = 0

    for other in all_articles:
        if other == article:
            continue
        if similarity(article["title"], other["title"]) > 0.6:
            similar_count += 1

    if similar_count >= 3:
        return "Widely Confirmed", similar_count
    elif similar_count >= 1:
        return "Moderately Confirmed", similar_count
    else:
        return "Low Confirmation", similar_count  
        
def get_framing_risk(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify the rhetorical framing intensity of this headline as Low, Moderate, or High."},
                {"role": "user", "content": title}
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except:
        return "Unknown"
@cache.cached(timeout=900)  # 15 minutes         
@app.route("/")
def index():
    category = request.args.get("category", "World")
    articles = get_headlines(category)
    analysis_results = analyze_headlines_batch(articles)

for i, article in enumerate(articles):
    if i < len(analysis_results):
        analysis = analysis_results[i]
        article["sentiment"] = analysis.get("sentiment", "Unknown")
        article["intensity"] = analysis.get("intensity", "Unknown")
        article["framing_risk"] = analysis.get("framing_risk", "Unknown")
        article["summary"] = analysis.get("summary", "Unavailable")
    else:
        article["sentiment"] = "Unknown"
        article["intensity"] = "Unknown"
        article["framing_risk"] = "Unknown"
        article["summary"] = "Unavailable"

    article["credibility"] = SOURCE_TRUST.get(article["source"], 5)

    # Cross confirmation (needs full list)
    for article in articles:
        confirmation, count = get_cross_confirmation(article, articles)
        article["confirmation"] = confirmation
        article["confirmation_count"] = count

    return render_template(
        "index.html",
        categories=CATEGORIES.keys(),
        current_category=category,
        articles=articles
    
 
    )

if __name__ == "__main__":
    app.run()
