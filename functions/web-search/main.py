import os
from googleapiclient.discovery import build

def web_search(request):
    """
    Performs a web search using the Google Custom Search API and enriches
    the results with publication date metadata.
    """
    api_key = os.environ.get("API_KEY")
    search_engine_id = os.environ.get("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        return {"error": "API_KEY or SEARCH_ENGINE_ID environment variables not set."}, 500

    request_json = request.get_json(silent=True)
    if not request_json or 'query' not in request_json:
        return {"error": "Missing 'query' in request body."}, 400

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
            # --- START: New logic for date extraction ---
            publication_date = None
            # The API returns metadata in a 'pagemap' object.
            # We safely access it using .get() to avoid errors if keys are missing.
            pagemap = item.get('pagemap', {})
            metatags_list = pagemap.get('metatags', [])
            
            if metatags_list:
                metatags = metatags_list[0]
                # Search for common date-related metatags in a prioritized order.
                publication_date = (
                    metatags.get('article:published_time') or
                    metatags.get('og:updated_time') or
                    metatags.get('publishdate') or
                    metatags.get('date') # A common alternative
                )
            # --- END: New logic for date extraction ---

            search_results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "publication_date": publication_date  # The new, crucial field. Can be None.
            })

        return {"results": search_results}, 200

    except Exception as e:
        # Return a generic error message for security. Log the actual error for debugging.
        print(f"An error occurred: {e}")
        return {"error": "An internal error occurred during the search operation."}, 500
