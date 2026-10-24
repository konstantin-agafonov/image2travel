def test_imports():
    from image2travel import __version__
    assert __version__ == "0.1.0"
    
    from image2travel.models import TripBrief, ExperienceFingerprint
    from image2travel.matching import DestinationMatcher
    from image2travel.itinerary import ItineraryBuilder
    from image2travel.validate import ItineraryValidator
