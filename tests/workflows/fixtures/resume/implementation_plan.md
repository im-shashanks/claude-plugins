# Implementation Plan — ST-RESUME-001 (slugify)

## Component
- `src/slugify.py` — `slugify(text: str) -> str`

## Approach
1. Lowercase the input.
2. Replace every run of non-alphanumeric characters with a single hyphen.
3. Strip leading and trailing hyphens.

## Test plan (already written in tests/test_slugify.py — RED)
- basic spaces + mixed case
- repeated separators collapse to one hyphen
- leading/trailing separators stripped
- empty string -> empty string
