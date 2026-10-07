"""
Teacher Brain & Series Engine for Channel 7 (Coding & Tech Studio).
Treats the channel as a Senior Software Engineer / Tech Instructor:
Playlists:
1. PYTHON 100 DAYS OF CODE (Core to Advanced internals)
2. LEETCODE & DSA PATTERNS (Pattern-based interview problem solving)
3. TRENDING LIBRARIES & DEV TOOLS (Polars, uv, DuckDB, Ollama, FastAPI)
4. SYSTEM DESIGN IN 60 SECONDS (Redis, B-Trees, Rate Limiting, Kafka)

Maintains episode progression state (Day 1 -> Day 2 -> Day 3...).
"""
from __future__ import annotations
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

DB_PATH = Path("d:/facts_yt/super_youtube_agent/07_coding_studio/teacher_memory.db")


@dataclass
class TeacherLesson:
    series_name: str        # e.g. "100 DAYS OF PYTHON", "LEETCODE PATTERNS", "TRENDING LIBRARIES"
    episode_num: int        # e.g. 14
    topic_title: str        # "Generators vs Lists (Memory Profiling)"
    badge_tag: str          # "ADVANCED PYTHON" / "SLIDING WINDOW" / "PERFORMANCE"
    filename: str           # "generator_benchmark.py"
    language: str           # "python", "sql", "bash"
    
    # 4-Stage Pedagogical Narration
    intro_hook: str         # "Welcome to Day 14 of 100 Days of Python. Today we solve a massive memory leak..."
    concept_walkthrough: str# "When you use a list comprehension with 10 million items, Python allocates gigabytes..."
    code_explanation: str   # "By simply swapping brackets to parentheses, we create a generator object that yields..."
    outro_homework: str     # "Save this snippet, and tell me in the comments: have you ever hit a memory error?"

    # Code Snippets (Before vs After / Bad vs Clean)
    code_before: list[tuple[str, str]]   # Naive or unoptimized snippet [(line, type)]
    code_after: list[tuple[str, str]]    # Teacher's clean production solution [(line, type)]
    
    # Teacher Callout Card
    teacher_tip: str                     # "PRO-TIP: sys.getsizeof() drops from 80MB to 112 bytes!"
    terminal_command: str                # "$ python3 memory_profile.py"
    terminal_logs: list[str]             # Live execution log lines


