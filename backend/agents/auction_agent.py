from backend.agents.base import BaseAgent

class AuctionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AuctionAgent")

    def run(self):
        # Later: replace this with Firecrawl + parsing auction results
        return [
            {
                "url": "https://usda.gov/auctions/cattle",
                "title": "Oklahoma cattle auction prices dip",
                "raw_text": "Cattle auction in Oklahoma showed a 10% drop due to drought."
            }
        ]

