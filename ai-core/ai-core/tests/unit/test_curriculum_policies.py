import pytest
from core_engine.curriculum.policies import assert_jss_level_allowed, assert_term_allowed, CurriculumPolicyError

def test_jss_allowed():
    for lvl in ["JSS1","JSS2","JSS3"]:
        assert_jss_level_allowed(lvl)

def test_jss_reject():
    with pytest.raises(CurriculumPolicyError):
        assert_jss_level_allowed("SS1")

def test_term_allowed():
    for t in [1,2,3]:
        assert_term_allowed(t)

def test_term_reject():
    with pytest.raises(CurriculumPolicyError):
        assert_term_allowed(4)