MASTER_SERIES_CATALOG: list[TeacherLesson] = [
    # -------------------------------------------------------------
    # SERIES 1: 100 DAYS OF PYTHON (The Complete Developer Masterclass)
    # -------------------------------------------------------------
    TeacherLesson(
        series_name="100 DAYS OF PYTHON",
        episode_num=1,
        topic_title="The Mutable Default Argument Bug",
        badge_tag="PYTHON INTERNALS • TRAP #1",
        filename="mutable_default_trap.py",
        language="python",
        intro_hook="Welcome to Day 1 of 100 Days of Python. Here is the number one bug that trips up every junior Python developer.",
        concept_walkthrough="In Python, default arguments are evaluated only once when the function is defined, not every time it is called. That means your list persists across function calls.",
        code_explanation="Always set the default parameter to None, and initialize a new list inside the function body. This guarantees a fresh instance every time.",
        outro_homework="Never pass mutable objects as default arguments. Follow for Day 2 tomorrow!",
        code_before=[
            ("# ❌ JUNIOR MISTAKE: MUTABLE DEFAULT LIST", "comment"),
            ("def add_item(item, basket=[]):", "def"),
            ("    basket.append(item)  # ⚠️ Shared across all calls!", "call"),
            ("    return basket", "return"),
            ("print(add_item('apple'))  # ['apple']", "call"),
            ("print(add_item('banana')) # ['apple', 'banana'] BUG!", "call"),
        ],
        code_after=[
            ("# ✨ SENIOR FIX: DEFAULT TO NONE", "comment"),
            ("def add_item(item, basket=None):", "def"),
            ("    if basket is None:", "keyword"),
            ("        basket = []       # Fresh list per call", "assign"),
            ("    basket.append(item)", "call"),
            ("    return basket", "return"),
        ],
        teacher_tip="TEACHER TIP: Default args are bound to the function object at definition time!",
        terminal_command="$ python3 mutable_default_trap.py",
        terminal_logs=[
            "Test 1: add_item('apple')  -> ['apple']",
            "Test 2: add_item('banana') -> ['banana'] (Isolated)",
            ">> BUG RESOLVED: Zero state bleeding between sessions!",
        ]
    ),
    TeacherLesson(
        series_name="100 DAYS OF PYTHON",
        episode_num=7,
        topic_title="List vs Set: 1,000x Lookup Speedup",
        badge_tag="BIG-O COMPLEXITY • SEARCH",
        filename="lookup_benchmark.py",
        language="python",
        intro_hook="Welcome to Day 7 of 100 Days of Python. If you are checking membership in large lists, your code is 1,000 times slower than it could be.",
        concept_walkthrough="Checking 'in' on a list performs an O of n linear scan through every element. A hash set computes a hash code in O of 1 constant time.",
        code_explanation="Converting your lookup collection to a set drops query time from 40 milliseconds to 40 nanoseconds. Instant speedup with zero refactoring.",
        outro_homework="Always use sets for lookups and filtering. Follow for Day 8 tomorrow!",
        code_before=[
            ("# ❌ LIST LOOKUP: O(n) LINEAR SCAN (42.1ms)", "comment"),
            ("valid_ids = [i for i in range(1_000_000)]", "assign"),
            ("def check_user(user_id):", "def"),
            ("    return user_id in valid_ids  # Scans 1M elements!", "return"),
        ],
        code_after=[
            ("# ✨ SET LOOKUP: O(1) CONSTANT TIME (0.04ms)", "comment"),
            ("valid_ids = set(range(1_000_000))  # Hash table lookup", "assign"),
            ("def check_user(user_id):", "def"),
            ("    return user_id in valid_ids  # ⚡ 1,000x Faster!", "return"),
        ],
        teacher_tip="TEACHER TIP: Sets use open-addressing hash tables — lookup is independent of collection size!",
        terminal_command="$ python3 lookup_benchmark.py --benchmark",
        terminal_logs=[
            "[+] Running 10,000 membership queries on 1,000,000 items...",
            "[x] List lookup time : 42.10 ms per query",
            "[✓] Set lookup time  : 0.04 ms per query",
            ">> RESULT: 1,052x SPEEDUP ACHIEVED!",
        ]
    ),
    TeacherLesson(
        series_name="100 DAYS OF PYTHON",
        episode_num=14,
        topic_title="Stop Wasting RAM: Generators vs Lists",
        badge_tag="MEMORY OPTIMIZATION",
        filename="generator_bench.py",
        language="python",
        intro_hook="Welcome back to Day 14 of 100 Days of Python. Today I'm showing you how to process 10 million items without crashing your server.",
        concept_walkthrough="A list comprehension builds all 10 million numbers in memory simultaneously. That allocates hundreds of megabytes of RAM.",
        code_explanation="Simply replace the square brackets with round parentheses. Now you have a generator expression that yields items on demand in O of 1 memory.",
        outro_homework="Generators are essential for production data pipelines. Follow for Day 15 tomorrow!",
        code_before=[
            ("# ❌ DAY 14: LIST COMPREHENSION (80MB RAM)", "comment"),
            ("import sys", "keyword"),
            ("numbers_list = [x * 2 for x in range(10_000_000)]", "assign"),
            ("ram_usage = sys.getsizeof(numbers_list) / (1024*1024)", "assign"),
            ("print(f'RAM Usage: {ram_usage:.1f} MB') # ⚠️ 80.0 MB!", "call"),
        ],
        code_after=[
            ("# ✨ DAY 14: GENERATOR EXPRESSION (112 BYTES)", "comment"),
            ("import sys", "keyword"),
            ("numbers_gen = (x * 2 for x in range(10_000_000))", "assign"),
            ("ram_usage = sys.getsizeof(numbers_gen)", "assign"),
            ("print(f'RAM Usage: {ram_usage} Bytes') # ⚡ ONLY 112 B!", "call"),
            ("first_item = next(numbers_gen)        # Yields on demand", "call"),
        ],
        teacher_tip="TEACHER TIP: Generators compute lazy evaluation — 80MB drops to 112 bytes!",
        terminal_command="$ python3 generator_bench.py",
        terminal_logs=[
            "[+] Profiling memory with tracemalloc...",
            "[x] List comprehension peak: 82.4 MB RAM",
            "[✓] Generator expression peak: 112 Bytes RAM",
            ">> RESULT: 735,000x MEMORY REDUCTION!",
        ]
    ),
    TeacherLesson(
        series_name="100 DAYS OF PYTHON",
        episode_num=27,
        topic_title="Decorators Demystified in 45 Seconds",
        badge_tag="INTERMEDIATE PYTHON",
        filename="timing_decorator.py",
        language="python",
        intro_hook="Welcome to Day 27 of 100 Days of Python. Today we demystify decorators, the most powerful syntactic sugar in Python.",
        concept_walkthrough="A decorator is simply a function that takes another function, wraps extra behavior around it, and returns it.",
        code_explanation="Here is a production execution timer. It records start time, executes your target function, and logs elapsed milliseconds.",
        outro_homework="Now you can time any API route with a single at symbol. Save this snippet for your projects!",
        code_before=[
            ("# ❌ MANUALLY TIMING EVERY FUNCTION (REDUNDANT)", "comment"),
            ("import time", "keyword"),
            ("def fetch_user_data():", "def"),
            ("    t0 = time.perf_counter()", "assign"),
            ("    db_query() # do actual work", "call"),
            ("    print(f'Time: {time.perf_counter() - t0:.4f}s')", "call"),
        ],
        code_after=[
            ("# ✨ ELEGANT REUSABLE @TIMER DECORATOR", "comment"),
            ("import time, functools", "keyword"),
            ("def timer(func):", "def"),
            ("    @functools.wraps(func)", "keyword"),
            ("    def wrapper(*args, **kwargs):", "def"),
            ("        t0 = time.perf_counter()", "assign"),
            ("        res = func(*args, **kwargs)", "assign"),
            ("        print(f'{func.__name__}: {time.perf_counter()-t0:.4f}s')", "call"),
            ("        return res", "return"),
            ("    return wrapper", "return"),
        ],
        teacher_tip="TEACHER TIP: Always use @functools.wraps to preserve function metadata & docstrings!",
        terminal_command="$ python3 timing_decorator.py",
        terminal_logs=[
            "@timer applied to calculate_analytics()...",
            "[✓] query_users() took: 0.0042s",
            "[✓] aggregate_metrics() took: 0.0128s",
            ">> CLEAN CODE: Zero code duplication across 50 endpoints!",
        ]
    ),
    TeacherLesson(
        series_name="100 DAYS OF PYTHON",
        episode_num=38,
        topic_title="is vs == (Integer Interning Trap)",
        badge_tag="PYTHON INTERNALS • PITFALL",
        filename="is_vs_equal.py",
        language="python",
        intro_hook="Welcome to Day 38 of 100 Days of Python. If you don't know the difference between 'is' and '==', this silent bug will ruin your production code.",
        concept_walkthrough="Double equals checks equality of value. The keyword 'is' checks identity of memory address. Python caches small integers from minus 5 to 256.",
        code_explanation="Comparing numbers with 'is' works for 256 but fails for 257 because Python allocates a distinct memory object. Always use double equals for value comparisons.",
        outro_homework="Only use 'is' when comparing against singletons like None. Save this snippet!",
        code_before=[
            ("# ❌ SILENT BUG: USING 'IS' FOR VALUE COMPARISON", "comment"),
            ("a = 256; b = 256", "assign"),
            ("print(a is b)  # True  (Interned in Python cache)", "call"),
            ("x = 257; y = 257", "assign"),
            ("print(x is b)  # False ⚠️ SILENT PRODUCTION FAILURE!", "call"),
        ],
        code_after=[
            ("# ✨ CORRECT: USE == FOR VALUES, 'IS' FOR NONE", "comment"),
            ("x = 257; y = 257", "assign"),
            ("print(x == y)      # True (Always compares value)", "call"),
            ("result = None", "assign"),
            ("if result is None: # Correct singleton comparison", "keyword"),
            ("    process_data()", "call"),
        ],
        teacher_tip="TEACHER TIP: '==' calls __eq__; 'is' checks id(a) == id(b) identity in RAM!",
        terminal_command="$ python3 is_vs_equal.py",
        terminal_logs=[
            "Testing 256: id(a) == id(b) -> TRUE (interned range -5..256)",
            "Testing 257: id(x) == id(y) -> FALSE (distinct memory heap)",
            ">> LESSON: Always use == for numerical and string comparisons!",
        ]
    ),

    # -------------------------------------------------------------
    # SERIES 2: LEETCODE & DSA PATTERNS (The Technical Interview Roadmap)
    # -------------------------------------------------------------
    TeacherLesson(
        series_name="LEETCODE DSA PATTERNS",
        episode_num=1,
        topic_title="Two Sum: Hash Map O(n) vs Brute Force",
        badge_tag="ARRAYS & HASHING • PATTERN #1",
        filename="two_sum.py",
        language="python",
        intro_hook="Welcome to Episode 1 of LeetCode Patterns. Here is how to turn an O of n squared brute force into an optimal O of n solution.",
        concept_walkthrough="Nested loops compare every pair of numbers, which times out on large inputs. In an interview, immediate brute force is a red flag.",
        code_explanation="Instead, store each number's index in a hash map as you iterate. Look for target minus current number in O of 1 time.",
        outro_homework="The hash map pattern is used in 40% of FAANG array questions. Follow for Pattern 2!",
        code_before=[
            ("# ❌ BRUTE FORCE: O(n²) TIME COMPLEXITY", "comment"),
            ("def twoSum(nums, target):", "def"),
            ("    for i in range(len(nums)):", "loop"),
            ("        for j in range(i + 1, len(nums)):", "loop"),
            ("            if nums[i] + nums[j] == target:", "keyword"),
            ("                return [i, j] # ⚠️ Times out on 100k items", "return"),
        ],
        code_after=[
            ("# ✨ ONE-PASS HASH MAP: O(n) TIME, O(n) SPACE", "comment"),
            ("def twoSum(nums, target):", "def"),
            ("    seen = {} # val -> index", "assign"),
            ("    for i, num in enumerate(nums):", "loop"),
            ("        diff = target - num", "assign"),
            ("        if diff in seen: return [seen[diff], i]", "keyword"),
            ("        seen[num] = i", "assign"),
        ],
        teacher_tip="TEACHER TIP: Hash map trading space for time is the core philosophy of DSA interviews!",
        terminal_command="$ python3 two_sum.py --test",
        terminal_logs=[
            "Test 1: nums=[2,7,11,15], target=9 -> Output: [0, 1] [PASS]",
            "Test 2: nums=[3,2,4], target=6      -> Output: [1, 2] [PASS]",
            "Runtime: 0.02ms (Beats 98.4% of Python Submissions)",
        ]
    ),
    TeacherLesson(
        series_name="LEETCODE DSA PATTERNS",
        episode_num=4,
        topic_title="QuickSort Partition in 60 Seconds",
        badge_tag="DIVIDE & CONQUER • SORTING",
        filename="quicksort.py",
        language="python",
        intro_hook="Welcome to LeetCode Patterns. Here is QuickSort explained step-by-step so simply you will never forget it in an interview.",
        concept_walkthrough="QuickSort picks a pivot element, partitions the array into elements smaller than pivot and greater than pivot, and recurses on both halves.",
        code_explanation="With Python list comprehensions, you can write QuickSort in just four lines of clean code. Base case: an array of length one or zero is already sorted.",
        outro_homework="QuickSort achieves O of n log n average time. Save this snippet and practice on LeetCode!",
        code_before=[
            ("# [!] BUBBLE SORT: O(n²) QUADRATIC SCAN", "comment"),
            ("def bubble_sort(arr):", "def"),
            ("    for i in range(len(arr)):", "loop"),
            ("        for j in range(len(arr) - 1):", "loop"),
            ("            if arr[j] > arr[j+1]: arr[j], arr[j+1] = arr[j+1], arr[j]", "assign"),
            ("    return arr", "return"),
        ],
        code_after=[
            ("# [*] QUICKSORT: ELEGANT 4-LINE RECURSION", "comment"),
            ("def quicksort(arr):", "def"),
            ("    if len(arr) <= 1: return arr", "keyword"),
            ("    pivot = arr[len(arr) // 2]", "assign"),
            ("    left = [x for x in arr if x < pivot]", "assign"),
            ("    right = [x for x in arr if x > pivot]", "assign"),
            ("    return quicksort(left) + [pivot] + quicksort(right)", "return"),
        ],
        teacher_tip="TEACHER TIP: QuickSort achieves O(n log n) by partitioning work around the pivot!",
        terminal_command="$ python3 quicksort.py --dry-run",
        terminal_logs=[
            "Data: [38, 27, 43, 3, 9, 82, 10]",
            "Pivot = 9 -> Left: [3], Right: [38, 27, 43, 82, 10]",
            ">> SORTED: [3, 9, 10, 27, 38, 43, 82] [PASS]",
        ]
    ),
    TeacherLesson(
        series_name="LEETCODE DSA PATTERNS",
        episode_num=6,
        topic_title="Sliding Window: Maximum Sum Subarray",
        badge_tag="SLIDING WINDOW • PATTERN #6",
        filename="max_subarray_k.py",
        language="python",
        intro_hook="Welcome to LeetCode Patterns Episode 6. Today we master the Sliding Window technique to find the max subarray sum of size K.",
        concept_walkthrough="Recalculating the sum of every K-length subarray from scratch recomputes K minus 1 elements repeatedly, taking O of n times K time.",
        code_explanation="Maintain a running window sum. When sliding forward, simply add the new incoming number and subtract the outgoing element in O of 1 time.",
        outro_homework="Mastering sliding window allows you to solve subarray and substring problems effortlessly. Follow for Episode 7!",
        code_before=[
            ("# ❌ RECOMPUTING SUMS: O(n * k) UNNECESSARY WORK", "comment"),
            ("def maxSubArrayK(nums, k):", "def"),
            ("    max_sum = float('-inf')", "assign"),
            ("    for i in range(len(nums) - k + 1):", "loop"),
            ("        curr_sum = sum(nums[i:i+k]) # Recomputes window!", "call"),
            ("        max_sum = max(max_sum, curr_sum)", "call"),
            ("    return max_sum", "return"),
        ],
        code_after=[
            ("# ✨ SLIDING WINDOW: O(n) TIME, O(1) SPACE", "comment"),
            ("def maxSubArrayK(nums, k):", "def"),
            ("    curr = max_sum = sum(nums[:k])", "assign"),
            ("    for i in range(k, len(nums)):", "loop"),
            ("        curr += nums[i] - nums[i - k] # Slide in O(1)!", "assign"),
            ("        if curr > max_sum: max_sum = curr", "keyword"),
            ("    return max_sum", "return"),
        ],
        teacher_tip="TEACHER TIP: Sliding window reuses existing work — add the incoming element, subtract the outgoing!",
        terminal_command="$ python3 max_subarray_k.py",
        terminal_logs=[
            "Array: [2, 1, 5, 1, 3, 2], k=3",
            "Window 1: [2, 1, 5] -> Sum 8",
            "Window 2: [1, 5, 1] -> Sum 7",
            "Window 3: [5, 1, 3] -> Sum 9 [MAXIMUM DETECTED]",
            ">> RESULT: Solved in single pass O(n) time!",
        ]
    ),
    TeacherLesson(
        series_name="LEETCODE DSA PATTERNS",
        episode_num=12,
        topic_title="Fast & Slow Pointers (Cycle Detection)",
        badge_tag="LINKED LISTS • PATTERN #12",
        filename="has_cycle.py",
        language="python",
        intro_hook="Welcome to LeetCode Patterns Episode 12. Today we master Floyd's Tortoise and Hare algorithm for linked list cycles.",
        concept_walkthrough="Storing visited nodes in a set takes O of n extra memory. Top tech companies will ask you to solve this in O of 1 space.",
        code_explanation="Advance the slow pointer by one step and fast pointer by two steps. If a cycle exists, they will mathematically collide in O of n time.",
        outro_homework="Fast and slow pointers solve cycle detection, middle of linked list, and happy number. Master this pattern!",
        code_before=[
            ("# ❌ NAIVE SET APPROACH: O(n) EXTRA MEMORY", "comment"),
            ("def hasCycle(head):", "def"),
            ("    visited = set() # ⚠️ Allocates extra RAM", "assign"),
            ("    curr = head", "assign"),
            ("    while curr:", "loop"),
            ("        if curr in visited: return True", "keyword"),
            ("        visited.add(curr); curr = curr.next", "call"),
            ("    return False", "return"),
        ],
        code_after=[
            ("# ✨ FLOYD'S ALGORITHM: O(1) CONSTANT SPACE", "comment"),
            ("def hasCycle(head):", "def"),
            ("    slow = fast = head", "assign"),
            ("    while fast and fast.next:", "loop"),
            ("        slow = slow.next       # moves 1 step", "assign"),
            ("        fast = fast.next.next  # moves 2 steps", "assign"),
            ("        if slow == fast:       # collision!", "keyword"),
            ("            return True", "return"),
            ("    return False", "return"),
        ],
        teacher_tip="TEACHER TIP: Fast pointer closes the gap by 1 node per iteration — guaranteed collision!",
        terminal_command="$ python3 has_cycle.py --test",
        terminal_logs=[
            "Test 1: Node 3 -> Node 2 -> Node 0 -> Node -4 (Cycle to pos 1)",
            "Step 1: slow=2, fast=0",
            "Step 2: slow=0, fast=2",
            "Step 3: slow=-4, fast=-4 [COLLISION DETECTED!]",
            ">> RESULT: Cycle found in O(1) space, 0ms latency!",
        ]
    ),

    # -------------------------------------------------------------
    # SERIES 3: TRENDING LIBRARIES & TOOLS (Modern Python 2026)
    # -------------------------------------------------------------
    TeacherLesson(
        series_name="TRENDING PYTHON TOOLS",
        episode_num=1,
        topic_title="uv vs Pip: 100x Faster Python Packaging",
        badge_tag="RUST TOOLING • DEVELOPER SPEED",
        filename="uv_speed.sh",
        language="bash",
        intro_hook="If you are still waiting 2 minutes for pip to install dependencies, switch to uv today. It is 100 times faster.",
        concept_walkthrough="Pip is written in pure Python and resolves wheels sequentially. Astral's uv is written in Rust with concurrent dependency resolution and global cache.",
        code_explanation="Simply prefix your pip command with uv. A cold installation of PyTorch or Pandas drops from 90 seconds to under 1 second.",
        outro_homework="uv also manages Python versions and virtual environments. Replace pip today!",
        code_before=[
            ("# ❌ PIP: SLOW PYTHON RESOLUTION (48.6s)", "comment"),
            ("$ python3 -m venv .venv", "call"),
            ("$ source .venv/bin/activate", "call"),
            ("$ pip install pandas torch transformers # ⚠️ 48s wait!", "call"),
        ],
        code_after=[
            ("# ✨ UV: RUST-POWERED INSTANT WHEELS (0.6s)", "comment"),
            ("$ uv venv                          # Instant venv creation", "call"),
            ("$ uv pip install pandas torch transformers # ⚡ 0.6 seconds!", "call"),
            ("$ uv run script.py                # Zero environment friction", "call"),
        ],
        teacher_tip="TEACHER TIP: uv uses hardlinks from a global cache — zero duplicated disk space!",
        terminal_command="$ uv pip install pandas scipy -v",
        terminal_logs=[
            "Resolved 12 packages in 34ms",
            "Installed 12 packages in 182ms",
            ">> TIME: 0.42s (versus pip 24.3s) — 57x SPEEDUP!",
        ]
    ),
    TeacherLesson(
        series_name="TRENDING PYTHON TOOLS",
        episode_num=4,
        topic_title="Stop Using Pandas for Big Data: Use Polars",
        badge_tag="MODERN LIBRARIES • 10x SPEED",
        filename="polars_speed.py",
        language="python",
        intro_hook="If you are still writing Pandas in 2026, here is why your data pipelines are 10 times slower than they should be.",
        concept_walkthrough="Pandas runs single-threaded in Python with high memory overhead. Polars is written in Rust with true multi-threading and query optimization.",
        code_explanation="Notice how Polars uses lazy frames. It analyzes your entire query chain before execution and prunes unused columns automatically.",
        outro_homework="Run this 3-line migration and watch your CPU utilize all cores. Drop a like if you love fast data!",
        code_before=[
            ("# ❌ PANDAS: SINGLE THREADED & SLOW (28.4s)", "comment"),
            ("import pandas as pd", "keyword"),
            ("df = pd.read_csv('10m_transactions.csv')", "assign"),
            ("res = df[df['amount'] > 100].groupby('user')['amount'].sum()", "assign"),
            ("# ⚠️ Eats 6GB RAM, maxes out only 1 CPU core!", "comment"),
        ],
        code_after=[
            ("# ✨ POLARS: RUST MULTI-THREADED LAZY ENGINE (1.8s)", "comment"),
            ("import polars as pl", "keyword"),
            ("q = (pl.scan_csv('10m_transactions.csv')", "assign"),
            ("     .filter(pl.col('amount') > 100)", "call"),
            ("     .group_by('user').agg(pl.col('amount').sum()))", "call"),
            ("res = q.collect() # ⚡ Auto query optimizer!", "assign"),
        ],
        teacher_tip="TEACHER TIP: Polars pl.scan_csv compiles execution plans in Rust across all CPU cores!",
        terminal_command="$ python3 polars_speed.py --benchmark",
        terminal_logs=[
            "[+] Benchmark on 10,000,000 transaction rows:",
            "[x] Pandas 2.2 runtime : 28.42 seconds (Peak 5.8 GB RAM)",
            "[✓] Polars 1.1 runtime : 1.76 seconds  (Peak 0.9 GB RAM)",
            ">> SPEEDUP: 16.1x FASTER with 85% less memory!",
        ]
    ),
    TeacherLesson(
        series_name="TRENDING PYTHON TOOLS",
        episode_num=7,
        topic_title="DuckDB: Run SQL on Parquet in 50ms",
        badge_tag="EMBEDDED OLAP • IN-PROCESS SQL",
        filename="duckdb_analytics.py",
        language="python",
        intro_hook="Stop spinning up Postgres or Snowflake just to analyze raw CSV or Parquet files. Use DuckDB.",
        concept_walkthrough="DuckDB is the SQLite of analytics. It runs in-process with columnar vectorized execution and directly queries Parquet files without importing.",
        code_explanation="With two lines of code, DuckDB queries a multi-gigabyte Parquet file directly from disk or S3 with zero memory bloat.",
        outro_homework="DuckDB is the future of local and serverless data analytics. Star this video!",
        code_before=[
            ("# ❌ TRADITIONAL: LOAD TO DATABASE FIRST", "comment"),
            ("import sqlite3, pandas as pd", "keyword"),
            ("df = pd.read_parquet('sales_2025.parquet')", "assign"),
            ("df.to_sql('sales', conn) # ⚠️ Slow copy into DB!", "call"),
        ],
        code_after=[
            ("# ✨ DUCKDB: DIRECT ZERO-COPY IN-MEMORY SQL", "comment"),
            ("import duckdb", "keyword"),
            ("res = duckdb.sql('''", "assign"),
            ("    SELECT region, SUM(amount) FROM 'sales_*.parquet'", "keyword"),
            ("    GROUP BY region ORDER BY 2 DESC LIMIT 5", "keyword"),
            ("''').df() # ⚡ Vectorized query in 45ms!", "call"),
        ],
        teacher_tip="TEACHER TIP: DuckDB vectorizes column queries directly into CPU cache registers!",
        terminal_command="$ python3 duckdb_analytics.py",
        terminal_logs=[
            "Scanning 4,500,000 records across 12 parquet files...",
            "[✓] Query executed in 0.048 seconds",
            ">> RESULT: Zero DB server needed, zero import latency!",
        ]
    ),

    # -------------------------------------------------------------
    # SERIES 4: SYSTEM DESIGN IN 60 SECONDS (Production Architecture)
    # -------------------------------------------------------------
    TeacherLesson(
        series_name="SYSTEM DESIGN IN 60s",
        episode_num=1,
        topic_title="Redis Cache-Aside Pattern in Production",
        badge_tag="CACHING ARCHITECTURE • RESILIENCE",
        filename="cache_aside.py",
        language="python",
        intro_hook="Welcome to System Design in 60 Seconds. Today: how top tech companies protect their databases using the Cache-Aside pattern.",
        concept_walkthrough="Hitting the database on every user request will melt your database server during traffic spikes. You need an in-memory caching layer.",
        code_explanation="First check Redis. If there is a cache hit, return immediately. If a cache miss occurs, query the database, populate Redis with a TTL, and return.",
        outro_homework="Always set a TTL to prevent stale data. Subscribe for Episode 2!",
        code_before=[
            ("# ❌ DIRECT DATABASE QUERIES: 10,000 QPS DB CRASH", "comment"),
            ("def get_user_profile(user_id):", "def"),
            ("    # ⚠️ Every request hammers Postgres directly!", "comment"),
            ("    return db.query('SELECT * FROM users WHERE id = %s', user_id)", "return"),
        ],
        code_after=[
            ("# ✨ CACHE-ASIDE PATTERN: REDIS IN-MEMORY LAYER", "comment"),
            ("def get_user_profile(user_id):", "def"),
            ("    cached = redis_client.get(f'user:{user_id}')", "assign"),
            ("    if cached: return json.loads(cached) # ⚡ 1ms response", "keyword"),
            ("    user = db.query('SELECT * FROM users WHERE id = %s', user_id)", "assign"),
            ("    redis_client.setex(f'user:{user_id}', 3600, json.dumps(user))", "call"),
            ("    return user", "return"),
        ],
        teacher_tip="TEACHER TIP: Cache-aside makes your system resilient even if Redis temporarily goes down!",
        terminal_command="$ locust -f load_test.py --headless -u 5000",
        terminal_logs=[
            "[+] Load test with 5,000 concurrent users:",
            "[x] Direct DB: 480 QPS, Latency 240ms, 4.2% Errors",
            "[✓] Redis Cache-Aside: 12,400 QPS, Latency 1.8ms, 0% Errors",
            ">> SYSTEM DESIGN: 25x Throughput Increase!",
        ]
    ),
]


