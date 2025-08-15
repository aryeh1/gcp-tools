import os
from googleapiclient.discovery import build
from flask import jsonify # <-- הוספת ייבוא הכרחי

def web_search(request):
    """
    Performs a web search using the Google Custom Search API and enriches
    the results with publication date metadata.
    """
    api_key = os.environ.get("API_KEY")
    search_engine_id = os.environ.get("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        return jsonify({"error": "API_KEY or SEARCH_ENGINE_ID environment variables not set."}), 500

    request_json = request.get_json(silent=True)
    if not request_json or 'query' not in request_json:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    query = request_json['query']

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(
            q=query,
            cx=search_engine_id,
            num=5  # Fetch 5 results
        ).execute()

        items = res.get('items', [])
        search_results = []
        for item in items:
            pagemap = item.get('pagemap', {})
            metatags_list = pagemap.get('metatags', [])
            publication_date = None

            if metatags_list:
                metatags = metatags_list[0]
                publication_date = (
                    metatags.get('article:published_time') or
                    metatags.get('og:updated_time') or
                    metatags.get('publishdate') or
                    metatags.get('date')
                )

            search_results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "publication_date": publication_date
            })

        final_response = {
            # עדכנתי גרסה כדי שנוכל לוודא שהפריסה החדשה עלתה
            "version": "v1.7000 - json fix",
            "results": search_results
        }
        
        # <-- שימוש ב-jsonify להחזרת תגובת JSON תקנית
        return jsonify(final_response), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        # <-- שימוש ב-jsonify גם עבור הודעות שגיאה
        return jsonify({"error": "An internal error occurred during the search operation."}), 500
