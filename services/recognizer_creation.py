from services.MelodicContourGenerator import MelodicContourGenerator
from services.SongRecognizer import SongRecognizer
from services.FingerprintGenerator import FingerprintGenerator

_recognizer_instance = None

def get_recognizer():
    global _recognizer_instance
    if _recognizer_instance is None:
        fingerprint_generator = FingerprintGenerator()
        melodic_contour_generator = MelodicContourGenerator()
        _recognizer_instance = SongRecognizer(fingerprint_generator, melodic_contour_generator)
    return _recognizer_instance