def init_teacher_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episode_history (
                series_name TEXT,
                episode_num INTEGER,
                topic_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (series_name, episode_num)
            )
        """)
        conn.commit()


def generate_ai_teacher_lesson(user_topic: str) -> TeacherLesson | None:
    """Uses Gemini 2.5 Flash to dynamically formulate a TeacherLesson for ANY programming topic."""
    import os
    import httpx

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Check fallback files
        for p in [Path("d:/facts_yt/.env"), Path("d:/facts_yt/super_youtube_agent/01_facts_shorts/.env")]:
            if p.exists():
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if api_key:
                break

    if not api_key:
        return None

    print(f"🧠 [Teacher Brain AI] Prompting Gemini Flash to create lesson for: '{user_topic}'...")

    system_instruction = (
        "You are an elite Senior Staff Software Engineer and programming instructor creating an authoritative, "
        "high-energy 30-45s vertical video coding lesson (like NeetCode, Fireship, or Alex Xu). "
        "Focus on practical code pedagogy: start with a common pitfall/naive code, transition to the optimal/senior solution, "
        "and provide benchmark telemetry logs. Output STRICT JSON only conforming to the requested schema."
    )

    prompt = f"""
    Create a complete coding short lesson for the topic: "{user_topic}".
    Return a JSON object with EXACTLY the following structure:
    {{
        "series_name": "100 DAYS OF PYTHON" or "LEETCODE DSA PATTERNS" or "TRENDING PYTHON TOOLS" or "SYSTEM DESIGN IN 60s",
        "episode_num": 99,
        "topic_title": "Concise Catchy Title (Max 6 words)",
        "badge_tag": "SHORT BADGE (Max 25 chars)",
        "filename": "demo_snippet.py",
        "language": "python",
        "intro_hook": "Hook sentence challenging the viewer or stating the trap (under 25 words).",
        "concept_walkthrough": "Why the naive way is bad or slow (under 30 words).",
        "code_explanation": "Explanation of the clean solution (under 30 words).",
        "outro_homework": "Takeaway or action item (under 20 words).",
        "code_before": [
            ["# ❌ NAIVE OR SLOW CODE", "comment"],
            ["line of code", "keyword/def/call/assign"]
        ],
        "code_after": [
            ["# ✨ SENIOR PRODUCTION CLEAN CODE", "comment"],
            ["line of code", "keyword/def/call/assign"]
        ],
        "teacher_tip": "TEACHER TIP: High value insight under 15 words.",
        "terminal_command": "$ python3 demo_snippet.py",
        "terminal_logs": [
            "Benchmark or test pass output line 1",
            "Output line 2",
            ">> RESULT: Impressive speedup or fix!"
        ]
    }}
    Ensure code_before and code_after have at most 6 lines each so they fit on screen comfortably.
    """

    candidate_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }

    try:
        with httpx.Client(timeout=22.0) as client:
            for model in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                try:
                    resp = client.post(url, params={"key": api_key}, json=body)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(raw_text)
                        lesson = TeacherLesson(
                            series_name=parsed.get("series_name", "MODERN DEV MASTERCLASS"),
                            episode_num=int(parsed.get("episode_num", 101)),
                            topic_title=parsed.get("topic_title", user_topic),
                            badge_tag=parsed.get("badge_tag", "SENIOR ENGINEERING"),
                            filename=parsed.get("filename", "solution.py"),
                            language=parsed.get("language", "python"),
                            intro_hook=parsed.get("intro_hook", ""),
                            concept_walkthrough=parsed.get("concept_walkthrough", ""),
                            code_explanation=parsed.get("code_explanation", ""),
                            outro_homework=parsed.get("outro_homework", ""),
                            code_before=[(l[0], l[1]) for l in parsed.get("code_before", [])],
                            code_after=[(l[0], l[1]) for l in parsed.get("code_after", [])],
                            teacher_tip=parsed.get("teacher_tip", "TEACHER TIP: Clean code wins!"),
                            terminal_command=parsed.get("terminal_command", "$ python3 test.py"),
                            terminal_logs=parsed.get("terminal_logs", ["All tests passing!"])
                        )
                        print(f"✨ [Teacher Brain AI] Dynamically crafted lesson with {model}: {lesson.topic_title} ({lesson.series_name})")
                        return lesson
                except Exception:
                    continue
    except Exception as e:
        print(f"⚠️ [Teacher Brain AI] Dynamic generation failed ({e}), falling back to catalog.")
        return None
    return None


def get_next_teacher_lesson(series_or_topic_filter: str | None = None) -> TeacherLesson:
    init_teacher_db()

    # 1. If explicit topic given, try dynamic AI generation first
    if series_or_topic_filter and len(series_or_topic_filter.strip()) > 3:
        clean_q = series_or_topic_filter.strip().lower()

        # Check if direct match in catalog
        for les in MASTER_SERIES_CATALOG:
            if clean_q in les.topic_title.lower() or clean_q in les.series_name.lower():
                return les

        # If not in catalog, try Gemini AI Teacher Generator
        ai_lesson = generate_ai_teacher_lesson(series_or_topic_filter)
        if ai_lesson:
            return ai_lesson

    # 2. Sequential progression from Catalog using database memory
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT series_name, episode_num FROM episode_history")
        used = set((r[0], r[1]) for r in cursor.fetchall())

    candidates = [
        les for les in MASTER_SERIES_CATALOG
        if (not series_or_topic_filter or series_or_topic_filter.lower() in les.series_name.lower())
        and (les.series_name, les.episode_num) not in used
    ]

    if not candidates:
        if series_or_topic_filter:
            for les in MASTER_SERIES_CATALOG:
                if series_or_topic_filter.lower() in les.series_name.lower() or series_or_topic_filter.lower() in les.topic_title.lower():
                    return les
        return MASTER_SERIES_CATALOG[0]

    chosen = candidates[0]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO episode_history (series_name, episode_num, topic_title) VALUES (?, ?, ?)",
                     (chosen.series_name, chosen.episode_num, chosen.topic_title))
        conn.commit()

    return chosen

