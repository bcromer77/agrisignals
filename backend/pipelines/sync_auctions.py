from sqlalchemy.orm import Session
from backend.ingestors.auction_pdf import seed_mock_auctions
from backend.ingestors.boxed_beef import seed_mock_boxed_beef
from backend.alerts.evaluate import evaluate_choice_select_spread

def run_all(db: Session):
    # In real life, replace seed_* with real fetch/parse functions.
    seed_mock_boxed_beef(db)
    seed_mock_auctions(db)
    evaluate_choice_select_spread(db)
