from sqlalchemy import func, select

from app.models.price_model import PriceList, PriceListDetail, Service
from app.scripts.seed_sample_data import SAMPLE_PRICE_LISTS, SAMPLE_SERVICES, seed_sample_prices


def test_sample_price_seed_is_idempotent(db):
    seed_sample_prices(db)
    seed_sample_prices(db)

    assert db.scalar(select(func.count()).select_from(Service)) == len(SAMPLE_SERVICES)
    assert db.scalar(select(func.count()).select_from(PriceList)) == len(SAMPLE_PRICE_LISTS)
    assert db.scalar(select(func.count()).select_from(PriceListDetail)) == len(SAMPLE_PRICE_LISTS)
