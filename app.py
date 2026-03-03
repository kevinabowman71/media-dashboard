###############################################
# Media Intelligent Dashboard                 #
# A dashboard formatted news program that     #
# searches the most credible news sources     #
# and analyzes the content and rates them     #
# according to Sentiment, Intensity,          #
# Credibility, Cross-Confirmation and Framing #
# Risk using intelligent scoring. Gives the   #
# user the info to determine if the news      #
# article is credible.                        #
# Written by Kevin Bowman - Python 3          #
# Origin date - 9-6-25 Update 3-2-26          #
###############################################


import os

import feedparser
from flask import Flask, render_template, request


app = Flask(__name__)

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
        # "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "Associated Press": "https://apnews.com/rss/apf-worldnews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "NPR": "https://feeds.npr.org/1004/rss.xml",
        "CBS News": "https://www.cbsnews.com/latest/rss/world",
        "ABC News": "https://abcnews.go.com/abcnews/internationalheadlines"
},
   
    "Politics": {
    "Reuters": "http://feeds.reuters.com/Reuters/politicsNews",
    # "BBC": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "NPR": "https://feeds.npr.org/1014/rss.xml",
    "Politico": "https://www.politico.com/rss/politics08.xml",
    "The Hill": "https://thehill.com/rss/syndicator/19109",
    "Associated Press": "https://apnews.com/rss/apf-politics",
    
    "The Guardian": "https://www.theguardian.com/us-news/us-politics/rss"
},
    "Business": {
        "Reuters": "http://feeds.reuters.com/reuters/businessNews",
        # "BBC": "http://feeds.bbci.co.uk/news/business/rss.xml"
    },
    "Technology": {
        "Reuters": "http://feeds.reuters.com/reuters/technologyNews",
        # "BBC": "http://feeds.bbci.co.uk/news/technology/rss.xml"
        "Techradar": "https://www.techradar.com/feeds.xml",
        "TechCrunch": "https://techcrunch.com/feed/"
    },
    "Entertainment": {
        "The Hollywood Reporter": "https://hollywoodreporter.com/c/news/feed/",
        "Variety": "https://variety.com/feed/",
        "Buzzeed": "https://www.buzzfeed.com/rss",
        "Pop Culture Junkie": "https://ejunkieblog.com/category/pop-culture/feed/"
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
    "Fox News": 3,
    "Al Jazeera": 7,
    "CBS News": 8,
    "ABC News": 8,
    "TechRadar": 9,
    "TechCrunch": 8,
    "The Hollywood Reporter": 7,
    "Variety": 9,
    "BuzzFeed": 8,
    "Pop Culture Junkie": 9
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
        
import re

POSITIVE_WORDS = {
    "win", "growth", "success", "improve", "benefit", "positive",
    "peace", "progress", "record", "strong", "gain", "support"
}

NEGATIVE_WORDS = {
    "crisis", "war", "attack", "collapse", "fail", "loss",
    "threat", "violence", "death", "chaos", "disaster",
    "corruption", "investigation", "crime"
}

HIGH_INTENSITY_WORDS = {
    "shocking", "explosive", "outrage", "bombshell",
    "devastating", "massive", "fury", "panic", "slam",
    "blasts", "destroys"
}

SENSATIONAL_PATTERNS = [
    r"\bshocking\b",
    r"\bexplosive\b",
    r"\bmassive\b",
    r"\bfury\b",
    r"\bdevastating\b",
    r"\bblasts?\b",
]

def analyze_headline_local(title):
    words = set(re.findall(r"\b\w+\b", title.lower()))

    positive_score = len(words & POSITIVE_WORDS)
    negative_score = len(words & NEGATIVE_WORDS)
    intensity_score = len(words & HIGH_INTENSITY_WORDS)

    if negative_score > positive_score:
        sentiment = "Negative"
    elif positive_score > negative_score:
        sentiment = "Positive"
    else:
        sentiment = "Neutral"

    if intensity_score >= 2:
        intensity = "High"
    elif intensity_score == 1:
        intensity = "Moderate"
    else:
        intensity = "Low"

    framing_hits = sum(bool(re.search(pattern, title.lower()))
                       for pattern in SENSATIONAL_PATTERNS)

    if framing_hits >= 2:
        framing_risk = "High"
    elif framing_hits == 1:
        framing_risk = "Moderate"
    else:
        framing_risk = "Low"

    return {
        "sentiment": sentiment,
        "intensity": intensity,
        "framing_risk": framing_risk,
        "summary": title
    }
# @cache.cached(timeout=900)  # 15 minutes         
@app.route("/")
def index():
    
    category = request.args.get("category", "World")
    articles = get_headlines(category)

    for article in articles:

        analysis = analyze_headline_local(article["title"])


    
    
        article["sentiment"] = analysis["sentiment"]
        article["intensity"] = analysis["intensity"]
        article["framing_risk"] = analysis["framing_risk"]
        article["summary"] = analysis["summary"]


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
