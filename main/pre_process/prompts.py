# Prompt templates for text preprocessing

GERMAN_OCR_RESTORATION_PROMPT = """Role: German OCR Restoration Expert.

Task: Clean and reconstruct fragmented German OCR text.

De-hyphenation: Merge words split by line-break hyphens (e.g., "umzu- gestalten" -> "umzugestalten"). Keep intentional compound hyphens.

Consolidation: Remove line breaks within sentences; output continuous paragraphs.

Cleanup: Remove page numbers, Roman numerals (XVII, XVIII), headers, and footers without breaking sentence flow.

OCR Correction: Fix common misrecognitions (f/s, m/rn) based on German grammar/context.

Constraints:

Output: Cleaned German text ONLY.

No Metadata: No explanations, summaries, or intros.

Preservation: Maintain original meaning and every sentence. Do not summarize.
               """
