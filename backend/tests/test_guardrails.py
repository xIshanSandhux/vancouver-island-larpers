from workflows.guardrails import check_variant

INPUT = "I got a coffee and went to a meeting."


def test_clean_variant_passes():
    post = "I got a coffee.\n\nThen I went to a meeting.\n\nSmall things compound."
    assert check_variant(INPUT, post) == []


def test_invented_numbers_are_rejected():
    reasons = check_variant(INPUT, "I closed 40 deals before that meeting.")
    assert any("invented numbers" in r for r in reasons)


def test_numbers_from_the_input_are_allowed():
    assert check_variant("I ran 5 km today.", "I ran 5 km today and felt alive.") == []


def test_list_markers_are_not_treated_as_invented_numbers():
    post = "Three lessons:\n\n1. Show up\n2. Listen\n3. Follow through"
    assert check_variant(INPUT, post) == []


def test_invented_company_names_are_rejected():
    reasons = check_variant(INPUT, "The meeting was at Microsoft, and it changed me.")
    assert any("proper nouns" in r for r in reasons)


def test_sentence_initial_capitals_are_not_flagged():
    post = "Coffee first.\n\nMeetings second.\n\nEverything else is noise."
    assert check_variant(INPUT, post) == []


def test_words_from_the_input_keep_their_capitals():
    assert check_variant("I met Dana for coffee.", "Coffee with Dana taught me something.") == []
