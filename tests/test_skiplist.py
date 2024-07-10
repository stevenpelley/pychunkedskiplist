import src.skiplist._skiplist as sl

def _create_skiplist(entries: dict[int, int]) -> sl._SkipList:
    s = sl._SkipList()
    for (k, v) in entries.items():
        s[k] = v
    return s


def test_set_item():
    s = _create_skiplist({1: 10})
    s._assert_rep_inv("")
    pass

def test_search():
    assert True