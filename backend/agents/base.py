import os
from firecrawl import Firecrawl

class BaseAgent:
    def __init__(self, name: str, queries: list[str] = None):
        """
        Base class for all agents.
        - name: str, agent name
        - queries: list[str], search queries the agent should run
        """
        self.name = name
        self._queries = queries or []
        self.fc = Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY"))

    def queries(self) -> list[str]:
        """Return the queries this agent should run. Override if needed."""
        return self._queries

    def run(self):
        """Each agent must implement its own run() method."""
        raise NotImplementedError

