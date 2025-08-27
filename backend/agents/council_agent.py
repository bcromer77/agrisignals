from backend.agents.base import BaseAgent

class CouncilAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CouncilAgent")

    def run(self):
        return [
            {
                "url": "https://citycouncil.gov/meeting",
                "title": "Water restrictions approved",
                "raw_text": "The council voted to restrict irrigation in Kern County."
            }
        ]

