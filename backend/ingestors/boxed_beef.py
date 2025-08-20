from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.db.models import BoxedBeef

def seed_mock_boxed_beef(db: Session):
    # Create 10 days mock data with a widening spread into day 7-9
    base_choice = 364.0
    base_select = 341.0
    base_loads = 80
    start = date.today() - timedelta(days=9)
    for i in range(10):
        d = start + timedelta(days=i)
        choice = base_choice + i * 4.0  # rising choice
        select = base_select + i * 2.0  # rising slower
        loads = base_loads + (i % 3) * 10
        db.add(BoxedBeef(date=d, choice=choice, select=select, loads=loads))
    db.commit()
