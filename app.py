from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import json
from scrapfly_scraper import scrape_single_tweet, save_to_file
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Allow all origins (for debugging) or specify domains explicitly
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")  # Path to Firebase key
firebase_admin.initialize_app(cred)
db = firestore.client()  # Firestore client

# Collection Name
COLLECTION_NAME = "x_posts"

@app.route("/scrape-tweet", methods=["POST"])
def scrape_tweet():
    tweet_url = request.json.get("tweetUrl")
    
    if not tweet_url:
        return jsonify({"error": "No tweet URL provided"}), 400
    
    tweet_data = scrape_single_tweet(tweet_url)
    
    if tweet_data:
        save_to_file(tweet_data)
        return jsonify(tweet_data), 200
    else:
        return jsonify({"error": "Failed to scrape tweet"}), 500

@app.route("/submit-vote", methods=["POST", "OPTIONS"])
def submit_vote():
    if request.method == "OPTIONS":  # Handle CORS preflight
        response = jsonify({"message": "CORS preflight OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        return response, 200

    data = request.json
    tweet_url = data.get("tweetUrl")
    vote = data.get("vote")
    evidence = data.get("evidence", "")

    if not tweet_url or not vote:
        return jsonify({"error": "Missing tweet URL or vote"}), 400

    # Extract tweet_id from URL
    tweet_id = tweet_url.split("/")[-1]

    # Reference Firestore document
    tweet_ref = db.collection(COLLECTION_NAME).document(tweet_id)
    tweet_doc = tweet_ref.get()

    if tweet_doc.exists:
        tweet_data = tweet_doc.to_dict()
    else:
        # Scrape tweet text (only when first time storing)
        tweet_info = scrape_single_tweet(tweet_url)

        if not tweet_info or "tweet_text" not in tweet_info:
            return jsonify({"error": "Failed to scrape tweet"}), 500

        tweet_data = {
            "tweet_id": tweet_id,
            "tweet_link": tweet_url,
            "tweet_text": tweet_info["tweet_text"],  # Store tweet text
            "votes_count": {"Real": 0, "Uncertain": 0, "Fake": 0},
            "total_votes": 0,  # ✅ Initialize total votes
            "evidence_list": {"Real": [], "Uncertain": [], "Fake": []}
        }

    # Update vote count
    if vote in tweet_data["votes_count"]:
        tweet_data["votes_count"][vote] += 1
        tweet_data["total_votes"] += 1  # ✅ Increment total vote count
    else:
        return jsonify({"error": "Invalid vote option"}), 400

    # Store evidence under the correct category
    if evidence:
        if vote in tweet_data["evidence_list"]:
            tweet_data["evidence_list"][vote].append(evidence)

    # Save updated data to Firestore
    tweet_ref.set(tweet_data)

    return jsonify({"status": "success"}), 200

def submit_voteOnly():
     i = "yippe"
     #TODO: WIP for VOTE ONLY submission

@app.route("/get-vote-count", methods=["GET"])
def get_vote_count():
    tweet_url = request.args.get("tweetUrl")

    if not tweet_url:
        return jsonify({"error": "Missing tweet URL"}), 400

    tweet_id = tweet_url.split("/")[-1]  # Extract tweet ID from URL
    tweet_ref = db.collection(COLLECTION_NAME).document(tweet_id)
    tweet_doc = tweet_ref.get()

    if not tweet_doc.exists:
        return jsonify({"total_votes": 0}), 200  # Default to 0 votes if tweet is not found

    tweet_data = tweet_doc.to_dict()
    total_votes = tweet_data.get("total_votes", 0)  # Retrieve or default to 0

    return jsonify({"total_votes": total_votes}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
