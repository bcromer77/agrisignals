import os
from firecrawl import Firecrawl

api_key = os.environ.get("FIRECRAWL_API_KEY")
print("🔑 FIRECRAWL_API_KEY loaded:", bool(api_key))

fc = Firecrawl(api_key=api_key)

try:
    res = fc.search(
        "Port of Houston shipping delays",
        limit=3,
        scrape_options={"formats": ["markdown"]}
    )

    # 🔍 Try web results first
    if hasattr(res, "web") and res.web:
        print(f"✅ Got {len(res.web)} web results")
        for i, item in enumerate(res.web, 1):
            print(f"\n[{i}] {getattr(item, 'title', 'No title')}")
            print(getattr(item, 'url', 'No URL'))
            if hasattr(item, "markdown") and item.markdown:
                print(item.markdown[:200], "...")
    elif hasattr(res, "news") and res.news:
        print(f"📰 Got {len(res.news)} news results")
        for i, item in enumerate(res.news, 1):
            print(f"\n[{i}] {getattr(item, 'title', 'No title')}")
            print(getattr(item, 'url', 'No URL'))
    else:
        print("⚠️ No web/news results found")

except Exception as e:
    print("🔥 Error during Firecrawl test:", e)

