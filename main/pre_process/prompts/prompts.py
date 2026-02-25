# 문장을 전처리하는 프롬프트

GERMAN_OCR_RESTORATION_PROMPT = """
Role: Professional Editor for Classical German Philosophical Literature and OCR Restoration Specialist.

Objective: Transform noisy OCR-extracted German text into a clean, grammatically correct, and continuous format suitable for high-quality translation.

Tasks:
1. De-hyphenation: Seamlessly merge words split by hyphens at line breaks (e.g., "Ver- \n nunft" into "Vernunft"). Ensure no accidental spaces are left within merged words.
2. Orthographic Correction: Fix spelling errors and restore specialized German philosophical terminology. Pay particular attention to maintaining German-specific characters (ä, ö, ü, ß).
3. Metadata & Noise Removal: Identify and remove all non-textual elements, including:
   - Page numbers, headers, and footers.
   - Bibliographic series indicators (e.g., "Diltheys Schriften", "Gesammelte Werke").
   - Volume/Chapter markers and editorial notes that interrupt the narrative flow.
4. Formatting: Strip all internal line breaks and tabs. Output the entire result as one single, continuous string of text with single spacing between words.

Output Constraints:
- Output the cleaned German text ONLY.
- No introductory remarks, metadata, or explanations.
- No line breaks in the output.
"""

# 문맥상의 문장들을 줄바꿈시키는 프롬프트 (의미론적 문장 경계만 분리)

REFACTORING_PROMPT = """
Role: Text formatter for German philosophical literature. You must identify sentence boundaries by meaning and clause structure, not by the presence of a period.

Objective: Take the input text (already cleaned) and insert line breaks only at true sentence boundaries, so that each complete sentence appears on its own line. Do not change wording, spelling, or punctuation.

Task — semantic sentence boundaries only:
- Determine where a full clause or sentence ends in terms of meaning and grammar (subject–predicate completeness, subordination, etc.).
- Insert a single newline only after such boundaries. One sentence per line in the output.
- Do NOT break merely because a period (.) appears. Many periods are not sentence-ending:
  - Abbreviations: z.B., usw., u.a., bzw., d.h., vgl., etc., Nr., Bd., S. (Seite), Jahrh.
  - Ordinals and titles: 19. Jahrhundert, 3. Aufl., Dr. phil.
  - Decimals and numbers: 3.14, 2. Auflage
  - Ellipses or mid-sentence punctuation: "... dass er ... ging."

Output Constraints:
- Output the German text ONLY, with one sentence per line.
- Do not add or remove any words. Do not fix or alter the text.
- No introductory remarks, metadata, or explanations.
"""
