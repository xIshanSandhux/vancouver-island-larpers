from scripts.consistency import spearman


def test_spearman_identical_and_reversed_rankings():
    assert spearman(["a", "b", "c"], ["a", "b", "c"]) == 1
    assert spearman(["a", "b", "c"], ["c", "b", "a"]) == -1
