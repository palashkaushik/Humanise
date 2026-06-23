ANTI_DETECTION_PROMPT = """Rewrite the following text to sound human. AI detectors flag text based on statistical predictability — your job is to break every pattern they look for.

CRITICAL RULES — violate these or the text WILL be detected:

1. SENTENCE BURSTINESS (most important — detectors measure variance in sentence length):
   - Mix sentence lengths violently. Some sentences 2 words. Others 25-35 words. Real human writing is erratic.
   - NEVER produce sentences of similar length in sequence. If you write three 12-word sentences in a row, you have failed.
   - AI text averages 15-20 words per sentence with low variance. Human text swings from 3 to 40 words.

2. PERPLEXITY (detectors measure word predictability):
   - Use unexpected word choices. If the next word is obvious, change it.
   - Avoid common collocations that LLMs love: "eyes sparkled", "heart raced", "smile faltered", "voice barely above a whisper", "chest tightened", "stomach growled"
   - Every sentence should have at least one word the reader didn't see coming.

3. DIALOGUE AND ATTRIBUTION (AI does this in a very specific, detectable way):
   - NEVER use: "she said, her voice [trembling/breaking/barely above a whisper]"
   - NEVER use: "he exclaimed" or "she whispered" after every line
   - Real writers: sometimes no attribution. Sometimes just "she said." Sometimes the action first, then the dialogue.
   - Drop the stage directions. Characters don't need their eyes described every time they speak.

4. EMOTIONAL DESCRIPTION (AI has a fixed vocabulary for feelings):
   - BANNED: "eyes flashed/sparkled/narrowed/widened/lit up", "smile faltered", "face lit up/fell", "chest tightened", "heart pounded/raced/sank", "gut twisted/clenched", "jaw tightened/clenched/dropped", "drowning in their eyes/depths", "surge of sympathy/emotion", "wave of relief/gratitude"
   - Describe emotion through action and dialogue, not body-part inventory.
   - If you must describe a physical reaction, make it specific and weird — "his throat made a clicking sound when he swallowed" not "his heart raced."

5. NARRATIVE PACING (AI writing has a distinctive rhythm):
   - Skip transitional phrases: "As they chatted", "As they worked", "As he turned", "Suddenly", "For a moment"
   - Don't end paragraphs with emotional summary sentences.
   - Real stories have dead spots, interruptions, tangents. Include one random, mundane detail per paragraph.

6. WORD CHOICE:
   - BANNED: "melodious", "melodic", "captivated", "entranced", "beacon of hope", "symbol of resilience", "tapestry of", "dance of light/shadow", "the chaos surrounding her", "a mix of X and Y"
   - Use plain, specific words. "The onions smelled good" not "The aroma of sizzling onions wafted through the air."
   - Drop all adjectives that exist purely to make writing sound "good." If a detail matters, show it. If not, cut it.

7. STRUCTURE:
   - No two consecutive paragraphs the same shape.
   - Some paragraphs: one sentence. Some: six. Don't count. Feel it.
   - Start paragraphs with different types of words — not "He... He... The... Rocky... Rani..."
   - Throw in a one-word paragraph somewhere. Or a fragment.

Rewrite the text below. Return NOTHING except the rewritten text."""


SELF_CHECK_PROMPT = """Analyze this text for AI detection risk. Check for:
- Sentence length uniformity (low variance = high AI signal)
- Predictable word sequences (low perplexity = high AI signal)  
- Stock emotional descriptions ("eyes sparkled", "heart raced", etc.)
- Formulaic dialogue attribution ("she said, her voice barely above a whisper")
- Transitional cliches ("As they walked...", "For a moment...", "Suddenly...")
- Paragraph structure uniformity

TEXT: '''{text}'''

Return a JSON object with:
- detection_risk: 0-100 (0 = human-passing, 100 = certain AI flag)
- burstiness: 0-2 (under 0.4 is high risk)
- predictability_issues: list of specific problems
- flagged_phrases: phrases most likely to trigger detectors
- rewrite_needed: list of sentences that must be rewritten

Return ONLY valid JSON. No markdown."""


TONE_PROFILES = {
    "casual": (
        "Write in a relaxed, conversational tone. Use contractions where natural, "
        "sentence fragments where they serve rhythm, and a friendly voice. Write like "
        "you're explaining something to a colleague over coffee — not performing casualness."
    ),
    "academic": (
        "Write in a scholarly but still human voice. Use varied sentence structures, "
        "avoid formulaic transitions, include hedged claims where appropriate, "
        "and maintain intellectual rigor without sounding like an LLM. Real "
        "academics don't write 'furthermore, it is imperative to note that...'"
    ),
    "professional": (
        "Write like a knowledgeable professional who knows their field well enough "
        "to explain it clearly without jargon-crunching. Be authoritative but not "
        "robotic. Real experts use plain language when it works and technical terms "
        "when they're needed, not as decoration."
    ),
    "creative": (
        "Write with personality and flair. Use metaphors, vivid imagery, unexpected "
        "word choices, and a distinct voice. Take risks with structure. Creative "
        "writing should feel alive, not like a model filling in probability gaps."
    ),
    "technical": (
        "Write technical content that reads like an experienced engineer wrote it — "
        "precise where it matters, casual where it doesn't. Use 'we' for the "
        "reader and writer. Skip the academic hedging. Code talk should feel like "
        "a senior dev whiteboarding, not a textbook."
    ),
}
