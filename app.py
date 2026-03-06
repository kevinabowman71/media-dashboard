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

import re

from collections import defaultdict

    # STOP = {"the","and","for","with","from","that","this","into","about","after"}
STOP = {
    "the","and","for","with","from","that","this",
    "into","about","after","over","under","between",
    "their","there","would","could","should","morning",
    "live","update","editorial","scoreboard","news"
}
        
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

BALANCED_SOURCES = {

# LEFT
"Mother Jones": "https://www.motherjones.com/feed",
"The Nation": "https://www.thenation.com/rss/articles",
"Jacobin": "https://jacobin.com/feed",
"Truthout": "https://truthout.org/feed",
"Common Dreams": "https://www.commondreams.org/rss",
"Democracy Now": "https://www.democracynow.org/democracynow.rss",
"The Intercept": "https://theintercept.com/feed",
"Daily Kos": "https://www.dailykos.com/rss.xml",
"Vox": "https://www.vox.com/rss/index.xml",

# CENTER
"Reuters": "https://www.reutersagency.com/feed/?best-topics=top-news",
"Associated Press": "https://feeds.apnews.com/ap/topnews",
"NPR": "https://feeds.npr.org/1001/rss.xml",
"BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
"Politico": "https://www.politico.com/rss/politics08.xml",
"PBS": "https://www.pbs.org/newshour/feeds/rss/all",
"ABC News": "https://feeds.abcnews.com/abcnews/topstories",
"CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",

# RIGHT
"Fox News": "http://feeds.foxnews.com/foxnews/latest",
"National Review": "https://www.nationalreview.com/feed",
"Washington Examiner": "https://www.washingtonexaminer.com/feed",
"The Federalist": "https://thefederalist.com/feed",
"Daily Caller": "https://dailycaller.com/section/politics/feed",
"Breitbart": "https://www.breitbart.com/feed",
"The American Conservative": "https://www.theamericanconservative.com/feed"

}        

