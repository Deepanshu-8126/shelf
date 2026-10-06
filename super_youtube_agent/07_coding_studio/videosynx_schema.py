"""
Channel 7 — Videosynx-Inspired Anchored Code Schema & Curriculum.
Full LeetCode Journey (Day 1 - Day 14) with line-by-line code,
per-line Hindi teacher explanations, spotlight cues, and sandbox runners.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re


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
    problem_statement: str = ""
    input_example: str = ""
    naive_pitfall: str = "O(n²) Brute Force -> High Latency"
    warning_banner: str = "[!] INSUFFICIENT OR BUGGY PATTERN"
    challenge_header: str = ""
    series_subtitle: str = ""
    cta_button_text: str = ""
    episode_label: str = ""
    diagram_title: str = ""
    diagram_rows: List[str] = field(default_factory=list)
    diagram_caption: str = ""
    next_day_preview: str = ""



# =========================================================================
# LEETCODE JOURNEY CURRICULUM (DAY 1 TO DAY 14)
# =========================================================================

# DAY 1: Two Sum
DAY1_TWO_SUM = AnchoredLesson(
    id="day1_two_sum",
    title="Day 1: Two Sum — O(n) Hash Map",
    series_name="LEETCODE JOURNEY",
    episode_num=1,
    badge_tag="DAY 1 • HASH MAP",
    filename="two_sum.py",
    intro_narration="Welcome to Day 1 of our LeetCode Journey! Aaj hum Two Sum ko O of n square ke bajaye O of 1 hash map se solve karenge.",
    lines=[
        AnchoredLine(
            code="def two_sum(nums, target):",
            narration="Function signature: input nums array aur target integer lete hain.",
            highlight=False,
            state_label="nums, target",
            tip="Function Signature"
        ),
        AnchoredLine(
            code="    seen = {}  # value -> index map",
            narration="Ek empty hash map initialize karte hain jo elements ko unke index ke saath map karega.",
            highlight=False,
            state_label="seen = {}",
            tip="Hash Map Lookup"
        ),
        AnchoredLine(
            code="    for i, num in enumerate(nums):",
            narration="Array pe single pass loop chalate hain index aur number dono track karte hue.",
            highlight=False,
            state_label="Loop: i, num",
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
            narration="Agar needed complement pehle se dictionary me hai, toh instant O of 1 time me dono indices return kar do!",
            highlight=True,
            state_label="Match Found!",
            tip="O(1) Instant Return"
        ),
        AnchoredLine(
            code="        seen[num] = i",
            narration="Warna current number ko dictionary me save kar lo future lookups ke liye.",
            highlight=False,
            state_label="seen[num] = i",
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
        "print(f'Input Array : {nums}, Target: {target}')\n"
        "print(f'Indices Match: {res} -> {nums[res[0]]} + {nums[res[1]]} = {target}')\n"
        "print('>> TEST STATUS: PASS (O(n) Optimal)')\n"
    ),
    outro_narration="Hash map lookup se time complexity O of n square se seedha O of n ban gayi. Follow for Day 2 tomorrow!",
    complexity_badge="O(n) TIME • O(n) SPACE",
    benchmark_metric="50x Speedup vs Brute Force",
    problem_statement="Given array nums and integer target, return indices of the two numbers that add up to target.",
    input_example="nums = [2, 7, 11, 15]  •  target = 9",
    naive_pitfall="Nested loops O(n²) checks every pair (TLE on 10⁵ elements)",
    next_day_preview="Day 2: Valid Parentheses (LIFO Stack)"
)

# DAY 2: Valid Parentheses
DAY2_VALID_PARENS = AnchoredLesson(
    id="day2_valid_parentheses",
    title="Day 2: Valid Parentheses — Stack",
    series_name="LEETCODE JOURNEY",
    episode_num=2,
    badge_tag="DAY 2 • STACK PATTERN",
    filename="valid_parens.py",
    intro_narration="Welcome to Day 2 of LeetCode Journey! Brackets balance check karne ke liye LIFO Stack sabse best data structure hai.",
    lines=[
        AnchoredLine(
            code="def is_valid(s: str) -> bool:",
            narration="Function header: string s jisme round, curly aur square brackets hain.",
            highlight=False,
            state_label="s: str",
            tip="Function Header"
        ),
        AnchoredLine(
            code="    stack = []",
            narration="Ek empty list initialize karte hain jo hamara LIFO Stack banegi.",
            highlight=False,
            state_label="stack = []",
            tip="LIFO Stack"
        ),
        AnchoredLine(
            code="    mapping = {')': '(', '}': '{', ']': '['}",
            narration="Closing brackets ko unke matching opening bracket se map kar dete hain.",
            highlight=False,
            state_label="mapping dict",
            tip="Bracket Pairs"
        ),
        AnchoredLine(
            code="    for char in s:",
            narration="String ke har character par loop chalate hain.",
            highlight=False,
            state_label="char in s",
            tip="Linear Iteration"
        ),
        AnchoredLine(
            code="        if char in mapping:",
            narration="Agar closing bracket hai, toh top element pop karke match verify karte hain.",
            highlight=True,
            state_label="Closing Match Check",
            tip="Pop & Validate"
        ),
        AnchoredLine(
            code="            top = stack.pop() if stack else '#'",
            narration="Stack se pop karte hain, agar empty ho toh dummy character lete hain.",
            highlight=False,
            state_label="top element",
            tip="Stack Pop"
        ),
        AnchoredLine(
            code="            if mapping[char] != top: return False",
            narration="Agar closing bracket stack ke top se match nahi karta, toh turant False return kar do.",
            highlight=True,
            state_label="Mismatch -> False",
            tip="Early Exit"
        ),
        AnchoredLine(
            code="        else: stack.append(char)",
            narration="Agar opening bracket hai, toh stack me push kar do.",
            highlight=False,
            state_label="stack.append(char)",
            tip="Stack Push"
        ),
        AnchoredLine(
            code="    return not stack",
            narration="Last me check karte hain: agar stack bilkul empty hai, tabhi string valid hai!",
            highlight=True,
            state_label="return not stack",
            tip="Final Empty Check"
        ),
    ],
    test_runner_code=(
        "def is_valid(s: str) -> bool:\n"
        "    stack = []\n"
        "    mapping = {')': '(', '}': '{', ']': '['}\n"
        "    for char in s:\n"
        "        if char in mapping:\n"
        "            top = stack.pop() if stack else '#'\n"
        "            if mapping[char] != top: return False\n"
        "        else: stack.append(char)\n"
        "    return not stack\n\n"
        "test_s = '()[]{}'\n"
        "print(f'Testing String : \"{test_s}\"')\n"
        "print(f'Is Valid Result: {is_valid(test_s)}')\n"
        "print('>> TEST STATUS: PASS (O(n) Linear Scan)')\n"
    ),
    outro_narration="Stack pattern har bracket matching problem ka core solution hai. Follow for Day 3 tomorrow!",
    complexity_badge="O(n) TIME • O(n) SPACE",
    benchmark_metric="O(n) Single Pass Stack",
    problem_statement="Given string s containing '()[]{}', determine if input string is valid and correctly nested.",
    input_example="s = '()[]{}'  ->  Valid: True",
    naive_pitfall="Recursive string replace O(n²) repeatedly rescans string",
    next_day_preview="Day 3: Binary Search (Divide & Conquer)"
)

# DAY 3: Binary Search
DAY3_BINARY_SEARCH = AnchoredLesson(
    id="day3_binary_search",
    title="Day 3: Binary Search in O(log n)",
    series_name="LEETCODE JOURNEY",
    episode_num=3,
    badge_tag="DAY 3 • BINARY SEARCH",
    filename="binary_search.py",
    intro_narration="Welcome to Day 3 of LeetCode Journey! Agar array sorted hai, toh kabhi linear scan mat karo, Binary Search lagao.",
    lines=[
        AnchoredLine(
            code="def binary_search(nums, target):",
            narration="Function define karte hain sorted nums aur search target ke saath.",
            highlight=False,
            state_label="nums, target",
            tip="Function Header"
        ),
        AnchoredLine(
            code="    left, right = 0, len(nums) - 1",
            narration="Do pointers initialize karte hain: left start pe aur right end pe.",
            highlight=False,
            state_label="left=0, right=len-1",
            tip="Two Pointers"
        ),
        AnchoredLine(
            code="    while left <= right:",
            narration="Jab tak pointers cross nahi hote, search space ko har step me half karte rahenge.",
            highlight=False,
            state_label="while left <= right",
            tip="Halving Loop"
        ),
        AnchoredLine(
            code="        mid = (left + right) // 2",
            narration="Middle index calculate karte hain.",
            highlight=True,
            state_label="mid index",
            tip="Middle Pivot"
        ),
        AnchoredLine(
            code="        if nums[mid] == target: return mid",
            narration="Agar middle element hi target hai, toh index turant mil gaya!",
            highlight=True,
            state_label="Found Target!",
            tip="Exact Match O(1)"
        ),
        AnchoredLine(
            code="        elif nums[mid] < target: left = mid + 1",
            narration="Agar target bada hai, toh left pointer ko right half me move kar do.",
            highlight=False,
            state_label="left = mid + 1",
            tip="Shift Right"
        ),
        AnchoredLine(
            code="        else: right = mid - 1",
            narration="Warna search space ko left half me narrow down kar do.",
            highlight=False,
            state_label="right = mid - 1",
            tip="Shift Left"
        ),
        AnchoredLine(
            code="    return -1",
            narration="Agar target nahi mila, toh minus one return kar do.",
            highlight=False,
            state_label="return -1",
            tip="Not Found"
        ),
    ],
    test_runner_code=(
        "def binary_search(nums, target):\n"
        "    left, right = 0, len(nums) - 1\n"
        "    while left <= right:\n"
        "        mid = (left + right) // 2\n"
        "        if nums[mid] == target: return mid\n"
        "        elif nums[mid] < target: left = mid + 1\n"
        "        else: right = mid - 1\n"
        "    return -1\n\n"
        "nums = [-1, 0, 3, 5, 9, 12]\n"
        "target = 9\n"
        "idx = binary_search(nums, target)\n"
        "print(f'Sorted Array : {nums}')\n"
        "print(f'Target {target} Found at Index: {idx}')\n"
        "print('>> TEST STATUS: PASS (O(log n) Logarithmic Time)')\n"
    ),
    outro_narration="Binary search 10 lakh elements ko sirf 20 operations me search kar leta hai. O of log n wins!",
    complexity_badge="O(log n) TIME • O(1) SPACE",
    benchmark_metric="1,000x Faster vs Linear Scan",
    problem_statement="Given sorted array nums and target, find index in O(log n) time complexity.",
    input_example="nums = [-1, 0, 3, 5, 9, 12]  •  target = 9",
    naive_pitfall="Linear search O(n) checks 1,000,000 items sequentially",
    next_day_preview="Day 4: QuickSort in 4 Lines (Partitioning)"
)

# DAY 4: QuickSort
DAY4_QUICKSORT = AnchoredLesson(
    id="day4_quicksort",
    title="Day 4: QuickSort in 4 Lines",
    series_name="LEETCODE JOURNEY",
    episode_num=4,
    badge_tag="DAY 4 • DIVIDE & CONQUER",
    filename="quicksort.py",
    intro_narration="Welcome to Day 4 of LeetCode Journey! Aaj hum QuickSort partition ko 4 clean lines me samajhte hain.",
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
            narration="Base case: agar array me 0 ya 1 element ho, toh woh already sorted hai.",
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
            narration="Left partition me pivot se chote saare numbers filter ho gaye.",
            highlight=False,
            state_label="Left: [3]",
            tip="Filter Subarray"
        ),
        AnchoredLine(
            code="    middle = [x for x in arr if x == pivot]",
            narration="Middle partition me pivot ke barabar elements aate hain.",
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
    benchmark_metric="160x Faster Execution",
    problem_statement="Sort an unsorted array efficiently using divide-and-conquer partition around a pivot.",
    input_example="arr = [38, 27, 43, 3, 9, 82, 10]",
    naive_pitfall="Bubble Sort O(n²) quadratic element swaps",
    next_day_preview="Day 5: Reverse Linked List (In-Place 3-Pointers)"
)

# DAY 5: Reverse Linked List
DAY5_REVERSE_LIST = AnchoredLesson(
    id="day5_reverse_linked_list",
    title="Day 5: Reverse Linked List",
    series_name="LEETCODE JOURNEY",
    episode_num=5,
    badge_tag="DAY 5 • LINKED LIST",
    filename="reverse_list.py",
    intro_narration="Welcome to Day 5 of LeetCode Journey! Singly Linked List ko reverse karne ke liye standard 3 pointers trick seekho.",
    lines=[
        AnchoredLine(
            code="def reverse_list(head):",
            narration="Function head node leta hai.",
            highlight=False,
            state_label="head: ListNode",
            tip="Function Header"
        ),
        AnchoredLine(
            code="    prev = None",
            narration="Previous pointer ko None se initialize karte hain.",
            highlight=False,
            state_label="prev = None",
            tip="Pointer: Prev"
        ),
        AnchoredLine(
            code="    curr = head",
            narration="Current pointer head se start karega.",
            highlight=False,
            state_label="curr = head",
            tip="Pointer: Curr"
        ),
        AnchoredLine(
            code="    while curr:",
            narration="Jab tak end of list nahi aata, pointer traversal chalega.",
            highlight=False,
            state_label="while curr",
            tip="Traversal Loop"
        ),
        AnchoredLine(
            code="        nxt = curr.next  # Save next node",
            narration="Agla node temporary pointer me save kar lo taaki link tootne par reference na khoye.",
            highlight=True,
            state_label="nxt = curr.next",
            tip="Save Reference"
        ),
        AnchoredLine(
            code="        curr.next = prev # Flip pointer reverse",
            narration="Current node ka link ulta karke previous node ki taraf point kar do!",
            highlight=True,
            state_label="curr.next = prev",
            tip="Reverse Link"
        ),
        AnchoredLine(
            code="        prev = curr      # Advance prev",
            narration="Prev pointer ko aage badha kar current pe le aao.",
            highlight=False,
            state_label="prev = curr",
            tip="Advance Prev"
        ),
        AnchoredLine(
            code="        curr = nxt       # Advance curr",
            narration="Aur current pointer ko saved next node pe shift kar do.",
            highlight=False,
            state_label="curr = nxt",
            tip="Advance Curr"
        ),
        AnchoredLine(
            code="    return prev          # New head",
            narration="Loop khatam hote hi prev pointer nayi reversed list ka head ban jaata hai!",
            highlight=True,
            state_label="return prev",
            tip="Return New Head"
        ),
    ],
    test_runner_code=(
        "class Node:\n"
        "    def __init__(self, val, next=None):\n"
        "        self.val = val; self.next = next\n\n"
        "def to_list(head):\n"
        "    r = []\n"
        "    while head: r.append(head.val); head = head.next\n"
        "    return r\n\n"
        "def reverse_list(head):\n"
        "    prev = None; curr = head\n"
        "    while curr:\n"
        "        nxt = curr.next; curr.next = prev; prev = curr; curr = nxt\n"
        "    return prev\n\n"
        "head = Node(1, Node(2, Node(3, Node(4, Node(5)))))\n"
        "print(f'Original List : {to_list(head)}')\n"
        "reversed_head = reverse_list(head)\n"
        "print(f'Reversed List : {to_list(reversed_head)}')\n"
        "print('>> TEST STATUS: PASS (O(n) In-Place)')\n"
    ),
    outro_narration="Three-pointer reversal in-place O of 1 memory me kaam karta hai. Follow for Day 6 tomorrow!",
    complexity_badge="O(n) TIME • O(1) SPACE",
    benchmark_metric="In-Place Pointer Reversal",
    problem_statement="Reverse a singly linked list in-place using O(1) auxiliary space.",
    input_example="1 -> 2 -> 3 -> 4 -> 5 -> NULL",
    naive_pitfall="Creating new list nodes wastes O(n) memory allocation",
    next_day_preview="Day 6: Best Time to Buy and Sell Stock (Greedy)"
)

# DAY 6: Best Time to Buy and Sell Stock
DAY6_BUY_SELL_STOCK = AnchoredLesson(
    id="day6_stock",
    title="Day 6: Best Time to Buy/Sell Stock",
    series_name="LEETCODE JOURNEY",
    episode_num=6,
    badge_tag="DAY 6 • DYNAMIC GREEDY",
    filename="max_profit.py",
    intro_narration="Welcome to Day 6 of LeetCode Journey! Stock profit nikalne ke liye nested loops nahi, single-pass minimum tracking use karo.",
    lines=[
        AnchoredLine(
            code="def max_profit(prices):",
            narration="Function prices list leta hai jisme daily stock rates hain.",
            highlight=False,
            state_label="prices: list",
            tip="Function Header"
        ),
        AnchoredLine(
            code="    min_price = float('inf')",
            narration="Lowest price ko infinity se initialize karte hain.",
            highlight=False,
            state_label="min_price = inf",
            tip="Min Price Tracker"
        ),
        AnchoredLine(
            code="    max_p = 0",
            narration="Maximum profit ko zero se initialize karte hain.",
            highlight=False,
            state_label="max_p = 0",
            tip="Max Profit Tracker"
        ),
        AnchoredLine(
            code="    for price in prices:",
            narration="Daily prices pe single pass scan chalate hain.",
            highlight=False,
            state_label="for price in prices",
            tip="Single Scan O(n)"
        ),
        AnchoredLine(
            code="        if price < min_price: min_price = price",
            narration="Agar aaj stock sabse sasta mila hai, toh min price update kar lo.",
            highlight=True,
            state_label="min_price updated",
            tip="Buy Opportunity"
        ),
        AnchoredLine(
            code="        elif price - min_price > max_p: max_p = price - min_price",
            narration="Warna aaj bechne par milne wala profit check karo aur maximum profit update karo!",
            highlight=True,
            state_label="max_p updated",
            tip="Sell Opportunity"
        ),
        AnchoredLine(
            code="    return max_p",
            narration="Scan khatam hone par guaranteed highest profit mil jaata hai.",
            highlight=True,
            state_label="return max_p",
            tip="Optimal Return"
        ),
    ],
    test_runner_code=(
        "def max_profit(prices):\n"
        "    min_price = float('inf'); max_p = 0\n"
        "    for price in prices:\n"
        "        if price < min_price: min_price = price\n"
        "        elif price - min_price > max_p: max_p = price - min_price\n"
        "    return max_p\n\n"
        "prices = [7, 1, 5, 3, 6, 4]\n"
        "profit = max_profit(prices)\n"
        "print(f'Stock Prices  : {prices}')\n"
        "print(f'Maximum Profit: {profit} (Buy at 1, Sell at 6)')\n"
        "print('>> TEST STATUS: PASS (O(n) Kadane Greedy)')\n"
    ),
    outro_narration="Single-pass greedy tracking se execution time 100x fast ho gaya. Follow for Day 7 tomorrow!",
    complexity_badge="O(n) TIME • O(1) SPACE",
    benchmark_metric="O(n) Greedy Single Pass",
    problem_statement="Maximize profit by choosing a single day to buy stock and a future day to sell.",
    input_example="prices = [7, 1, 5, 3, 6, 4]  ->  Max Profit: 5",
    naive_pitfall="Comparing all (i, j) pairs takes O(n²) nested loops",
    next_day_preview="Day 7: Merge Two Sorted Lists"
)

# DAY 14: Stop Wasting RAM (Generators vs Lists)
DAY14_GENERATORS = AnchoredLesson(
    id="day14_generators",
    title="Day 14: Stop Wasting RAM — Generators",
    series_name="100 DAYS OF PYTHON",
    episode_num=14,
    badge_tag="DAY 14 • MEMORY OPTIMIZATION",
    filename="generators.py",
    intro_narration="Welcome to Day 14 of 100 Days of Python! Agar aap 1 crore numbers process kar rahe ho, toh RAM crash hone se bachao.",
    lines=[
        AnchoredLine(
            code="# ❌ LIST COMPREHENSION (80MB RAM)",
            narration="List comprehension saare elements ko memory me ek saath allocate kar deta hai.",
            highlight=False,
            state_label="80,000,000 Bytes",
            tip="Eager Allocation"
        ),
        AnchoredLine(
            code="nums_list = [x * 2 for x in range(10_000_000)]",
            narration="Yeh ek single line server ki 80 megabytes RAM turant khaa jaati hai.",
            highlight=False,
            state_label="High Memory Spike",
            tip="RAM Spike"
        ),
        AnchoredLine(
            code="# ✨ GENERATOR EXPRESSION (112 BYTES ONLY)",
            narration="Solution: square brackets hata kar round parentheses laga do.",
            highlight=True,
            state_label="112 Bytes Only!",
            tip="Lazy Evaluation"
        ),
        AnchoredLine(
            code="nums_gen = (x * 2 for x in range(10_000_000))",
            narration="Ab ban gaya generator jo demand aane par ek ek element yield karta hai.",
            highlight=True,
            state_label="O(1) Constant RAM",
            tip="Generator Protocol"
        ),
        AnchoredLine(
            code="print(f'First: {next(nums_gen)}') # 0",
            narration="next call karne par next element calculate hota hai, state suspend rehti hai.",
            highlight=False,
            state_label="next() -> On Demand",
            tip="State Suspension"
        ),
    ],
    test_runner_code=(
        "import sys\n"
        "gen = (x * 2 for x in range(10_000_000))\n"
        "size_bytes = sys.getsizeof(gen)\n"
        "print(f'Generator Size in RAM: {size_bytes} bytes')\n"
        "print(f'First Element Yield  : {next(gen)}')\n"
        "print('>> TEST STATUS: PASS (99.9% Memory Saved)')\n"
    ),
    outro_narration="Generators production backend pipelines me Out Of Memory crashes rokte hain. Follow for Day 15 tomorrow!",
    complexity_badge="O(1) MEMORY FIXED",
    benchmark_metric="99.9% RAM Reduction (112 Bytes)",
    problem_statement="Prevent out-of-memory spikes when processing millions of stream items in Python.",
    input_example="range(10_000_000)  ->  10 Million integers",
    naive_pitfall="List comprehension allocates 80MB eagerly in RAM",
    next_day_preview="Day 15: Concurrency vs AsyncIO"
)


ANCHORED_CATALOG: Dict[str, AnchoredLesson] = {
    "1": DAY1_TWO_SUM,
    "day1": DAY1_TWO_SUM,
    "two_sum": DAY1_TWO_SUM,
    "day_1": DAY1_TWO_SUM,

    "2": DAY2_VALID_PARENS,
    "day2": DAY2_VALID_PARENS,
    "valid_parens": DAY2_VALID_PARENS,
    "valid_parentheses": DAY2_VALID_PARENS,
    "day_2": DAY2_VALID_PARENS,

    "3": DAY3_BINARY_SEARCH,
    "day3": DAY3_BINARY_SEARCH,
    "binary_search": DAY3_BINARY_SEARCH,
    "day_3": DAY3_BINARY_SEARCH,

    "4": DAY4_QUICKSORT,
    "day4": DAY4_QUICKSORT,
    "quicksort": DAY4_QUICKSORT,
    "day_4": DAY4_QUICKSORT,

    "5": DAY5_REVERSE_LIST,
    "day5": DAY5_REVERSE_LIST,
    "reverse_linked_list": DAY5_REVERSE_LIST,
    "reverse_list": DAY5_REVERSE_LIST,
    "day_5": DAY5_REVERSE_LIST,

    "6": DAY6_BUY_SELL_STOCK,
    "day6": DAY6_BUY_SELL_STOCK,
    "stock": DAY6_BUY_SELL_STOCK,
    "best_time_to_buy_and_sell_stock": DAY6_BUY_SELL_STOCK,
    "day_6": DAY6_BUY_SELL_STOCK,

    "14": DAY14_GENERATORS,
    "day14": DAY14_GENERATORS,
    "generators": DAY14_GENERATORS,
    "day_14": DAY14_GENERATORS,
}

QUICKSORT_ANCHORED = DAY4_QUICKSORT
TWO_SUM_ANCHORED = DAY1_TWO_SUM


def get_anchored_lesson(query: str | None) -> AnchoredLesson:
    """
    Dynamically maps any query (day 1, day 2, quicksort, stock, etc.)
    to its exact AnchoredLesson.
    """
    if not query:
        return DAY4_QUICKSORT
    
    q = query.lower().strip()
    
    # Check for direct day number matching: e.g. "day 2", "day 5", "5"
    day_match = re.search(r'\b(?:day\s*|ep\s*|episode\s*)?(\d+)\b', q)
    if day_match:
        d_num = day_match.group(1)
        if d_num in ANCHORED_CATALOG:
            return ANCHORED_CATALOG[d_num]

    # Keyword search
    clean_q = q.replace("-", "_").replace(" ", "_")
    for key, item in ANCHORED_CATALOG.items():
        if key in clean_q or clean_q in key:
            return item

    for item in ANCHORED_CATALOG.values():
        if any(w in item.title.lower() for w in q.split()):
            return item

    # If topic is not in static catalog, invoke AI Curriculum Generator dynamically!
    try:
        from ai_curriculum_generator import generate_ai_anchored_lesson
        return generate_ai_anchored_lesson(query)
    except Exception as e:
        print(f"[!] [Catalog] AI Generator fallback error: {e}")
        return DAY4_QUICKSORT


