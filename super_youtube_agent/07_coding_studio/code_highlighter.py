"""
Code Highlighting & Typing Tokenizer Engine for Channel 7 Coding Studio.
Integrates Pygments to provide token-accurate styling, character-by-character
streaming, and cursor tracking for both Light and Dark editor themes.
"""

from typing import List, Tuple, Dict, Any, Optional
import pygments
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.token import (
    Token,
    Keyword,
    Name,
    Comment,
    String,
    Error,
    Number,
    Operator,
    Punctuation,
    Generic,
)

# Calibrated palette for White Minimal Swiss UI (vs-light / github-light inspired)
THEME_LIGHT: Dict[Any, Tuple[int, int, int]] = {
    Keyword: (175, 0, 90),          # Magenta / Ruby (#AF005A)
    Keyword.Constant: (0, 92, 197),  # Blue
    Keyword.Declaration: (175, 0, 90),
    Keyword.Namespace: (175, 0, 90),
    Keyword.Type: (0, 92, 197),
    Name.Function: (111, 66, 193),   # Purple (#6F42C1)
    Name.Class: (111, 66, 193),
    Name.Builtin: (0, 92, 197),      # Ocean Blue (#005CC5)
    Name.Variable: (36, 41, 46),     # Charcoal (#24292E)
    String: (34, 134, 58),           # Forest Green (#22863A)
    Number: (0, 92, 197),            # Blue (#005CC5)
    Operator: (215, 58, 73),         # Crimson Red (#D73A49)
    Punctuation: (88, 96, 105),      # Slate Gray (#586069)
    Comment: (106, 115, 125),        # Muted Gray italic (#6A737D)
    Token.Text: (36, 41, 46),        # Default Charcoal
}

# Calibrated palette for Dark Mode (github-dark / monokai inspired)
THEME_DARK: Dict[Any, Tuple[int, int, int]] = {
    Keyword: (255, 123, 114),        # Coral Pink (#FF7B72)
    Keyword.Constant: (121, 192, 255), # Cyan Blue (#79C0FF)
    Keyword.Declaration: (255, 123, 114),
    Keyword.Namespace: (255, 123, 114),
    Keyword.Type: (121, 192, 255),
    Name.Function: (210, 168, 255),  # Violet (#D2A8FF)
    Name.Class: (210, 168, 255),
    Name.Builtin: (121, 192, 255),
    Name.Variable: (230, 237, 243),  # Off-white (#E6EDF3)
    String: (165, 214, 167),         # Mint Green (#A5D6A7)
    Number: (121, 192, 255),
    Operator: (255, 123, 114),
    Punctuation: (139, 148, 158),
    Comment: (139, 148, 158),
    Token.Text: (230, 237, 243),
}


def get_token_color(token_type: Any, is_dark: bool = False) -> Tuple[int, int, int]:
    """Resolves hierarchical token type to an RGB tuple."""
    theme = THEME_DARK if is_dark else THEME_LIGHT
    default_color = (230, 237, 243) if is_dark else (36, 41, 46)

    curr = token_type
    while curr:
        if curr in theme:
            return theme[curr]
        curr = curr.parent
    return default_color


class CodeRun:
    def __init__(self, text: str, color: Tuple[int, int, int], token_type: Any):
        self.text = text
        self.color = color
        self.token_type = token_type


class CodeLine:
    def __init__(self, line_num: int, runs: List[CodeRun], raw_text: str):
        self.line_num = line_num
        self.runs = runs
        self.raw_text = raw_text


def tokenize_code(
    code_text: str,
    language: str = "python",
    is_dark: bool = False,
    char_limit: Optional[int] = None
) -> Tuple[List[CodeLine], Optional[Tuple[int, int]]]:
    """
    Tokenizes code into line-based styled runs.
    If char_limit is specified, only code[:char_limit] is tokenized,
    and returns (lines, cursor_position=(line_idx, char_in_line)).
    """
    if char_limit is not None:
        trimmed_code = code_text[:char_limit]
    else:
        trimmed_code = code_text

    try:
        lexer = get_lexer_by_name(language)
    except Exception:
        lexer = PythonLexer()

    tokens = list(pygments.lex(trimmed_code, lexer))

    lines: List[CodeLine] = []
    current_runs: List[CodeRun] = []
    current_raw = []
    line_no = 1

    for token_type, val in tokens:
        # Split tokens that contain newlines
        parts = val.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                lines.append(CodeLine(line_no, current_runs, "".join(current_raw)))
                current_runs = []
                current_raw = []
                line_no += 1
            if part:
                col = get_token_color(token_type, is_dark=is_dark)
                current_runs.append(CodeRun(part, col, token_type))
                current_raw.append(part)

    # Append trailing line if exists or if trailing newline
    lines.append(CodeLine(line_no, current_runs, "".join(current_raw)))

    # Determine cursor position
    cursor_pos = None
    if char_limit is not None and char_limit < len(code_text):
        last_line_idx = max(0, len(lines) - 1)
        last_line_len = len(lines[last_line_idx].raw_text)
        cursor_pos = (last_line_idx, last_line_len)
    elif char_limit is not None and char_limit >= len(code_text):
        last_line_idx = max(0, len(lines) - 1)
        last_line_len = len(lines[last_line_idx].raw_text)
        cursor_pos = (last_line_idx, last_line_len)

    return lines, cursor_pos
