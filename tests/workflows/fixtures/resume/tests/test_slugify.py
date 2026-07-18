"""RED tests written in the prior session — src.slugify does not exist yet."""

from src.slugify import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_collapses_separators():
    assert slugify("a  --  b__c") == "a-b-c"


def test_strips_edges():
    assert slugify("--Hello!!") == "hello"


def test_empty():
    assert slugify("") == ""
