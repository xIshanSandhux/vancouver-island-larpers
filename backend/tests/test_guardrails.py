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


class TestFalsePositivesFoundInRealRuns:
    """A real run rejected 6 of 20 variants for 'invented proper nouns'.

    Every one was a false positive: capitals inside hashtags, and capitals that open
    a bullet or follow a colon. Each rejection costs a retry and can drop the variant.
    """

    def test_hashtags_are_decoration_not_invented_employers(self):
        post = "Coffee first, meeting second.\n\n#Grind #Hustle #StartupLife #Blessed"
        assert check_variant(INPUT, post) == []

    def test_a_capital_opening_a_bullet_is_not_a_name(self):
        post = "Three rules:\n\n- Show up early\n- Bring the coffee\n- Follow through"
        assert check_variant(INPUT, post) == []

    def test_a_capital_opening_a_numbered_item_is_not_a_name(self):
        post = "What I learned:\n\n1. Caffeine helps\n2. Meetings end\n3. Patience wins"
        assert check_variant(INPUT, post) == []

    def test_a_capital_after_a_colon_is_not_a_name(self):
        assert check_variant(INPUT, "My rule is simple: Always bring the coffee.") == []

    def test_a_capital_opening_a_quote_is_not_a_name(self):
        assert check_variant(INPUT, 'Someone said "Coffee is the agenda" and I agreed.') == []

    def test_real_violations_still_fail(self):
        """The loosened rules must not blind the check to actual invented facts."""
        assert check_variant(INPUT, "I joined Microsoft after that meeting.")
        assert check_variant(INPUT, "I had coffee with Satya and everything changed.")
        assert check_variant(INPUT, "That meeting generated 40 new leads.")

    def test_a_hashtag_does_not_hide_a_violation_next_to_it(self):
        """Blanking hashtags must not shift offsets and mask the word after them."""
        assert check_variant(INPUT, "Coffee time #Hustle then I joined Microsoft.")
