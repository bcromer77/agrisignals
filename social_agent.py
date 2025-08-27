# backend/agents/social_agent.py
import os
import datetime
from pymongo import MongoClient
from openai import OpenAI
import tweepy  # pip install tweepy

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# --- Setup Mongo ---
mongo_client = MongoClient(os.environ["MONGO_URI"])
db = mongo_client[os.environ.get("MONGO_DB", "agrisignals")]

# --- Setup Twitter API ---
auth = tweepy.OAuth1UserHandler(
    os.environ["TWITTER_API_KEY"],
    os.environ["TWITTER_API_SECRET"],
    os.environ["TWITTER_ACCESS_TOKEN"],
    os.environ["TWITTER_ACCESS_SECRET"],
)
twitter_api = tweepy.API(auth)

# backend/agents/social_agent.py
import os
import datetime
from pymongo import MongoClient
from openai import OpenAI
import tweepy  # pip install tweepy

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# --- Setup Mongo ---
mongo_client = MongoClient(os.environ["MONGO_URI"])
db = mongo_client[os.environ.get("MONGO_DB", "agrisignals")]

# --- Setup Twitter API ---
auth = tweepy.OAuth1UserHandler(
    os.environ["TWITTER_API_KEY"],
    os.environ["TWITTER_API_SECRET"],
    os.environ["TWITTER_ACCESS_TOKEN"],
    os.environ["TWITTER_ACCESS_SECRET"],
)
twitter_api = tweepy.API(auth)

# --- Prompt Template ---
SOCIAL_PROMPT = """
You are an intelligence filter that monitors real-time Twitter/X accounts, council transcripts, and water board updates.

Your mission:
- Detect breaking stories, anomalies, or disruptions in agriculture, commodities, labor, or water.
- Focus on themes like: migrant worker shortages (H2A/H2B visas), weather shocks, union strikes, disease outbreaks, tariffs, ICE enforcement, city council water restrictions, municipal bankruptcies, and mega-events (Olympics, World Cup, Vegas tourism).
- Extract the market signal before it becomes mainstream.

For each item you process, return the following fields in JSON:
{
  "headline": "...",
  "so_what": "...",
  "who_bleeds": "...",
  "who_benefits": "...",
  "tradecraft": "..."
}
Be abstract and sharp. Don’t just restate the news — infer the hidden financial and systemic implications.
"""

class SocialAgent:
    def __init__(self, handles=None, limit=50):
        self.handles = handles or []
        self.limit = limit

    def fetch_tweets(self):
        """Pull latest tweets from selected accounts"""
        tweets = []
        for handle in self.handles:
            try:
                user_tweets = twitter_api.user_timeline(
                    screen_name=handle,
                    count=self.limit,
                    tweet_mode="extended"
                )
                for t in user_tweets:
                    tweets.append({
                        "handle": handle,
                        "text": t.full_text,
                        "date": t.created_at,
                        "id": t.id
                    })
            except Exception as e:
                print(f"⚠️ Error fetching {handle}: {e}")
        return tweets

    def analyze_tweet(self, tweet_text):
        """Send tweet to GPT for structured analysis"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SOCIAL_PROMPT},
                {"role": "user", "content": tweet_text}
            ]
        )
        return response.choices[0].message.content

    def run(self):
        print("🐦 SocialAgent is running...")
        tweets = self.fetch_tweets()
        for tw in tweets:
            analysis = self.analyze_tweet(tw["text"])
            try:
                doc = {
                    "tweet": tw,
                    "analysis": analysis,
                    "date": datetime.datetime.utcnow()
                }
                db["social_signals"].insert_one(doc)
                print(f"✅ Inserted social signal from @{tw['handle']}")
            except Exception as e:
                print(f"⚠️ Mongo insert error: {e}")

