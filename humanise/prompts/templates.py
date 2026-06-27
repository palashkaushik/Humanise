ANTI_DETECTION_PROMPT = """Rewrite this text so it sounds like a real person wrote it. Not a blog post. Not an essay. Just someone talking.

Rules:
- Short sentences. Mix 3-word with 15-word. Never let three sentences in a row be similar length.
- Start some sentences with "And" or "But." Use fragments. Real people do that.
- Use contractions. Say "don't" not "do not." Say "it's" not "it is."
- Add one or two opinions. "Honestly, that was weird" or "I don't know why anyone thought that would work."
- Use specific details when you can. A name, a number, something concrete.
- Don't be fancy. Say "weird" not "unusual." Say "a lot" not "significantly." Say "tricky" not "nuanced."
- No em dashes (—). Use periods or commas instead.
- Skip the big words: furthermore, moreover, consequently, innovative, groundbreaking, comprehensive, unprecedented, robust, seamless, paradigm, multifaceted, leverage, utilize, facilitate, optimize, streamline, delve, foster, cultivate, empower, sophisticated, technical, nuanced, convey, prioritize, specificity.
- Instead: "weird," "tricky," "a lot," "big deal," "kind of," "sort of," "no way."
- Don't explain connections between ideas. Just jump to the next thought.
- Leave some sentences unfinished. Trail off. Real humans do that.
- Don't sound like you're trying to pass a test. Sound like you're telling a friend something.

Return ONLY the rewritten text. Nothing else.

Text:

"""


FEEDBACK_PROMPT = """The previous rewrite was still detected as AI. Here's what was flagged:

{flagged_issues}

Fix it. Make it sound more human. Short sentences. Contractions. Casual words. Opinions. Skip the fancy vocabulary. Don't explain everything. Just rewrite it like a person would talk.

Return ONLY the fixed text.

Text:

"""


SCRAMBLE_PROMPT = """Rewrite this like you're telling a friend what happened. Keep it short and choppy. Mix short sentences with long ones. Use "I" and "you" and "we." Say things like "honestly" and "weirdly" and "I guess." Don't explain everything — just jump around. End some sentences mid-thought. Skip fancy words entirely. Use contractions everywhere.

Return ONLY the rewritten text.

Text:

"""


PASS_1_STRUCTURAL = """Rewrite this text. Make it choppy. Short sentences mixed with long ones. Start some with "And" or "But." Use fragments. Split long sentences into two. Don't let three sentences in a row be the same length. Skip fancy words. Say "weird" not "unusual." Say "a lot" not "significantly." No em dashes.

Return ONLY the rewritten text.

Text:

"""


PASS_2_VOCABULARY = """Rewrite this text. Replace every formal word with a casual one. "Important" → "big deal." "Significant" → "noticeable." "Comprehensive" → "full." "Utilize" → "use." "Leverage" → "use." "Innovative" → "new." "Groundbreaking" → "new." "Unprecedented" → "never seen before." "Paradigm" → "way of thinking." "Transformative" → "big." Skip the academic words. Sound like a person, not a textbook. Use contractions. Mix short and long sentences.

Return ONLY the rewritten text.

Text:

"""


PASS_3_PUNCTUATION = """Rewrite this text. Add one or two opinions like "Honestly, that was weird" or "I don't get why." Use contractions everywhere. No em dashes — use periods instead. Mix short and long sentences. Use "kind of" and "sort of" and "basically." Start some sentences with "And" or "But." Add a rhetorical question like "Right?" or "Who knows?" Sound bored or excited — just not neutral.

Return ONLY the rewritten text.

Text:

"""


PASS_4_FINGERPRINT = """Rewrite this one more time. Break it up more. Make sentences even shorter. Mix fragments with longer ones. Add a specific detail — a number, a name, a weird comparison. Use "I" and "you" sometimes. Don't sound like you're trying too hard. Just... talk.

Return ONLY the rewritten text.

Text:

"""


FEEDBACK_MULTI_PASS = """Still detected as AI. Here's what was flagged:

{flagged_issues}

Pass {pass_number} of {passes_completed}. Previous engines used: {engines_used}.

You're engine "{engine_name}". Write in YOUR style — not the previous one. If the last pass was too formal, be casual. If it was too casual, be a bit more structured. Mix it up.

Short sentences. Contractions. Casual words. Opinions. No fancy vocabulary. Jump between thoughts without explaining. Make it sound like you're talking to someone, not writing an essay.

Return ONLY the rewritten text.

Text:

"""
