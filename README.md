# pychunkedskiplist
python chunked skiplist as an ordered dict

# Rationale
I need to brush up on Python a little bit so just want something to work on.

After looking for an ordered dict/tree for some other problem I'm a bit appalled by Python's options.  There is no standard library ordered dict, which is reasonable.  But the popular options have shortcomings:

## blist
blist was originally intended as a replacement for list but with better insertion performance by removing the "double on copy" of appends and by allowing faster and more flexible insertion in the middle.  Blist is a c-extension data structure and looks rather complicated.  It's implementation mirrors a B-Tree in that the blist is a multi-level array of arrays tracking indices.  The sorteddict is then a blist of keys and a separate builtin dict.  The keys are maintained in sorted order and all value accesses are looked up in the builtin list.

Perhaps my biggest complaint is that the tools for searching its dict are lacking.  It provides bisect-like calls that take O(log n) to return an index where an item exists or should be inserted.  But with this you must then access the item by index.  To iterate over a range (or simply get the next/previous element) requires accessing by index and iterating over an index range.

Accessing by index, meanwhile, is O(1) "so long as the data structure hasn't been modified recently" and in one point the documentation claims that several index accesses are amorizted O(1).  The supporting discussion and documentation on implementation doesn't, in my opinion, make this clear, or help the user understand what the cost is when modifications are frequent.

## sortedcontainers
sortedcontainers are somewhat similar to blist, except that a sortedlist is at most 2 levels.  This allows the data structure to be simpler and pure python (no C).  However, it makes reasoning about performance a bit trickier, as very large lists with large memories might start to see degraded performance.  The sorteddict again uses a separate builtin dict for values while storing the keys in a sorted list.  The implementation favors lower performance constants over asymptotic complexity, noting that by making these constants as small as possible allows better performance for all reasonable memory sizes.

In terms of semantics the sorteddict allows an irange to get keys within a range (can select inclusive or exclusive and direction) and islice to get a range by indices.  Index lookup is O(log n).

Key lookups are "approximately O(log n)"

## Improvements
There may be some improvement to be had by maintaining the same order of values as in keys, by placing values in another list (or list-like data structure) or by coupling the keys and values together.  This isn't entirely clear, as python dicts are surely quite optimized.  I expect improvements to come particularly when iterating over items or values.

Strict complexity guarantees, still somewhat simple.  I don't want to compromise on complexity, or at least I want it to be easy to reason about how performance degrades with size.

Improved/additional semantics.  The following operations should be intuitive and performant (and that means not performing more than 1 lookup):

- finding a key and value
- iterating over values
- iterating in reverse
- iterating over a range of keys/values/items, including endpoints that span "strictly outside" the provided endpoints (sortedcontainers requires 2 iterators -- one left and one right)

# Implementation
First build a skip list.  The linked list should support O(log n) access by index/position.  The linked list should allow reverse traversal either by providing reverse points or by tracking a "stack per level" cursor.  It must also consider what happens with modifications while iterating.  Reverse leaf pointers don't have any problem, the stack per level cursor would need to be updated on modification and modifications while iterating would have to go through this object itself.  Allowing inserts and updates via some iterator/cursor would allow better performance (don't need to search for an insert position)

Then make the skip list entries (key at start of a range, capped length list of items in range).  Each of these lists resembles the page of a btree and contains the actual items.  Finding a key requires a bisect.  Once the list reaches its limit a new range/skiplist item is created, half of the items are moved to the new skiplist item.  When a list size falls below a threshold it can be merged with the adjacent items.  Access by index must allow examining the length of each page, so the initial skiplist implementation should consider this "access by weight" and accept a function to calculate the weight of an item.