from app.services.affiliations.normalizer import normalize,resolve_affiliation

def test_german_exclusion():
    r=resolve_affiliation("Technical University of Munich, Munich, Germany")
    assert r.is_german and r.country_code=="DE"

def test_foreign_detection():
    r=resolve_affiliation("University of Oxford, Oxford, United Kingdom")
    assert not r.is_german and r.country_code=="GB" and not r.needs_review

def test_unknown_goes_to_review():
    assert resolve_affiliation("Advanced Research Centre, Innovation District").needs_review

def test_alias_normalization():
    assert normalize("  Univ. Oxford ")==normalize("University Oxford")

def test_utn_not_partner():
    assert resolve_affiliation("UTN, Nuremberg, Germany",name="UTN").is_utn
