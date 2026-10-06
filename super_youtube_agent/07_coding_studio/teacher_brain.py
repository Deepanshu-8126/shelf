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

    # -------------------------------------------------------------
    # SERIES 2: LEETCODE & DSA PATTERNS (The Technical Interview Roadmap)
    # -------------------------------------------------------------
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


def get_next_teacher_lesson(series_filter: str | None = None) -> TeacherLesson:
    init_teacher_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT series_name, episode_num FROM episode_history")
        used = set((r[0], r[1]) for r in cursor.fetchall())

    candidates = [
        les for les in MASTER_SERIES_CATALOG
        if (not series_filter or series_filter.lower() in les.series_name.lower())
        and (les.series_name, les.episode_num) not in used
    ]

    if not candidates:
        # If all used or query specific, pick from catalog
        if series_filter:
            for les in MASTER_SERIES_CATALOG:
                if series_filter.lower() in les.series_name.lower() or series_filter.lower() in les.topic_title.lower():
                    return les
        return MASTER_SERIES_CATALOG[0]

    chosen = candidates[0]
    # Mark used
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO episode_history (series_name, episode_num, topic_title) VALUES (?, ?, ?)",
                     (chosen.series_name, chosen.episode_num, chosen.topic_title))
        conn.commit()

    return chosen
