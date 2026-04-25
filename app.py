import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Instagram ──────────────────────────────────────────────────────────────
def check_instagram(username):
    try:
        res = requests.get(
            f"https://www.instagram.com/{username}/",
            headers=HEADERS, timeout=8
        )
        text = res.text
        if "Profile isn't available" in text or "isn't available" in text:
            return "available"
        if res.status_code == 404:
            return "available"
        if res.status_code == 200:
            return "taken"
        return "unknown"
    except Exception:
        return "unknown"

# ── Facebook ───────────────────────────────────────────────────────────────
def check_facebook(username):
    try:
        res = requests.get(
            f"https://www.facebook.com/{username}",
            headers=HEADERS, timeout=8, allow_redirects=True
        )
        text = res.text
        if "This content isn't available at the moment" in text:
            return "available"
        if "isn't available" in text or res.status_code == 404:
            return "available"
        if res.status_code == 200 and "timeline" in text.lower():
            return "taken"
        return "unknown"
    except Exception:
        return "unknown"

# ── X / Twitter ────────────────────────────────────────────────────────────
def check_twitter(username):
    try:
        res = requests.get(
            f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}",
            headers=HEADERS, timeout=8
        )
        if res.status_code == 200:
            return "taken"
        if res.status_code == 404:
            return "available"

        # Fallback: scrape nitter instance
        res2 = requests.get(
            f"https://nitter.privacydev.net/{username}",
            headers=HEADERS, timeout=8
        )
        text = res2.text
        if "this account doesn't exist" in text.lower() or res2.status_code == 404:
            return "available"
        if res2.status_code == 200:
            return "taken"
        return "unknown"
    except Exception:
        return "unknown"

# ── GitHub ─────────────────────────────────────────────────────────────────
def check_github(username):
    try:
        res = requests.get(f"https://api.github.com/users/{username}", timeout=7)
        if res.status_code == 200:
            return "taken"
        if res.status_code == 404:
            return "available"
        return "unknown"
    except Exception:
        return "unknown"

# ── Reddit ─────────────────────────────────────────────────────────────────
def check_reddit(username):
    try:
        res = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers={**HEADERS, "Accept": "application/json"},
            timeout=7
        )
        if res.status_code == 200:
            return "taken"
        if res.status_code == 404:
            return "available"
        return "unknown"
    except Exception:
        return "unknown"

# ── TikTok ─────────────────────────────────────────────────────────────────
def check_tiktok(username):
    try:
        url = f"https://www.tiktok.com/api/user/detail/?uniqueId={username}&aid=1988&app_language=en"
        res = requests.get(url, headers=HEADERS, timeout=8)
        data = res.json()
        status_code = data.get("statusCode", -1)
        if status_code == 0:
            return "taken"
        if status_code == 10202:
            return "available"
        return "unknown"
    except Exception:
        return "unknown"

# ── YouTube ────────────────────────────────────────────────────────────────
def check_youtube(username):
    try:
        res = requests.get(
            f"https://www.youtube.com/@{username}",
            headers=HEADERS, timeout=8
        )
        if res.status_code == 404:
            return "available"
        if res.status_code == 200:
            return "taken"
        return "unknown"
    except Exception:
        return "unknown"


CHECKERS = {
    "github":    check_github,
    "reddit":    check_reddit,
    "twitter":   check_twitter,
    "instagram": check_instagram,
    "tiktok":    check_tiktok,
    "youtube":   check_youtube,
    "facebook":  check_facebook,
    "linkedin":  lambda u: "unknown",
}

@app.route("/check")
def check():
    username = request.args.get("username", "").strip().lower()
    platform = request.args.get("platform", "").strip().lower()
    if not username or not platform:
        return jsonify({"error": "Missing params"}), 400
    if platform not in CHECKERS:
        return jsonify({"error": "Unknown platform"}), 400
    return jsonify({
        "platform": platform,
        "username": username,
        "status": CHECKERS[platform](username)
    })

@app.route("/check-all")
def check_all():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"error": "Missing username"}), 400
    return jsonify({
        "username": username,
        "results": {p: fn(username) for p, fn in CHECKERS.items()}
    })

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Username Checker API"})

if __name__ == "__main__":
    app.run()
