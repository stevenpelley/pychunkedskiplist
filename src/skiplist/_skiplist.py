import itertools
import typing

_SkipListEntry = typing.NewType("_SkipListEntry", None)


class _FillableList[T](list[T]):
    def ensure_size(self, n: int, fill_value=None):
        if len(self) < n:
            self.extend(itertools.repeat(fill_value, times=n-len(self)))


class _SkipListLevelsVector(object):
    """Level references in a skiplist.  Index 0 is the "leaf" level and its
    reference points to the next greater entry.
    This Vector refers to _SkiplistEntries

    The vector must always have size at least 1 as index 0 is the linked list of
    all entries.
    The vector will always have the size corresponding to the level of the
    entry.  If the entry is that last in the skip list at that level then the
    value in this vector for that level will be None.
    """
    _levels: list[_SkipListEntry]

    def __init__(self, level_idx: int) -> None:
        self._levels = [None] * (level_idx + 1)

    def __repr__(self) -> str:
        return repr(self._levels)

    def find_greatest_nongreater_key(
            self,
            k,
            greatest_level_to_search: int) -> typing.Tuple[
            typing.Optional[_SkipListEntry], int]:
        """Return entry and level/index with entry containing the greatest key
        that is no greater than k.  Returns (None, -1) if even level 0 is greater.
        """
        assert greatest_level_to_search >= 0

        # handle index 0 separately since it may refer to None for the last entry
        # this avoids an if in the common case.
        for idx in range(min(len(self._levels) - 1, greatest_level_to_search), 0, -1):
            if self._levels[idx].key <= k:
                return (self._levels[idx], idx)

        # now index 0
        if self._levels[0] is not None and self._levels[idx].key <= k:
            return (self._levels[idx], idx)
        else:
            return (None, -1)

    def get_level(self, level_idx: int) -> typing.Optional[_SkipListEntry]:
        return self._levels[level_idx]

    def update_level(self, level_idx: int, entry: _SkipListEntry) -> None:
        self._levels[level_idx] = entry

    def __len__(self) -> int:
        return len(self._levels)

    def _assert_rep_inv(self, prefix: str) -> None:
        """Assert that the representation invariant of this object holds.
        This is intended to be used in tests.
        """
        prefix = "{}: _SkipListLevelsVector"

        # cannot be empty
        assert len(self._levels) > 0, "{}: _levels is empty".format(prefix)

        # Nones must be grouped at the end.  You cannot have a None at a lower
        # level and then point to something at a higher level.
        greatest_non_none_idx = None
        for idx in range(len(self._levels)-1, -1, -1):
            entry = self._levels[idx]
            assert entry is not None or greatest_non_none_idx is None, (
                    "{}: idx {} is None and have already observed a non-None".format(prefix, idx))
            if entry is not None and greatest_non_none_idx is None:
                greatest_non_none_idx = idx

        # if all pointers are None there is nothing more to check
        if greatest_non_none_idx is None:
            return

        # pointed keys must be descending by from higher level to lower level,
        # or adjacent levels may point to the same entry.
        prev_entry = self._levels[greatest_non_none_idx]
        for idx in range(greatest_non_none_idx-1, -1, -1):
            this_entry = self._levels[idx]
            assert prev_entry == this_entry or prev_entry.key > this_entry.key, (
                    "{}: idx {} has greater key ({}) than 1 greater index ({})".format(
                    idx, this_entry.key, prev_entry.key))
            prev_entry = this_entry

        # an entry pointed to at level N has level >= N
        for idx, entry in enumerate(self._levels[0:greatest_non_none_idx+1]):
            assert len(entry.levels) >= idx + 1, (
                    "{}: entry {} should have level at least {}".format(
                    entry, idx + 1))

        
class _SkipListHeaderLevelsVector(_SkipListLevelsVector):
    """special levels vector that may grow in the number of levels when an
    entry with a new greatest level is added.
    """
    _levels: _FillableList[_SkipListEntry]

    def __init__(self, level_idx: int) -> None:
        self._levels = _FillableList()
        self._levels.ensure_size(level_idx + 1)

    def get_level(self, level_idx: int) -> typing.Optional[_SkipListEntry]:
        if level_idx > len(self._levels) - 1:
            return None
        return self._levels[level_idx]

    def update_level(self, level_idx: int, entry: _SkipListEntry) -> None:
        self._levels.ensure_size(level_idx + 1)
        self._levels[level_idx] = entry


class _SkipListEntry(typing.NamedTuple):
    key: None
    value: None
    levels: _SkipListLevelsVector

    def _assert_rep_inv(
            self,
            expected_next_entry_by_level: list[_SkipListEntry],
            prefix: str) -> None:
        prefix = "{}: _SkipListEntry"
        self.levels._assert_rep_inv(prefix)

        # this entry's key must be less than the keys of all entries in levels
        for idx, pointed_entry in enumerate(self.levels._levels):
            assert pointed_entry is None or self.key < pointed_entry.key, (
                    "{}: key {} is not less than {}'th index key {}".format(
                    prefix, self.key, idx, pointed_entry.key))

        # an entry pointed to at level N with level N' > N must be pointed to at
        # level N' by the closest less entry with level N'
        for idx, pointed_entry in enumerate(self.levels._levels):
            # _levels tells us the level of _this_ entry as well, so for each we
            # point to some other entry must point to us.
            assert expected_next_entry_by_level[idx] == self, (
                    "{}: entry {} is unexpected next entry at level {}. Expected {}".format(
                    prefix, self, idx, expected_next_entry_by_level[idx]))

            # update with this entry's pointed values for subsequent entries
            # note that this may be None, and that by the end we expect all
            # expected next entries to be None.
            expected_next_entry_by_level[idx] = pointed_entry


