"""Wrapper around Amazon Comprehend synchronous APIs used in the demo.

Features implemented (all synchronous):
 - Sentiment
 - Entities
 - Key Phrases
 - Syntax
 - Dominant Language
 - PII Entities
 - Targeted Sentiment

"Categories" in the spec does not map to a single synchronous API unless a
custom classifier or topic modeling job is configured (which would require
asynchronous jobs & S3). For this simple demo, we approximate "categories" by
aggregating entity types & key phrase POS tags to provide a lightweight
categorization feel without extra AWS setup.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter, defaultdict
from typing import Any, Dict, List
import boto3
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComprehendResult:
    sentiment: Dict[str, Any]
    entities: List[Dict[str, Any]]
    key_phrases: List[Dict[str, Any]]
    syntax_tokens: List[Dict[str, Any]]
    languages: List[Dict[str, Any]]
    pii_entities: List[Dict[str, Any]]
    targeted_sentiment: Dict[str, Any]
    derived_categories: Dict[str, Any]


class ComprehendService:
    def __init__(self, region: str | None = None):
        # Region: if not provided, boto3 will fall back on environment / config.
        self.client = boto3.client("comprehend", region_name=region)

    def analyze(self, text: str) -> ComprehendResult:
        # Call all needed synchronous APIs. Failures logged but won't break entire response.
        def safe_call(name: str, func):
            try:
                return func()
            except Exception as e:  # noqa: BLE001 broad but acceptable for demo per spec
                logger.warning("%s call failed: %s", name, e)
                return None

        sentiment = safe_call("detect_sentiment", lambda: self.client.detect_sentiment(Text=text, LanguageCode="en"))
        # We detect dominant language first to pick the first language for other APIs, but spec keeps simple -> assume English.
        languages = safe_call("detect_dominant_language", lambda: self.client.detect_dominant_language(Text=text))
        entities = safe_call("detect_entities", lambda: self.client.detect_entities(Text=text, LanguageCode="en"))
        key_phrases = safe_call("detect_key_phrases", lambda: self.client.detect_key_phrases(Text=text, LanguageCode="en"))
        syntax = safe_call("detect_syntax", lambda: self.client.detect_syntax(Text=text, LanguageCode="en"))
        pii = safe_call("detect_pii_entities", lambda: self.client.detect_pii_entities(Text=text, LanguageCode="en"))
        targeted = safe_call("detect_targeted_sentiment", lambda: self.client.detect_targeted_sentiment(Text=text, LanguageCode="en"))

        derived = self._derive_categories(entities, key_phrases, syntax)

        return ComprehendResult(
            sentiment=sentiment or {},
            entities=(entities or {}).get("Entities", []) if entities else [],
            key_phrases=(key_phrases or {}).get("KeyPhrases", []) if key_phrases else [],
            syntax_tokens=(syntax or {}).get("SyntaxTokens", []) if syntax else [],
            languages=(languages or {}).get("Languages", []) if languages else [],
            pii_entities=(pii or {}).get("Entities", []) if pii else [],
            targeted_sentiment=targeted or {},
            derived_categories=derived,
        )

    @staticmethod
    def _derive_categories(entities_resp: Dict[str, Any] | None, kp_resp: Dict[str, Any] | None, syntax_resp: Dict[str, Any] | None) -> Dict[str, Any]:
        categories: Dict[str, Any] = {}
        # Entity type counts
        if entities_resp and "Entities" in entities_resp:
            type_counts = Counter(e.get("Type") for e in entities_resp["Entities"])
            categories["entity_type_counts"] = dict(type_counts)
        # Key phrase length buckets
        if kp_resp and "KeyPhrases" in kp_resp:
            length_buckets = {"short": 0, "medium": 0, "long": 0}
            for kp in kp_resp["KeyPhrases"]:
                length = len(kp.get("Text", "").split())
                if length <= 2:
                    length_buckets["short"] += 1
                elif length <= 5:
                    length_buckets["medium"] += 1
                else:
                    length_buckets["long"] += 1
            categories["key_phrase_length_buckets"] = length_buckets
        # Part of speech distribution
        if syntax_resp and "SyntaxTokens" in syntax_resp:
            pos_counts = Counter(tok.get("PartOfSpeech", {}).get("Tag") for tok in syntax_resp["SyntaxTokens"])
            categories["part_of_speech_counts"] = dict(pos_counts)
        return categories


def curate_for_ui(result: ComprehendResult) -> Dict[str, Any]:
    """Produce a pared-down, human-friendly structure for the template."""
    sentiment = {} if not result.sentiment else {
        "overall": result.sentiment.get("Sentiment"),
        "scores": result.sentiment.get("SentimentScore", {}),
    }
    # Entities curated: show text, type, score
    entities = [
        {
            "text": e.get("Text"),
            "type": e.get("Type"),
            "score": round(e.get("Score", 0.0), 4),
        }
        for e in result.entities[:50]
    ]  # cap to keep UI simple
    key_phrases = [kp.get("Text") for kp in result.key_phrases[:30]]
    pos_freq = result.derived_categories.get("part_of_speech_counts", {})
    pos_top = sorted(pos_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    languages = [
        {"lang": l.get("LanguageCode"), "score": round(l.get("Score", 0.0), 4)}
        for l in result.languages
    ]
    pii_entities = [
        {
            "type": e.get("Type"),
            "score": round(e.get("Score", 0.0), 4),
            "begin": e.get("BeginOffset"),
            "end": e.get("EndOffset"),
        }
        for e in result.pii_entities[:50]
    ]
    targeted_mentions = []
    if result.targeted_sentiment:
        for ent in result.targeted_sentiment.get("Entities", [])[:50]:
            targeted_mentions.append(
                {
                    "text": ent.get("Text"),
                    "type": ent.get("Type"),
                    "sentiment": ent.get("Sentiment"),
                    "confidence": round(ent.get("SentimentScore", {}).get(ent.get("Sentiment", ""), 0.0), 4),
                }
            )
    return {
        "sentiment": sentiment,
        "entities": entities,
        "key_phrases": key_phrases,
        "languages": languages,
        "pii": pii_entities,
        "targeted": targeted_mentions,
        "entity_type_counts": result.derived_categories.get("entity_type_counts", {}),
        "key_phrase_length_buckets": result.derived_categories.get("key_phrase_length_buckets", {}),
        "pos_top": pos_top,
    }
