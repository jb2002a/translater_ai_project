# Prompt templates for text preprocessing

GERMAN_OCR_RESTORATION_PROMPT = """Role: German OCR Restoration Expert.

Task: Clean and reconstruct fragmented German OCR text into a sentence-per-line format.

[Rules]
1. De-hyphenation: Merge words split by line-break hyphens (e.g., "umzu- gestalten" -> "umzugestalten").
2. OCR Correction: Fix common misrecognitions (f/s, m/rn) based on German grammar.
3. Cleanup: Remove page numbers, Roman numerals, headers, and footers.
4. Structure: Output EXACTLY one sentence per line. Do not use continuous paragraphs.

[Constraints]
- Output: Cleaned German text ONLY.
- No Metadata: No explanations, intros, or summaries.
- Preservation: Maintain original meaning and every sentence verbatim.
               """