class _SkipList(object):
    _header: _SkipListHeaderLevelsVector = _SkipListHeaderLevelsVector(0)

    # PUBLIC INTERFACE
    
    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        (existing_entry, traversed_entries) = self._search_to_modify(key)
        if existing_entry is not None:
            existing_entry.value = value
        else:
            level = self._generate_level()
            new_entry = _SkipListEntry(key, value, _SkipListLevelsVector(level))
            self._link_entry(level, new_entry, traversed_entries)

    def __delitem__(self, key):
        pass

    def __missing__(self, key):
        pass

    def __iter__(self):
        pass

    def __reversed__(self):
        pass

    def __contains__(self, item):
        pass

    def __repr__(self) -> str:
        return repr(self._header)

    ###def search(self, key) -> _SkipListCursor:
    ###    """Search for the provided key, returning a cursor pointing just prior
    ###    to the key.  If an entry with the key exists the cursor points to the
    ###    gap before the key.  If no entry with the key exists the cursor points
    ###    between the two closest items with smaller and greater keys.

    ###    The returned cursor iterates in the forward direction (reverse its
    ###    direction after creation if desired).
    ###    """
    ###    levels_stacks = []
    ###    def construct_stacks(entry, level_idx):
    ###        while level_idx > len(levels_stacks) - 1:
    ###            levels_stacks.append([])
    ###        levels_stacks[level_idx].append(entry)

    ###    self._search(key, construct_stacks)
    ###    # construct and return the actual cursor object

    # PRIVATE METHODS
    
    def _search(
            self,
            key,
            fn: typing.Callable[[_SkipListEntry, int], None] = None
            ) -> _SkipListEntry:
        """Search for an entry with the given key.
        the provided fn, when not None, is called for every entry traversed
        along with the level of the _SkipListLevelsVector it was reached.  It is
        not called for an entry with key itself.
        Returns the entry with key equal to k or the closest key less than k, or
        None if all keys are greater than k.
        """
        levels: _SkipListLevelsVector = self._header
        entry = None
        # index of the greatest level in levels list
        greatest_level_to_search_idx = len(levels) - 1

        while True:
            (next_entry, level_idx) = levels.find_greatest_nongreater_key(
                    key, greatest_level_to_search_idx)
            if level_idx < 0:
                return entry # might be None if levels is still _header
            if next_entry.key == key:
                return next_entry

            if fn is not None:
                fn(entry, level_idx)
            entry = next_entry
            greatest_level_to_search_idx = level_idx

    def _search_to_modify(
            self,
            key) -> typing.Tuple[_SkipListEntry, list[_SkipListEntry]]:
        """Search for an entry with the provided key.
        Return (entry, [entries])
        where entry is either the _SkipListEntry with the given key, or None if
        no such key exists;
        and {entries} is the list of entries traversed to reach the
        entry (or location where the entry would be) for the entry of level_idx
        with the greatest key.  Thus, this is the list of entries that will need
        to be modified to point to a new entry at the given key, or that must be
        changed to point around an entry to delete it.
        levels with no traversed entry will be None, and indicate that some
        traversed entry points to keys' entry at multiple levels.
        If the pointing entry is the _header it will be omitted.  When searching
        for the first entry or a key less than the first entry's key an empty
        dict will be returned as the _header points/would point to the entry at
        all levels.
        """
        # level_idx -> entry
        most_recent_traversed_by_level_idx: _FillableList[_SkipListEntry] = _FillableList()
        def traverse(entry, level_idx):
            most_recent_traversed_by_level_idx.ensure_size(level_idx+1)
            most_recent_traversed_by_level_idx[level_idx] = entry
        entry = self._search(key, traverse)
        if entry is None or entry.key != key:
            entry = None
        return (entry, most_recent_traversed_by_level_idx,)

    def _generate_level(self) -> int:
        # TODO
        return 0

    def _link_entry(
            self,
            link_level: int,
            entry: _SkipListEntry,
            traversed_entries: list[_SkipListEntry]) -> None:
        entry_level_vector = entry.levels

        pointing_entries = [None] * len(traversed_entries)
        for idx in range(len(traversed_entries)-1, -1, -1):
            pointing_entries[idx] = (
                    pointing_entries[idx + 1]
                    if traversed_entries[idx] is None
                    else traversed_entries[idx])

        for level in range(link_level + 1):
            prev_vector = (
                self._header
                if level > len(pointing_entries) - 1
                else pointing_entries[level])
            next_entry = prev_vector.get_level(level)

            prev_vector.update_level(level, entry)
            entry_level_vector.update_level(level, next_entry)

    def _assert_rep_inv(self, prefix: str) -> None:
        """Assert that the representation invariant of this object holds.
        This is intended to be used in tests.
        """
        prefix = "{}: _SkipList".format(str)
        self._header._assert_rep_inv(prefix)

        # prime "expected next entry by level" with the header vector
        expected_next_entry_by_level = list(self._header._levels)
        entry = self._header.get_level(0)
        while entry is not None:
            entry._assert_rep_inv(expected_next_entry_by_level, prefix)
            entry = entry.levels.get_level(0)
