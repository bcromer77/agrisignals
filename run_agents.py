from backend.agents.auction_agent import AuctionAgent
from backend.agents.council_agent import CouncilAgent
from backend.agents.infra_agent import InfraAgent
from backend.agents.retail_agent import RetailAgent

def run_all_agents():
    agents = [
        AuctionAgent(),
        CouncilAgent(),
        InfraAgent(),
        RetailAgent(),  # 👈 must be here
    ]

    for agent in agents:
        print(f"🚀 Running {agent.__class__.__name__} ...")
        docs = agent.run()
        if docs:
            print(f"✅ Saved {len(docs)} docs from {agent.__class__.__name__}")
        else:
            print(f"⚠️ No docs returned from {agent.__class__.__name__}")

if __name__ == "__main__":
    run_all_agents()

