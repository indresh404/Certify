from app.core.generator import get_unique_filename, sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("Alice") == "Alice"
    assert sanitize_filename("Bob / Smith") == "Bob_Smith"
    assert sanitize_filename('Charlie:*?"<>|') == "Charlie"
    assert sanitize_filename("  Dave.  ") == "Dave"
    assert sanitize_filename("Eve___Test") == "Eve_Test"
    assert sanitize_filename("...Frank...") == "Frank"


def test_get_unique_filename(tmp_path):
    gen_set = set()
    f1 = get_unique_filename("Alice", tmp_path, gen_set)
    assert f1.name == "Alice.png"
    assert "alice.png" in gen_set

    # Simulate file exists on disk
    f1.touch()

    f2 = get_unique_filename("Alice", tmp_path, gen_set)
    assert f2.name == "Alice_2.png"
    assert "alice_2.png" in gen_set

    # Test empty after sanitize
    f3 = get_unique_filename("???", tmp_path, gen_set)
    assert f3.name == "Certificate.png"
