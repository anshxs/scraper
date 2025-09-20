from flask import Flask, request, jsonify
import requests, re
from bs4 import BeautifulSoup
from urllib.parse import quote

app = Flask(__name__)

# ---------------- Images ----------------
def search_images(query, max_results=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.5993.90 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    res = requests.get("https://duckduckgo.com/", params={"q": query}, headers=headers)
    match = re.search(r'vqd="([\d-]+)"', res.text)
    if not match:
        return {"error": "Could not get vqd token"}
    vqd = match.group(1)

    url = "https://duckduckgo.com/i.js"
    params = {"q": query, "vqd": vqd, "f": "", "p": "1", "o": "json", "l": "us-en", "s": "0"}
    image_urls = []

    while len(image_urls) < max_results:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            data = r.json()
        except (ValueError, requests.RequestException):
            break
        for item in data.get("results", []):
            image_urls.append(item["image"])
            if len(image_urls) >= max_results:
                break
        if "next" in data:
            url = "https://duckduckgo.com" + data["next"]
        else:
            break
    return image_urls

@app.route("/images", methods=["GET"])
def images_api():
    query = request.args.get("q")
    max_results = int(request.args.get("max", 10))
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    images = search_images(query, max_results)
    return jsonify({"query": query, "results": images})


# ---------------- Videos ----------------
def search_videos(query, max_results=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.5993.90 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    res = requests.get("https://duckduckgo.com/", params={"q": query}, headers=headers)
    match = re.search(r'vqd="([\d-]+)"', res.text)
    if not match:
        return {"error": "Could not get vqd token"}
    vqd = match.group(1)

    url = "https://duckduckgo.com/v.js"
    params = {"q": query, "vqd": vqd, "o": "json", "l": "us-en", "p": "1", "s": "0"}
    video_urls = []

    while len(video_urls) < max_results:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            data = r.json()
        except (ValueError, requests.RequestException):
            break
        for item in data.get("results", []):
            if "video" in item:
                video_urls.append(item["video"])
            if len(video_urls) >= max_results:
                break
        if "next" in data:
            url = "https://duckduckgo.com" + data["next"]
        else:
            break
    return video_urls

@app.route("/videos", methods=["GET"])
def videos_api():
    query = request.args.get("q")
    max_results = int(request.args.get("max", 10))
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    videos = search_videos(query, max_results)
    return jsonify({"query": query, "results": videos})


# ---------------- Web Search ----------------
def normalize_url(url):
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return "https://" + url.lstrip("/")

def fetch_duckduckgo(query, num=10):
    url = f"https://duckduckgo.com/html/?q={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    
    for ddg in soup.select(".result"):
        title_el = ddg.select_one(".result__title a")
        snippet_el = ddg.select_one(".result__snippet")
        display_url_el = ddg.select_one(".result__url")
        
        if title_el:
            raw_url = display_url_el.text.strip() if display_url_el else title_el["href"]
            results.append({
                "title": title_el.text.strip(),
                "url": normalize_url(raw_url),
                "snippet": snippet_el.text.strip() if snippet_el else ""
            })
        if len(results) >= num:
            break
    return results

@app.route("/search", methods=["GET"])
def search_api():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing 'q' query parameter"}), 400
    results = fetch_duckduckgo(query)
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
