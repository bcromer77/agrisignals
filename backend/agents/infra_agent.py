from backend.agents.base import BaseAgent

class InfraAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="InfraAgent")

    def run(self):
        return [
            {
                "url": "https://infrastructure.org/logistics",
                "title": "Rail delays affect corn shipments",
                "raw_text": "Corn shipments in Iowa delayed due to rail maintenance."
            }
        ]

