from image2travel.models import TripBrief, ExperienceFingerprint, PlanTripResult
from image2travel.matching import DestinationMatcher
from image2travel.itinerary import ItineraryBuilder
from image2travel.validate import ItineraryValidator


def test_models():
    fp = ExperienceFingerprint(emotions=["calm"], landscape=["lake"])
    brief = TripBrief(days=3, fingerprint=fp)
    assert brief.days == 3


def test_matching():
    m = DestinationMatcher()
    res = m.match({"emotions": ["calm"]}, {"days": 3})
    assert isinstance(res, list)
    assert len(res) > 0


def test_itinerary():
    b = ItineraryBuilder()
    itin = b.build({"days": 2}, "dest_001")
    assert itin["days"] == 2
    assert len(itin["days_detail"]) == 2


def test_validate():
    v = ItineraryValidator()
    b = ItineraryBuilder()
    itin = b.build({"days": 3}, "dest_001")
    res = v.validate(itin)
    assert res["valid"] is True
