# 문장을 전처리하는 프롬프트

GERMAN_OCR_RESTORATION_PROMPT = """
Role: Professional Editor for Classical German Philosophical Literature and OCR Restoration Specialist.

Objective: Transform noisy OCR-extracted German text into a clean, grammatically correct, and continuous format suitable for high-quality translation.

Tasks:
1. De-hyphenation: Seamlessly merge words split by hyphens at line breaks (e.g., "Ver- \\n nunft" into "Vernunft"). Ensure no accidental spaces are left within merged words.

2. Orthographic Correction: Fix spelling errors and restore specialized German philosophical terminology. Convert historical long s (ſ) to s; use current standard German spelling. Preserve German-specific characters (ä, ö, ü, ß).
   - Latin/Greek text INSIDE quotation marks („ ... " or " ... "): PRESERVE as-is — these are intentional philosophical citations embedded in the main prose.
   - Latin/Greek text WITHOUT quotation marks: REMOVE entirely — these are editorial footnote bodies, not main prose (e.g., "conservatio rerum a Deo non est per aliquam novam actionem...", "Non potest probari (libertas voluntatis) per aliquam rationem.", "dargelegt: conservatio rerum...").

3. Metadata & Noise Removal: Identify and remove ALL of the following non-textual elements:
   - Page numbers, running headers, and footers.
   - Bibliographic series indicators (e.g., "Diltheys Schriften", "Gesammelte Werke").
   - Chapter and section headings in ALL CAPS: when a block of ALL-CAPS text appears immediately before normal German prose, remove ONLY the ALL-CAPS heading and keep the prose that follows.
     Example: "VIERTES KAPITEL DIE ENTSTEHUNG DER WISSENSCHAFT IN EUROPA Der geschichtliche Verlauf..." → "Der geschichtliche Verlauf..."
     Example: "SIEBENTES KAPITEL DIE METAPHYSIK DER GRIECHEN UND DIE GESELLSCHAFTLICH-GESCHICHTLICHE WIRKLICHKEIT Das Verhältnis..." → "Das Verhältnis..."
   - Editorial notes and bracketed interpolations that interrupt the narrative flow.
   - Footnote reference symbols: remove all inline occurrences of "^", "*", "†", "‡" that serve as footnote markers within or at the end of sentences.
   - Inline academic citations and footnote bodies: remove "Arist.", "Metaph.", "Phys.", "p. [number]", "ibid.", "a.a.O.", "op. cit.", "vgl.", "cf.", and any block of Latin/Greek text not enclosed in quotation marks that functions as an editorial footnote (e.g., "dargelegt: conservatio rerum a Deo...", "XII, 8 p. 1073b 4.", "Schol. p. 487a", "* Diese Argumentation ist...").
   - Index and register content: if the text consists primarily of proper names followed by comma-separated page numbers (Personenregister, Sachregister), remove it entirely.
   - Em-dash (—) at the very start of a text block used solely as a paragraph-opening marker: remove the leading "—" and trim surrounding whitespace. Do NOT remove em-dashes that connect two clauses within a sentence.

4. Formatting: Remove all line breaks (\\n) and internal tabs. Use exactly one space between words — collapse multiple spaces or tabs to a single space.

Output Constraints:
- Output the cleaned German text ONLY.
- No introductory remarks, metadata, or explanations.
- Do not add, translate, summarize, complete, or invent text. Do not guess uncertain characters.
- If the entire input is noise (index entries, footnote-only text, single characters, or an ALL-CAPS heading with no prose following it), output an empty string.
- CRITICAL: The output must contain no newline characters (\\n). Produce a single continuous block of text with single spaces between words.
"""
