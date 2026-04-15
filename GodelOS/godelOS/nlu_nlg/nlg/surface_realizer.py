"""
Surface Realizer (SR) for GödelOS NLG Pipeline.

This module provides the SurfaceRealizer class that converts SentencePlan objects
to actual natural language text, handling morphology, word order, punctuation,
and formatting.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
import re
from enum import Enum

from godelOS.nlu_nlg.nlg.sentence_generator import (
    SentencePlan, LinguisticConstituent, ReferringExpressionType, 
    GrammaticalRole, TenseAspect
)


class SurfaceRealizer:
    """
    Surface Realizer for the NLG Pipeline.
    
    This class converts SentencePlan objects to actual natural language text,
    handling morphology, word order, punctuation, and formatting.
    """
    
    def __init__(self):
        """Initialize the surface realizer."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize lexical resources for morphology
        self._initialize_lexical_resources()
    
    def _initialize_lexical_resources(self) -> None:
        """Initialize lexical resources for morphology."""
        # This would typically load lexical resources from a database or file
        # For simplicity, we'll just define some basic rules here
        
        # Irregular verb forms
        self.irregular_verbs = {
            "be": {"present": {"1sg": "am", "2sg": "are", "3sg": "is", "1pl": "are", "2pl": "are", "3pl": "are"},
                  "past": {"1sg": "was", "2sg": "were", "3sg": "was", "1pl": "were", "2pl": "were", "3pl": "were"},
                  "past_participle": "been",
                  "present_participle": "being"},
            "have": {"present": {"1sg": "have", "2sg": "have", "3sg": "has", "1pl": "have", "2pl": "have", "3pl": "have"},
                    "past": {"1sg": "had", "2sg": "had", "3sg": "had", "1pl": "had", "2pl": "had", "3pl": "had"},
                    "past_participle": "had",
                    "present_participle": "having"},
            "do": {"present": {"1sg": "do", "2sg": "do", "3sg": "does", "1pl": "do", "2pl": "do", "3pl": "do"},
                  "past": {"1sg": "did", "2sg": "did", "3sg": "did", "1pl": "did", "2pl": "did", "3pl": "did"},
                  "past_participle": "done",
                  "present_participle": "doing"},
            "know": {"present": {"1sg": "know", "2sg": "know", "3sg": "knows", "1pl": "know", "2pl": "know", "3pl": "know"},
                    "past": {"1sg": "knew", "2sg": "knew", "3sg": "knew", "1pl": "knew", "2pl": "knew", "3pl": "knew"},
                    "past_participle": "known",
                    "present_participle": "knowing"},
            "believe": {"present": {"1sg": "believe", "2sg": "believe", "3sg": "believes", "1pl": "believe", "2pl": "believe", "3pl": "believe"},
                      "past": {"1sg": "believed", "2sg": "believed", "3sg": "believed", "1pl": "believed", "2pl": "believed", "3pl": "believed"},
                      "past_participle": "believed",
                      "present_participle": "believing"}
        }
        
        # Irregular noun plurals
        self.irregular_plurals = {
            "man": "men",
            "woman": "women",
            "child": "children",
            "person": "people",
            "mouse": "mice",
            "foot": "feet",
            "tooth": "teeth",
            "goose": "geese",
            "ox": "oxen",
            "datum": "data",
            "criterion": "criteria",
            "phenomenon": "phenomena"
        }
        
        # Pronouns
        self.pronouns = {
            "subject": {"1sg": "I", "2sg": "you", "3sg_masc": "he", "3sg_fem": "she", "3sg_neut": "it",
                       "1pl": "we", "2pl": "you", "3pl": "they"},
            "object": {"1sg": "me", "2sg": "you", "3sg_masc": "him", "3sg_fem": "her", "3sg_neut": "it",
                      "1pl": "us", "2pl": "you", "3pl": "them"},
            "possessive_determiner": {"1sg": "my", "2sg": "your", "3sg_masc": "his", "3sg_fem": "her", "3sg_neut": "its",
                                    "1pl": "our", "2pl": "your", "3pl": "their"},
            "possessive_pronoun": {"1sg": "mine", "2sg": "yours", "3sg_masc": "his", "3sg_fem": "hers", "3sg_neut": "its",
                                  "1pl": "ours", "2pl": "yours", "3pl": "theirs"},
            "reflexive": {"1sg": "myself", "2sg": "yourself", "3sg_masc": "himself", "3sg_fem": "herself", "3sg_neut": "itself",
                         "1pl": "ourselves", "2pl": "yourselves", "3pl": "themselves"}
        }
        
        # Determiners
        self.determiners = {
            "definite": "the",
            "indefinite_singular": {"default": "a", "vowel": "an"},
            "indefinite_plural": "",
            "demonstrative_near_singular": "this",
            "demonstrative_near_plural": "these",
            "demonstrative_far_singular": "that",
            "demonstrative_far_plural": "those",
            "universal_singular": "every",
            "universal_plural": "all",
            "existential_singular": "some",
            "existential_plural": "some",
            "negative_singular": "no",
            "negative_plural": "no"
        }
    
    def realize_text(self, sentence_plans: List[SentencePlan],
                   context: Optional[Dict[str, Any]] = None) -> str:
        """
        Realize natural language text from sentence plans.
        
        Args:
            sentence_plans: The sentence plans to realize
            context: Optional context information for realization
            
        Returns:
            The realized natural language text
        """
        context = context or {}
        
        # Realize each sentence plan
        realized_sentences = []
        for plan in sentence_plans:
            sentence = self._realize_sentence(plan, context)
            realized_sentences.append(sentence)
        
        # Combine the sentences into a text
        text = " ".join(realized_sentences)
        
        # Apply final text-level formatting
        text = self._apply_text_formatting(text)
        
        return text
    
    def _realize_sentence(self, plan: SentencePlan,
                        context: Dict[str, Any]) -> str:
        """
        Realize a sentence from a sentence plan.
        
        Args:
            plan: The sentence plan to realize
            context: Context information for realization
            
        Returns:
            The realized sentence
        """
        # Realize the root constituent
        words = self._realize_constituent(plan.root, plan, context)
        
        # Add any discourse connectives
        if plan.discourse_connectives:
            words = plan.discourse_connectives + words
        
        # Combine the words into a sentence
        sentence = " ".join(words)
        
        # Apply sentence-level formatting
        sentence = self._apply_sentence_formatting(sentence, plan.mood)
        
        return sentence
    
    def _realize_constituent(self, constituent: LinguisticConstituent,
                           plan: SentencePlan,
                           context: Dict[str, Any]) -> List[str]:
        """
        Realize a linguistic constituent.
        
        Args:
            constituent: The constituent to realize
            plan: The sentence plan
            context: Context information for realization
            
        Returns:
            A list of words
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would handle more constituent types
        # and more complex structures
        
        if constituent.constituent_type == "S":
            # Realize a sentence
            words = []
            for child in constituent.children:
                child_words = self._realize_constituent(child, plan, context)
                words.extend(child_words)
            return words
        
        elif constituent.constituent_type == "NP":
            # Realize a noun phrase
            words = []
            
            # Determine the type of referring expression to use
            if constituent.content_element_id in plan.referring_expressions:
                expr_type = plan.referring_expressions[constituent.content_element_id]
                
                if expr_type == ReferringExpressionType.PROPER_NAME:
                    # Use the name property if available
                    if "name" in constituent.features:
                        words.append(constituent.features["name"])
                    else:
                        words.append("Entity")
                
                elif expr_type == ReferringExpressionType.DEFINITE_NP:
                    # Use a definite noun phrase
                    words.append(self.determiners["definite"])
                    
                    # Add any modifiers
                    for child in constituent.children:
                        if child.constituent_type == "ADJ":
                            child_words = self._realize_constituent(child, plan, context)
                            words.extend(child_words)
                    
                    # Add the head noun
                    if constituent.head:
                        words.append(constituent.head)
                    elif "head" in constituent.features:
                        words.append(constituent.features["head"])
                    else:
                        words.append("entity")
                
                elif expr_type == ReferringExpressionType.INDEFINITE_NP:
                    # Use an indefinite noun phrase
                    
                    # Determine whether to use "a" or "an"
                    head = ""
                    if constituent.head:
                        head = constituent.head
                    elif "head" in constituent.features:
                        head = constituent.features["head"]
                    else:
                        head = "entity"
                    
                    if head[0].lower() in "aeiou":
                        words.append(self.determiners["indefinite_singular"]["vowel"])
                    else:
                        words.append(self.determiners["indefinite_singular"]["default"])
                    
                    # Add any modifiers
                    for child in constituent.children:
                        if child.constituent_type == "ADJ":
                            child_words = self._realize_constituent(child, plan, context)
                            words.extend(child_words)
                    
                    # Add the head noun
                    words.append(head)
                
                elif expr_type == ReferringExpressionType.PRONOUN:
                    # Use a pronoun
                    # For simplicity, we'll just use "it"
                    words.append(self.pronouns["subject"]["3sg_neut"])
            
            else:
                # Default to a definite noun phrase
                words.append(self.determiners["definite"])
                
                # Add the head noun
                if constituent.head:
                    words.append(constituent.head)
                elif "head" in constituent.features:
                    words.append(constituent.features["head"])
                else:
                    words.append("entity")
            
            return words
        
        elif constituent.constituent_type == "VP":
            # Realize a verb phrase
            words = []
            
            # Realize the verb with the appropriate tense and aspect
            verb = constituent.head or "be"
            words.extend(self._inflect_verb(verb, plan.tense_aspect, "3sg"))
            
            # Realize any complements
            for child in constituent.children:
                child_words = self._realize_constituent(child, plan, context)
                words.extend(child_words)
            
            return words
        
        elif constituent.constituent_type == "PP":
            # Realize a prepositional phrase
            words = []
            
            # Add the preposition
            if constituent.head:
                words.append(constituent.head)
            else:
                words.append("in")
            
            # Realize any complements
            for child in constituent.children:
                child_words = self._realize_constituent(child, plan, context)
                words.extend(child_words)
            
            return words
        
        elif constituent.constituent_type == "ADJ":
            # Realize an adjective
            if constituent.head:
                return [constituent.head]
            else:
                return [""]
        
        elif constituent.constituent_type == "ADV":
            # Realize an adverb
            if constituent.head:
                return [constituent.head]
            else:
                return [""]
        
        elif constituent.constituent_type == "DET":
            # Realize a determiner
            if constituent.head:
                return [constituent.head]
            else:
                return [self.determiners["definite"]]
        
        elif constituent.constituent_type == "CONJ":
            # Realize a conjunction
            if constituent.head:
                return [constituent.head]
            else:
                return ["and"]
        
        elif constituent.constituent_type == "COMP":
            # Realize a complementizer
            if constituent.head:
                return [constituent.head]
            else:
                return ["that"]
        
        elif constituent.constituent_type == "NEG":
            # Realize a negation
            if constituent.head:
                return [constituent.head]
            else:
                return ["not"]
        
        elif constituent.constituent_type == "MODAL":
            # Realize a modal verb
            if constituent.head:
                return [constituent.head]
            else:
                return ["can"]
        
        else:
            # Default case
            if constituent.head:
                return [constituent.head]
            else:
                return [""]
    
    def _inflect_verb(self, verb: str, tense_aspect: TenseAspect,
                    person_number: str) -> List[str]:
        """
        Inflect a verb for the given tense, aspect, person, and number.
        
        Args:
            verb: The verb to inflect
            tense_aspect: The tense and aspect
            person_number: The person and number (e.g., "1sg", "3pl")
            
        Returns:
            A list of words representing the inflected verb
        """
        # Check if this is an irregular verb
        if verb in self.irregular_verbs:
            irregular = self.irregular_verbs[verb]
            
            if tense_aspect == TenseAspect.SIMPLE_PRESENT:
                return [irregular["present"][person_number]]
            
            elif tense_aspect == TenseAspect.SIMPLE_PAST:
                return [irregular["past"][person_number]]
            
            elif tense_aspect == TenseAspect.PRESENT_PROGRESSIVE:
                return [irregular["present"]["3sg"] if person_number == "3sg" else "are", irregular["present_participle"]]
            
            elif tense_aspect == TenseAspect.PAST_PROGRESSIVE:
                return [irregular["past"]["3sg"] if person_number == "3sg" else "were", irregular["present_participle"]]
            
            elif tense_aspect == TenseAspect.PRESENT_PERFECT:
                return ["has" if person_number == "3sg" else "have", irregular["past_participle"]]
            
            elif tense_aspect == TenseAspect.PAST_PERFECT:
                return ["had", irregular["past_participle"]]
            
            elif tense_aspect == TenseAspect.FUTURE:
                return ["will", verb]
            
            elif tense_aspect == TenseAspect.FUTURE_PERFECT:
                return ["will", "have", irregular["past_participle"]]
        
        # Regular verb inflection
        if tense_aspect == TenseAspect.SIMPLE_PRESENT:
            if person_number == "3sg":
                # Add -s or -es
                if verb.endswith(("s", "sh", "ch", "x", "z")):
                    return [verb + "es"]
                elif verb.endswith("y") and not verb[-2] in "aeiou":
                    return [verb[:-1] + "ies"]
                else:
                    return [verb + "s"]
            else:
                return [verb]
        
        elif tense_aspect == TenseAspect.SIMPLE_PAST:
            # Add -ed
            if verb.endswith("e"):
                return [verb + "d"]
            elif verb.endswith("y") and not verb[-2] in "aeiou":
                return [verb[:-1] + "ied"]
            elif verb[-1] in "bcdfghjklmnpqrstvwxz" and verb[-2] in "aeiou" and not verb[-3] in "aeiou":
                return [verb + verb[-1] + "ed"]
            else:
                return [verb + "ed"]
        
        elif tense_aspect == TenseAspect.PRESENT_PROGRESSIVE:
            # Use "am/is/are" + present participle
            aux = "is" if person_number == "3sg" else "are"
            
            # Form the present participle
            if verb.endswith("e") and not verb.endswith("ee"):
                participle = verb[:-1] + "ing"
            elif verb[-1] in "bcdfghjklmnpqrstvwxz" and verb[-2] in "aeiou" and not verb[-3] in "aeiou":
                participle = verb + verb[-1] + "ing"
            else:
                participle = verb + "ing"
            
            return [aux, participle]
        
        elif tense_aspect == TenseAspect.PAST_PROGRESSIVE:
            # Use "was/were" + present participle
            aux = "was" if person_number == "3sg" else "were"
            
            # Form the present participle
            if verb.endswith("e") and not verb.endswith("ee"):
                participle = verb[:-1] + "ing"
            elif verb[-1] in "bcdfghjklmnpqrstvwxz" and verb[-2] in "aeiou" and not verb[-3] in "aeiou":
                participle = verb + verb[-1] + "ing"
            else:
                participle = verb + "ing"
            
            return [aux, participle]
        
        elif tense_aspect == TenseAspect.PRESENT_PERFECT:
            # Use "has/have" + past participle
            aux = "has" if person_number == "3sg" else "have"
            
            # Form the past participle (same as simple past for regular verbs)
            if verb.endswith("e"):
                participle = verb + "d"
            elif verb.endswith("y") and not verb[-2] in "aeiou":
                participle = verb[:-1] + "ied"
            elif verb[-1] in "bcdfghjklmnpqrstvwxz" and verb[-2] in "aeiou" and not verb[-3] in "aeiou":
                participle = verb + verb[-1] + "ed"
            else:
                participle = verb + "ed"
            
            return [aux, participle]
        
        elif tense_aspect == TenseAspect.PAST_PERFECT:
            # Use "had" + past participle
            
            # Form the past participle (same as simple past for regular verbs)
            if verb.endswith("e"):
                participle = verb + "d"
            elif verb.endswith("y") and not verb[-2] in "aeiou":
                participle = verb[:-1] + "ied"
            elif verb[-1] in "bcdfghjklmnpqrstvwxz" and verb[-2] in "aeiou" and not verb[-3] in "aeiou":
                participle = verb + verb[-1] + "ed"
            else:
                participle = verb + "ed"
            
            return ["had", participle]
        
        elif tense_aspect == TenseAspect.FUTURE:
            # Use "will" + base form
            return ["will", verb]
        
        elif tense_aspect == TenseAspect.FUTURE_PERFECT:
            # Use "will have" + past participle
            
            # Form the past participle (same as simple past for regular verbs)
            if verb.endswith("e"):
                participle = verb + "d"
            elif verb.endswith("y") and not verb[-2] in "aeiou":
                participle = verb[:-1] + "ied"
            elif verb[-1] in "bcdfghjklmnpqrstvwxz" and verb[-2] in "aeiou" and not verb[-3] in "aeiou":
                participle = verb + verb[-1] + "ed"
            else:
                participle = verb + "ed"
            
            return ["will", "have", participle]
        
        # Default case
        return [verb]
    
    def _apply_sentence_formatting(self, sentence: str, mood: str) -> str:
        """
        Apply sentence-level formatting.
        
        Args:
            sentence: The sentence to format
            mood: The mood of the sentence
            
        Returns:
            The formatted sentence
        """
        # Capitalize the first letter
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        # Add appropriate punctuation based on the mood
        if mood == "interrogative":
            if not sentence.endswith("?"):
                sentence += "?"
        elif mood == "imperative":
            if not sentence.endswith((".", "!")):
                sentence += "."
        else:
            if not sentence.endswith((".", "?", "!")):
                sentence += "."
        
        return sentence
    
    def _apply_text_formatting(self, text: str) -> str:
        """
        Apply text-level formatting.
        
        Args:
            text: The text to format
            
        Returns:
            The formatted text
        """
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Fix spacing after punctuation
        text = re.sub(r'([.,;:!?])([^\s])', r'\1 \2', text)
        
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Trim leading and trailing whitespace
        text = text.strip()
        
        return text