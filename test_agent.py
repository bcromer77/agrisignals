# test_agent.py
from backend.agents.base import BaseAgent
from backend.services.county_scanner.firecrawl_client import fc_search
from backend.services.county_scanner.storage import save_vectors

class TestAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TestAgent", queries=["Colorado cattle auction drought"])

    def run(self):
        docs = []
        for q in self.queries():
            try:
                res = fc_search(q, limit=3, formats=["markdown"])
                for item in res.get("data", []):
                    docs.append({
                        "url": item.get("url"),
                        "title": item.get("title"),
                        "raw_text": item.get("markdown") or "",
                    })
            except Exception as e:
                print(f"❌ Error searching {q}:", e)
        return docs

if __name__ == "__main__":
    agent = TestAgent()
    docs = agent.run()
    if not docs:
        print("⚠️ No docs found")
    else:
        print(f"📥 {agent.name} ingested {len(docs)} docs")
        save_vectors(docs, backend="mongo")

