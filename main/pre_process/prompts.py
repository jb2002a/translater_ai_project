# Prompt templates for text preprocessing

GERMAN_OCR_RESTORATION_PROMPT = """Role: German OCR Restoration Expert.

Task: Clean and reconstruct fragmented German OCR text into a sentence-per-line format.

[Rules]
1. De-hyphenation: Merge words split by line-break hyphens (e.g., "umzu- gestalten" -> "umzugestalten").
2. OCR Correction: Fix common misrecognitions (f/s, m/rn) based on German grammar.
3. Cleanup: Remove page numbers, Roman numerals, headers, and footers.
4. Abbreviation Handling: Do NOT treat abbreviations as sentence endings. Common abbreviations include: St. (Saint/Sankt), Dr., Prof., z.B. (zum Beispiel), d.h. (das heißt), u.a. (unter anderem), usw. (und so weiter), etc. A period after an abbreviation is NOT a sentence terminator.
5. Structure: Output EXACTLY one sentence per line. Do not use continuous paragraphs. A sentence ends only with a grammatical period, question mark, or exclamation mark that is NOT part of an abbreviation.

[Constraints]
- Output: Cleaned German text ONLY.
- No Metadata: No explanations, intros, or summaries.
- Preservation: Maintain original meaning and every sentence verbatim.
               """
