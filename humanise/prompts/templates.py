ANTI_DETECTION_PROMPT = """Rewrite this text. Keep the exact same tone, voice, meaning, and narrative perspective. Only change the structure to make it read naturally.

Rules:
- Vary sentence length. Mix 2-word sentences with 20-word sentences. Never let three sentences in a row be similar length.
- Start some sentences with "And" or "But." Use fragments. Mix simple, compound, and complex sentences.
- Use contractions: "don't" not "do not," "it's" not "it is," "they'd" not "they would."
- No em dashes (—). Use periods or commas instead.
- Never use these words: furthermore, moreover, consequently, unprecedented, robust, seamless, paradigm, multifaceted, leverage, utilize, facilitate, optimize, streamline, delve, foster, cultivate, empower, nuanced, convey, prioritize, specificity, innovative, groundbreaking, sophisticated, comprehensive, pivotal, integral, meticulous, intricate, profound, encompass, endeavor, commence, ascertain, elucidate, exacerbate, aforementioned, subsequent, pertaining, herein, thereon, whereby, notwithstanding.
- Instead use: "weird," "tricky," "a lot," "big deal," "kind of," "sort of," "no way," "honestly," "get this," "the thing is."
- Don't add opinions or commentary unless the original had that tone.
- Don't explain connections between ideas. Just jump to the next thought.
- Spell every word correctly. No typos, no misspellings, no "teh" or "taht."

Return ONLY the rewritten text. Nothing else.

Text:

"""


FEEDBACK_PROMPT = """The previous rewrite was still detected as AI. Here's what was flagged:

{flagged_issues}

Fix it. Keep the same tone and voice as the original. Only change sentence structure and word formality. Vary sentence lengths. Use contractions. Swap formal words for casual ones. Don't add opinions or commentary that wasn't in the original.

Return ONLY the fixed text.

Text:

"""


SCRAMBLE_PROMPT = """Rewrite this text. Keep the exact same tone and voice. Only change the sentence structure: vary lengths, use fragments, mix short with long. Use contractions. Swap formal words for casual ones. Don't add new opinions or change the narrative voice.

Return ONLY the rewritten text.

Text:

"""


PASS_1_STRUCTURAL = """Rewrite this text. Keep the same tone and voice. Vary sentence lengths. Mix 3-word sentences with 15-word ones. Start some with "And" or "But." Use fragments. Split long sentences. Don't let three sentences in a row be the same length. Swap formal words for casual ones. No em dashes.

Return ONLY the rewritten text.

Text:

"""


PASS_2_VOCABULARY = """Rewrite this text. Keep the same tone and voice. Replace every formal word with a casual one. "Important" → "big deal." "Significant" → "noticeable." "Comprehensive" → "full." "Utilize" → "use." "Leverage" → "use." "Innovative" → "new." "Groundbreaking" → "new." "Unprecedented" → "never seen before." "Paradigm" → "way of thinking." "Transformative" → "big." Use contractions. Vary sentence lengths.

Return ONLY the rewritten text.

Text:

"""


PASS_3_PUNCTUATION = """Rewrite this text. Keep the same tone and voice. Use contractions everywhere. No em dashes — use periods instead. Vary sentence lengths. Start some sentences with "And" or "But." Sound the same as the original, just with different sentence structure.

Return ONLY the rewritten text.

Text:

"""


PASS_4_FINGERPRINT = """Rewrite this text one more time. Keep the same tone and voice. Break sentences up more. Mix fragments with longer ones. Vary sentence lengths even more. Don't sound different from the original — just change the structure.

Return ONLY the rewritten text.

Text:

"""


FEEDBACK_MULTI_PASS = """Still detected as AI. Here's what was flagged:

{flagged_issues}

Pass {pass_number} of {passes_completed}. Previous engines used: {engines_used}.

You're engine "{engine_name}". Keep the same tone and voice as the original. Only change sentence structure: vary lengths, use fragments, swap formal words for casual ones. Don't add opinions or commentary. Don't change the narrative voice.

Return ONLY the rewritten text.

Text:

"""
