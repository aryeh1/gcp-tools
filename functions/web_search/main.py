import os
import json # <-- ייבוא חדש
from googleapiclient.discovery import build
from flask import Response # <-- שינוי בייבוא

def web_search(request):
    """
    Performs a web search using the Google Custom Search API and enriches
    the results with publication date metadata.
    """
    api_key = os.environ.get("API_KEY")
    search_engine_id = os.environ.get("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        error_response = json.dumps({"error": "API_KEY or SEARCH_ENGINE_ID not set."}, ensure_ascii=False)
        return Response(error_response, status=500, mimetype='application/json; charset=utf-8')

    request_json = request.get_json(silent=True)
    if not request_json or 'query' not in request_json:
        error_response = json.dumps({"error": "Missing 'query' in request body."}, ensure_ascii=False)
        return Response(error_response, status=400, mimetype='application/json; charset=utf-8')

    query = request_json['query']

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(
            q=query,
            cx=search_engine_id,
            num=5
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
            # שנה את הגרסה כדי שנדע שהפריסה עבדה
            "version": "v2.01",
            "results": search_results
        }
        
        # --- השינוי המרכזי ---
        # 1. נמיר ל-JSON עם ensure_ascii=False כדי לשמור על עברית.
        # 2. ניצור אובייקט Response עם הכותרות הנכונות.
        json_payload = json.dumps(final_response, ensure_ascii=False)
        return Response(json_payload, status=200, mimetype='application/json; charset=utf-8')

    except Exception as e:
        print(f"An error occurred: {e}")
        error_response = json.dumps({"error": "An internal error occurred."}, ensure_ascii=False)
        return Response(error_response, status=500, mimetype='application/json; charset=utf-8')
