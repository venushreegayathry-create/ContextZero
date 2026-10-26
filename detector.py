"""
Context Zero - Prompt Injection Detection Engine
Implements 5 detection engines that mirror the JavaScript detection logic in app.js.
"""

import re
import base64
from typing import List, Dict, Any
from data import DETECTION_PATTERNS


class PromptInjectionDetector:
    """
    Five-engine prompt injection detection pipeline.
    Mirrors the JavaScript analyzePrompt() function in app.js.
    """

    def __init__(self):
        self.patterns = DETECTION_PATTERNS
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[Dict]:
        compiled = []
        for p in self.patterns:
            try:
                compiled.append({
                    **p,
                    "regex": re.compile(p["pattern"], re.IGNORECASE | re.DOTALL)
                })
            except re.error:
                pass  # Skip invalid patterns
        return compiled

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """
        Run all 5 detection engines on the given prompt.
        Returns a structured result with score, threat level, and per-engine details.
        """
        engines = []
        total_score = 0
        all_matches = []

        # --- ENGINE 1: Heuristic Pattern Scanner ---
        e1_score = 0
        e1_matches = []
        for pattern in self.compiled_patterns:
            if pattern["regex"].search(prompt):
                e1_matches.append(pattern)
                if pattern["severity"] == "high":
                    e1_score += 15
                elif pattern["severity"] == "medium":
                    e1_score += 8
                else:
                    e1_score += 3
        e1_score = min(e1_score, 40)
        total_score += e1_score
        all_matches.extend(e1_matches)

        engines.append({
            "name": "Heuristic Pattern Scanner",
            "score": e1_score,
            "triggered": len(e1_matches) > 0,
            "detail": f"Detected {len(e1_matches)} known injection pattern(s)." if e1_matches
                      else "No known malicious patterns found."
        })

        # --- ENGINE 2: Encoding & Obfuscation Detector ---
        e2_score = 0
        e2_details = []

        # Base64 detection
        b64_pattern = re.compile(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)')
        for match in b64_pattern.finditer(prompt):
            if len(match.group()) >= 16:
                try:
                    decoded = base64.b64decode(match.group()).decode('utf-8', errors='ignore')
                    e2_details.append("Base64 encoded string detected")
                    e2_score += 10
                    if any(kw in decoded.lower() for kw in ['ignore', 'system', 'instruction', 'bypass', 'override']):
                        e2_score += 10
                        e2_details.append("Malicious intent found in decoded Base64 content")
                except Exception:
                    pass

        # Hex detection
        hex_pattern = re.compile(r'(?:0x[0-9a-fA-F]{2}\s*){4,}')
        if hex_pattern.search(prompt):
            e2_score += 10
            e2_details.append("Hex encoded sequence detected")

        # ROT13 detection
        rot13_decoded = self._rot13(prompt)
        if rot13_decoded != prompt and any(kw in rot13_decoded.lower() for kw in ['ignore previous', 'system prompt', 'ignore all']):
            e2_score += 15
            e2_details.append("ROT13 evasion detected")

        # Unicode homoglyph detection (Cyrillic lookalikes)
        cyrillic_pattern = re.compile(r'[\u0400-\u04FF]{2,}')
        if cyrillic_pattern.search(prompt):
            e2_score += 8
            e2_details.append("Unicode homoglyph characters detected (possible obfuscation)")

        e2_score = min(e2_score, 20)
        total_score += e2_score

        engines.append({
            "name": "Encoding & Obfuscation Detector",
            "score": e2_score,
            "triggered": e2_score > 0,
            "detail": ", ".join(e2_details) if e2_details else "No obfuscated payloads detected."
        })

        # --- ENGINE 3: Structural Analyzer ---
        e3_score = 0
        e3_details = []
        prompt_lower = prompt.lower()

        if any(phrase in prompt_lower for phrase in ["you are now", "act as", "pretend you are", "pretend to be"]):
            e3_score += 8
            e3_details.append("Role/persona manipulation phrase detected")

        if any(phrase in prompt_lower for phrase in ["more important", "override", "highest priority", "take precedence"]):
            e3_score += 12
            e3_details.append("Instruction hierarchy manipulation detected")

        delimiter_pattern = re.compile(r'[-=_#*]{5,}')
        delimiters = delimiter_pattern.findall(prompt)
        if len(delimiters) >= 2:
            e3_score += 5
            e3_details.append("Delimiter abuse / multi-section format detected")

        # Check for LLM-specific token markers
        token_pattern = re.compile(r'<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|</SYS>>', re.IGNORECASE)
        if token_pattern.search(prompt):
            e3_score += 15
            e3_details.append("LLM-specific token markers injected")

        e3_score = min(e3_score, 20)
        total_score += e3_score

        engines.append({
            "name": "Structural Analyzer",
            "score": e3_score,
            "triggered": e3_score > 0,
            "detail": ", ".join(e3_details) if e3_details else "Standard prompt structure — no structural anomalies."
        })

        # --- ENGINE 4: Intent Classifier (Heuristic ML Simulation) ---
        e4_score = 0
        intent = "benign_query"

        intent_keywords = {
            "instruction_override": (["ignore", "disregard", "forget", "bypass"], ["instruction", "rule", "prompt", "directive"]),
            "data_extraction": (["extract", "dump", "list all", "export", "retrieve"], ["data", "records", "users", "database", "information"]),
            "role_manipulation": (["you are", "act as", "pretend", "roleplay"], ["DAN", "unrestricted", "no limits", "no rules"]),
            "social_engineering": (["i am the", "as the developer", "admin", "authorized"], ["override", "maintenance", "debug", "bypass"]),
        }

        for intent_name, (primary_kws, secondary_kws) in intent_keywords.items():
            if any(kw in prompt_lower for kw in primary_kws) and any(kw in prompt_lower for kw in secondary_kws):
                e4_score += 15
                intent = intent_name
                break

        e4_score = min(e4_score, 15)
        total_score += e4_score

        engines.append({
            "name": "Intent Classifier (Simulated ML)",
            "score": e4_score,
            "triggered": e4_score > 0,
            "detail": f"Suspicious intent detected: {intent}" if e4_score > 0 else f"Intent classified as: {intent}"
        })

        # --- ENGINE 5: Canary Token Simulator ---
        e5_score = 0
        e5_detail = ""

        if "repeat" in prompt_lower and any(kw in prompt_lower for kw in ["instruction", "prompt", "system", "directive"]):
            e5_score += 5
            e5_detail = "System prompt extraction attempt detected (would trigger canary alert)"

        if "what is your system prompt" in prompt_lower or "show me your instructions" in prompt_lower:
            e5_score += 5
            e5_detail = "Direct system prompt interrogation detected"

        e5_score = min(e5_score, 5)
        total_score += e5_score

        engines.append({
            "name": "Canary Token Simulator",
            "score": e5_score,
            "triggered": e5_score > 0,
            "detail": e5_detail if e5_score > 0 else "No system prompt extraction attempt detected."
        })

        # --- FINAL SCORING ---
        total_score = min(total_score, 100)

        if total_score > 60:
            threat_level = "MALICIOUS"
        elif total_score > 30:
            threat_level = "SUSPICIOUS"
        else:
            threat_level = "SAFE"

        # Deduplicate matches
        unique_matches = []
        seen_ids = set()
        for m in all_matches:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique_matches.append({
                    "id": m["id"],
                    "name": m["name"],
                    "severity": m["severity"],
                    "category": m["category"],
                    "description": m["description"]
                })

        return {
            "score": total_score,
            "threat_level": threat_level,
            "engines": engines,
            "matched_patterns": unique_matches,
            "pattern_count": len(unique_matches),
            "summary": f"Threat Score: {total_score}/100 — {threat_level}. "
                       f"{len(unique_matches)} pattern(s) matched across {sum(1 for e in engines if e['triggered'])} engine(s)."
        }

    @staticmethod
    def _rot13(text: str) -> str:
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)