CATEGORIES = {
    "World": {
        "Reuters": "https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US%3Aen",
        # "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "Associated Press": "https://apnews.com/index.rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "NPR": "https://feeds.npr.org/1004/rss.xml",
        "CBS News": "https://www.cbsnews.com/latest/rss/world",
        "ABC News": "https://abcnews.go.com/abcnews/internationalheadlines",
        "Honolulu Star-Advertiser": "http://staradvertiser.com/feed",
        "Fox News": "https://moxie.foxnews.com/google-publisher/latest.xml"
},
   
    "Politics": {
    "Reuters": "https://rss.app/feeds/xbg6yCCO4BUjNsEJ.xml",
    # "BBC": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "NPR": "https://feeds.npr.org/1014/rss.xml",
    "Politico": "https://www.politico.com/rss/politics08.xml",
    "The Hill": "https://thehill.com/rss/syndicator/19109",
    "Associated Press": "https://apnews.com/rss/apf-politics",
    "Democracy Now": "https://www.democracynow.org/democracynow.rss",
    "The Guardian": "https://www.theguardian.com/us-news/us-politics/rss"
},
    "Business": {
        "Reuters": "https://rss.app/feeds/6Vzt4fsbzIdkqN43.xml",
        # "BBC": "http://feeds.bbci.co.uk/news/business/rss.xml"
    },
    "Technology": {
        "Reuters": "https://rss.app/feeds/uLBJJc3MXuWpNaGu.xml",
        # "BBC": "http://feeds.bbci.co.uk/news/technology/rss.xml"
        "Techradar": "https://www.techradar.com/feeds.xml",
        "TechCrunch": "https://techcrunch.com/feed/"
    },
    "Entertainment": {
        "The Hollywood Reporter": "https://hollywoodreporter.com/c/news/feed/",
        "Variety": "https://variety.com/feed/",
        "Buzzeed": "https://www.buzzfeed.com/rss",
        "Pop Culture Junkie": "https://ejunkieblog.com/category/pop-culture/feed/"
    },
    "Local News": {
        "Sacramento News & Review": "https://sacramento.newsreview.com/feed/",
        "Sacramento Observer": "https://www.sacobserver.com/feed/",
        "Inside Sacramento": "https://insidesacramento.com/feed/",
        "KCRA": "https://www.kcra.com/topstories-rss",
        "Midweek": "https://www.midweek.com/category/hawaii-community-news/windward/windward-oahu-news/feed/",
        "KHON2": "https://www.khon2.com/feed",
        "KITV": "https://www.kitv.com/news.rss",
        "Hawaii News Now": "https://www.hawaiinewsnow.com/rss/"
},
     "Narrative Monitor": BALANCED_SOURCES
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
    "Pop Culture Junkie": 9,
    "Honolulu Star-Advertiser": 9,
    "Sacramento News & Review": 9,
    "Sacramento Observer": 8,
    "Inside Sacramento": 8,
    "KCRA": 7,
    "Midweek": 9,
    "KHON2": 8,
    "KITV": 8,
    "Hawaii News Now": 9,
    "Democracy Now": 10
}
SOURCE_BIAS = {
    "Reuters": "center",
    "Associated Press": "center",
    "NPR": "center",
    "CBS News": "center",
    "ABC News": "center",
    "The Guardian": "left",
    "Democracy Now": "left",
    "Politico": "center",
    "The Hill": "center",
    "Fox News": "right",
    "Al Jazeera": "center"
}
SOURCE_BIAS.update({

# LEFT
"Mother Jones": "left",
"The Nation": "left",
"Jacobin": "left",
"Truthout": "left",
"Common Dreams": "left",
"The Intercept": "left",
"Daily Kos": "left",
"Vox": "left",

# CENTER
"BBC": "center",
"PBS": "center",
"CNN": "center",

# RIGHT
"National Review": "right",
"Washington Examiner": "right",
"The Federalist": "right",
"Daily Caller": "right",
"Breitbart": "right",
"The American Conservative": "right"
})
NARRATIVE_ALLOWED = {
    "Reuters",
    "Associated Press",
    "NPR",
    "BBC",
    "Politico",
    "PBS",
    "ABC News",
    "CNN",
    "Fox News",
    "National Review",
    "Washington Examiner",
    "The Federalist",
    "Daily Caller",
    "Breitbart",
    "The American Conservative",
    "Mother Jones",
    "The Nation",
    "Jacobin",
    "Truthout",
    "Common Dreams",
    "The Intercept",
    "Daily Kos",
    "Vox",
    "Democracy Now"
}
def get_headlines(category):
    articles = []
    feeds = CATEGORIES.get(category, {})

    for source, url in feeds.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:30]:

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                import datetime
                published = datetime.datetime(*entry.published_parsed[:6])

            articles.append({
                "title": entry.title,
                "link": entry.link,
                "source": source,
                "bias": SOURCE_BIAS.get(source, "center"),
                "published": published
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
    "blasts", "destroys", "Predators"
}

SENSATIONAL_PATTERNS = [
    r"\bshocking\b",
    r"\bexplosive\b",
    r"\bmassive\b",
    r"\bfury\b",
    r"\bdevastating\b",
    r"\bblasts?\b",
    r"\bcontroversial\b",
    r"\bFox News\b",
    r"\bdead\b"
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
    
# def extract_keywords(title):
#    words = re.findall(r"[a-zA-Z]{4,}", title.lower())
#    return [w for w in words if w not in STOP]
def extract_keywords(title):

    words = re.findall(r"[a-zA-Z]{3,}", title.lower())

    words = [w for w in words if w not in STOP]

    if not words:
        words = re.findall(r"[a-zA-Z]{3,}", title.lower())

    return words

def normalize_title(title):

    title = title.lower()

    title = re.sub(r"exclusive:", "", title)
    title = re.sub(r"breaking:", "", title)
    title = re.sub(r"[^\w\s]", "", title)

    return title
    
def cluster_articles(articles):

    clusters = []

    for article in articles:

        placed = False
        title = normalize_title(article["title"])

        for cluster in clusters:

            for existing in cluster:

                if similarity(title, normalize_title(existing["title"])) > 0.35:
                    cluster.append(article)
                    placed = True
                    break

            if placed:
                break

        if not placed:
            clusters.append([article])

    return clusters

    timeline = {}

    for a in cluster:
        bias = a["bias"]
        t = a["published"]

        if not t:
            continue

        if bias not in timeline or t < timeline[bias]:
            timeline[bias] = t

    return timeline
def narrative_timeline(cluster):

    timeline = {}

    for article in cluster:

        bias = article.get("bias")
        time = article.get("published")

        if not bias or not time:
            continue

        if bias not in timeline or time < timeline[bias]:
            timeline[bias] = time

    return timeline

def detect_narratives(articles):

    clusters = cluster_articles(articles)

    # print("CLUSTERS FOUND:", len(clusters))

    narratives = []

    for cluster in clusters:

        topic = cluster[0]["title"][:40]   # short label

        #print("Topic:", topic, "Articles:", len(cluster))

        if len(cluster) < 2:
            continue

        timeline = narrative_timeline(cluster)

        if len(timeline) < 2:
            continue

        times = list(timeline.values())
        earliest = min(times)
   
        bars = {}

        for bias, t in timeline.items():
            minutes = int((t - earliest).total_seconds() / 60)
            bars[bias] = minutes

        narratives.append({
            "topic": cluster[0]["title"],
            "timeline": timeline,
            "bars": bars
})

    return narratives
def get_top_narratives(articles):

    clusters = cluster_articles(articles)

    ranked = sorted(clusters, key=lambda c: len(c), reverse=True)

    top = []

    for cluster in ranked[:5]:

        if len(cluster) < 2:
            continue

        top.append({
            "topic": cluster[0]["title"],
            "count": len(cluster)
        })

    return top  
def get_narrative_momentum(articles):

    clusters = cluster_articles(articles)

    momentum = []

    for cluster in clusters:

        if len(cluster) < 3:
            continue

        times = [a.get("published") for a in cluster if a.get("published")]

        if len(times) < 2:
            continue

        earliest = min(times)
        latest = max(times)

        spread_minutes = int((latest - earliest).total_seconds() / 60)

        days = spread_minutes // 1440
        hours = (spread_minutes % 1440) // 60
        minutes = spread_minutes % 60

        spread = f"{days}d {hours}h {minutes}m"

        if spread_minutes <= 0:
            continue

        velocity = len(cluster) / spread_minutes

        momentum.append({
            "topic": cluster[0]["title"],
            "sources": len(cluster),
            "spread": spread,
            "velocity": velocity
        })

    momentum.sort(key=lambda x: x["velocity"], reverse=True)

    return momentum[:5]
    
def get_narrative_polarization(articles):

    clusters = cluster_articles(articles)

    polarization = []

    for cluster in clusters:

        if len(cluster) < 3:
            continue

        counts = {"left":0, "center":0, "right":0}

        for a in cluster:
            bias = a.get("bias")
            if bias in counts:
                counts[bias] += 1

        polarization.append({
            "topic": cluster[0]["title"],
            "left": counts["left"],
            "center": counts["center"],
            "right": counts["right"],
            "total": len(cluster)
        })

    polarization.sort(key=lambda x: x["total"], reverse=True)

    return polarization[:5]
    
def get_narrative_diversity(polarization):

    diversity = []

    for p in polarization:

        total = p["left"] + p["center"] + p["right"]

        if total == 0:
            continue

        proportions = [
            p["left"]/total,
            p["center"]/total,
            p["right"]/total
        ]

        score = 1 - sum(x*x for x in proportions)

        score = round(score, 2)

        # interpret the score
        if score < 0.30:
            label = "Low (Echo Chamber)"
        elif score < 0.50:
            label = "Moderate"
        elif score < 0.70:
            label = "High"
        else:
            label = "Very Balanced"

        diversity.append({
            "topic": p["topic"],
            "score": score,
            "label": label
        })

    return diversity
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

    for article in articles:
        confirmation, count = get_cross_confirmation(article, articles)
        article["confirmation"] = confirmation
        article["confirmation_count"] = count
        
    narratives = detect_narratives(articles)
    top_narratives = get_top_narratives(articles)
    momentum = get_narrative_momentum(articles)
    polarization = get_narrative_polarization(articles)
    diversity = get_narrative_diversity(polarization)
    #print(narratives)
       
    
    return render_template(
    "index.html",
    categories=CATEGORIES.keys(),
    current_category=category,
    articles=articles,
    narratives=narratives,
    top_narratives=top_narratives,
    momentum=momentum,
    polarization=polarization,
    diversity=diversity
)

 
    

if __name__ == "__main__":
    app.run()
