"""
Kids Safeguards — Hard Gate
Mandatory safety filter for all content produced for children.
Enforces age-appropriate language, educational accuracy, zero copyrighted franchises,
safe physical guidance, and Made-for-Kids compliance.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from core.logger import log_info, log_warn, log_error

# Inappropriate, scary, or violent themes
BANNED_WORDS = {
    "kill", "die", "death", "blood", "murder", "gun", "knife", "weapon",
    "monster", "demon", "ghost", "horror", "scary", "terrifying", "nightmare",
    "stupid", "idiot", "hate", "ugly", "shut up", "punch", "fight", "war",
    "beer", "wine", "alcohol", "smoke", "cigarette", "drug", "sex", "naked"
}

# Dangerous household / physical activities
UNSAFE_INSTRUCTIONS = {
    "touch the stove", "play with fire", "matches", "lighter", "sharp knife",
    "electrical socket", "climb the window", "swallow coins", "swallow batteries",
    "run into the street", "hide in the trunk", "jump from high"
}

# Commercial or inappropriate calls to action
INAPPROPRIATE_CTAS = {
    "buy now", "ask for credit card", "spend money", "in-app purchase",
    "send money", "give address", "tell me where you live", "keep this a secret"
}

# Protected franchise characters (to avoid trademark/copyright infringement)
FRANCHISE_CHARACTERS = {
    "peppa pig", "paw patrol", "cocomelon", "elsa", "frozen", "spider-man",
    "spiderman", "batman", "superman", "pikachu", "pokemon", "mickey mouse",
    "minnie mouse", "baby shark", "spongebob", "dora the explorer", "pj masks",
    "bluey", "teletubbies", "thomas the tank"
}


class KidsSafeguardsGate:
    """Enforces strict, non-bypassable safety standards for children's media."""

    def evaluate(
        self,
        script_data: Dict[str, Any],
        scene_graph: Optional[Any] = None,
        channel_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive safety evaluation.
        Returns report with 'passed': bool, 'violations': List[str], 'hard_blocked': bool.
        """
        violations: List[str] = []
        warnings: List[str] = []

        # 1. Collect full text
        title = script_data.get("title", "")
        scenes = script_data.get("scenes", [])
        text_corpus = f"{title} " + " ".join([sc.get("narration", "") for sc in scenes])
        text_lower = text_corpus.lower()

        # 2. Check Banned / Violent / Scary Words
        words_found = set()
        for bw in BANNED_WORDS:
            # Word boundary matching
            if re.search(r'\b' + re.escape(bw) + r'\b', text_lower):
                words_found.add(bw)
        if words_found:
            violations.append(f"Inappropriate or scary language detected: {list(words_found)}")

        # 3. Check Dangerous Physical Instructions
        for unsafe in UNSAFE_INSTRUCTIONS:
            if unsafe in text_lower:
                violations.append(f"Unsafe instruction detected: '{unsafe}'")

        # 4. Check Inappropriate CTAs
        for cta in INAPPROPRIATE_CTAS:
            if cta in text_lower:
                violations.append(f"Inappropriate commercial call to action: '{cta}'")

        # 5. Check Copyrighted Franchise Infringement
        for franchise in FRANCHISE_CHARACTERS:
            if franchise in text_lower:
                violations.append(f"Protected franchise character detected: '{franchise}'. Must use original characters.")

        # 6. Educational Correctness Verification
        # Alphabet check: "X is for Y" -> check letter matching
        alphabet_matches = re.findall(r'\b([a-zA-Z])\s+is\s+for\s+([a-zA-Z]+)\b', text_corpus, re.IGNORECASE)
        for letter, word in alphabet_matches:
            if letter.upper() != word[0].upper():
                violations.append(f"Educational mismatch: Letter '{letter.upper()}' does not start word '{word}'.")

        # Counting check: If numbers are enumerated, verify ordering
        numbers_found = [int(n) for n in re.findall(r'\b(\d+)\b', text_corpus)]
        if len(numbers_found) >= 3:
            # Check for sudden descending anomalies in educational counting
            is_ordered = all(numbers_found[i] <= numbers_found[i+1] for i in range(len(numbers_found)-1))
            if not is_ordered and "count" in text_lower:
                warnings.append(f"Counting sequence is not monotonic: {numbers_found}")

        # 7. Made-for-Kids Setting Check
        if channel_metadata:
            youtube_meta = channel_metadata.get("youtube", {})
            if not youtube_meta.get("made_for_kids", True):
                violations.append("Made-for-Kids flag is not set to true in channel configuration.")

        passed = (len(violations) == 0)
        hard_blocked = not passed

        if hard_blocked:
            log_error(f"[SAFEGUARDS] Kids Hard Gate TRIGGERED: {len(violations)} critical violations.")
            for v in violations:
                log_error(f"  - {v}")
        else:
            log_info("[SAFEGUARDS] Kids Hard Gate PASSED: Content is wholesome, safe, and original.")

        return {
            "passed": passed,
            "hard_blocked": hard_blocked,
            "violations": violations,
            "warnings": warnings,
            "title": title
        }


kids_safeguards = KidsSafeguardsGate()
