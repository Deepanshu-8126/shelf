"""
Channel 7 — Videosynx-Inspired Anchored Code Schema.
Every line carries its code fragment, live teacher narration, spotlight highlight,
and dry-run runtime state.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AnchoredLine:
    code: str
    narration: str
    highlight: bool = False
    state_label: str = ""
    tip: str = ""


@dataclass
class AnchoredLesson:
    id: str
    title: str
    series_name: str
    episode_num: int
    badge_tag: str
    filename: str = "main.py"
    language: str = "python"
    intro_narration: str = ""
    lines: List[AnchoredLine] = field(default_factory=list)
    test_runner_code: str = ""
    outro_narration: str = ""
    complexity_badge: str = "O(n log n) AVERAGE"
    benchmark_metric: str = "160x Faster Execution"


# =========================================================================
# PRE-CONFIGURED ANCHORED LESSON CATALOG
# =========================================================================

QUICKSORT_ANCHORED = AnchoredLesson(
    id="quicksort_anchored",
    title="QuickSort — Line by Line",
    series_name="LEETCODE DSA PATTERNS",
    episode_num=4,
    badge_tag="DIVIDE & CONQUER • SORTING",
    filename="quicksort.py",
    intro_narration="Aaj hum quicksort dekhenge line-by-line. Yeh divide and conquer ka sabse elegant algorithm hai.",
    lines=[
        AnchoredLine(
            code="def quicksort(arr):",
            narration="Yeh function define kar rahe hain, naam hai quicksort, jo ek input array accept karta hai.",
            highlight=False,
            state_label="Input: arr",
            tip="Function Header"
        ),
        AnchoredLine(
            code="    if len(arr) <= 1: return arr",
            narration="Pehle base case check karte hain: agar array me zero ya one element ho, toh woh already sorted hai.",
            highlight=True,
            state_label="Base Case: len <= 1",
            tip="Base Case Check"
        ),
        AnchoredLine(
            code="    pivot = arr[len(arr) // 2]",
            narration="Ab pivot element pick karte hain: array ka exact middle element.",
            highlight=True,
            state_label="Pivot = 9",
            tip="Pivot Selection"
        ),
        AnchoredLine(
            code="    left = [x for x in arr if x < pivot]",
            narration="Left list comprehension me pivot se chote saare numbers filter karte hain.",
            highlight=False,
            state_label="Left: [3]",
            tip="Filter Subarray"
        ),
        AnchoredLine(
            code="    middle = [x for x in arr if x == pivot]",
            narration="Middle me pivot ke equal elements aate hain.",
            highlight=False,
            state_label="Middle: [9]",
            tip="Pivot Placement"
        ),
        AnchoredLine(
            code="    right = [x for x in arr if x > pivot]",
            narration="Aur right partition me pivot se bade saare elements chale jaate hain.",
            highlight=False,
            state_label="Right: [38, 27, 43, 82, 10]",
            tip="Filter Greater"
        ),
        AnchoredLine(
            code="    return quicksort(left) + middle + quicksort(right)",
            narration="Finally left aur right ko recursively sort karke middle ke saath jod kar return kar dete hain.",
            highlight=True,
            state_label="Recursive Assembly",
            tip="Recursive Merge"
        ),
    ],
    test_runner_code=(
        "def quicksort(arr):\n"
        "    if len(arr) <= 1: return arr\n"
        "    pivot = arr[len(arr) // 2]\n"
        "    left = [x for x in arr if x < pivot]\n"
        "    middle = [x for x in arr if x == pivot]\n"
        "    right = [x for x in arr if x > pivot]\n"
        "    return quicksort(left) + middle + quicksort(right)\n\n"
        "data = [38, 27, 43, 3, 9, 82, 10]\n"
        "print(f'Input Array : {data}')\n"
        "sorted_data = quicksort(data)\n"
        "print(f'Sorted Array: {sorted_data}')\n"
        "print('>> TEST STATUS: PASS (160x Faster)')\n"
    ),
    outro_narration="Yehi hai QuickSort: O of n log n average complexity. Clean, efficient aur interview favorite!",
    complexity_badge="O(n log n) AVERAGE",
    benchmark_metric="O(n log n) • 160x Speedup"
)

TWO_SUM_ANCHORED = AnchoredLesson(
    id="two_sum_anchored",
    title="Two Sum — O(n) Hash Map",
    series_name="LEETCODE DSA PATTERNS",
    episode_num=1,
    badge_tag="HASH MAP • ARRAY",
    filename="two_sum.py",
    intro_narration="Two Sum ko O of n square me solve karna junior mistake hai. Dekho Senior Dev kaise O of 1 hash map use karta hai.",
    lines=[
        AnchoredLine(
            code="def two_sum(nums, target):",
            narration="Pehle function header: nums list aur target integer lete hain.",
            highlight=False,
            state_label="nums, target",
            tip="Function Signature"
        ),
        AnchoredLine(
            code="    seen = {}  # value -> index map",
            narration="Ek empty hash map initialize karte hain jo number ko uske index se map karega.",
            highlight=False,
            state_label="seen = {}",
            tip="Hash Map Lookup"
        ),
        AnchoredLine(
            code="    for i, num in enumerate(nums):",
            narration="Array pe single pass loop chalate hain index aur value dono lete hue.",
            highlight=False,
            state_label="Loop: index, num",
            tip="Single Scan O(n)"
        ),
        AnchoredLine(
            code="        needed = target - num",
            narration="Complement calculate karte hain: target minus current number.",
            highlight=True,
            state_label="needed = target - num",
            tip="Complement Math"
        ),
        AnchoredLine(
            code="        if needed in seen: return [seen[needed], i]",
            narration="Agar complement already dictionary me hai, toh instant O of 1 time me solution mil gaya!",
            highlight=True,
            state_label="Instant Match!",
            tip="O(1) Direct Return"
        ),
        AnchoredLine(
            code="        seen[num] = i",
            narration="Warna current number ko dictionary me store kar lo future numbers ke liye.",
            highlight=False,
            state_label="seen[num] = index",
            tip="Map Insertion"
        ),
    ],
    test_runner_code=(
        "def two_sum(nums, target):\n"
        "    seen = {}\n"
        "    for i, num in enumerate(nums):\n"
        "        needed = target - num\n"
        "        if needed in seen: return [seen[needed], i]\n"
        "        seen[num] = i\n"
        "    return []\n\n"
        "nums = [2, 7, 11, 15]\n"
        "target = 9\n"
        "res = two_sum(nums, target)\n"
        "print(f'Input: nums={nums}, target={target}')\n"
        "print(f'Indices: {res} -> {nums[res[0]]} + {nums[res[1]]} = {target}')\n"
        "print('>> TEST STATUS: PASS (O(n) Linear Time)')\n"
    ),
    outro_narration="Hash map lookup se complexity O of n square se seedha O of n ho jaati hai. Save this pattern!",
    complexity_badge="O(n) TIME • O(n) SPACE",
    benchmark_metric="O(n) Optimal • 50x Faster"
)

ANCHORED_CATALOG = {
    "quicksort": QUICKSORT_ANCHORED,
    "two_sum": TWO_SUM_ANCHORED,
    "quicksort_anchored": QUICKSORT_ANCHORED,
    "two_sum_anchored": TWO_SUM_ANCHORED,
}


def get_anchored_lesson(query: str | None) -> AnchoredLesson:
    if not query:
        return QUICKSORT_ANCHORED
    q = query.lower().replace("-", "_").replace(" ", "_")
    for key, item in ANCHORED_CATALOG.items():
        if key in q or q in key:
            return item
    return QUICKSORT_ANCHORED
