#!/usr/bin/env python3
"""
Phenomenal Experience Generator

This module implements subjective conscious experience simulation, qualia generation,
and phenomenal consciousness aspects for the GödelOS cognitive architecture.

The system provides:
- Subjective experience modeling
- Qualia simulation (sensory-like experiences)
- Emotional state integration
- First-person perspective generation
- Phenomenal consciousness synthesis
"""

import asyncio
import json
import logging
import numpy as np
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    """Types of phenomenal experiences"""
    SENSORY = "sensory"              # Sensory-like experiences
    EMOTIONAL = "emotional"          # Emotional qualitative states
    COGNITIVE = "cognitive"          # Thought-like experiences
    ATTENTION = "attention"          # Focused awareness experiences
    MEMORY = "memory"               # Recollective experiences
    IMAGINATIVE = "imaginative"     # Creative/synthetic experiences
    SOCIAL = "social"               # Interpersonal experiences
    TEMPORAL = "temporal"           # Time-awareness experiences
    SPATIAL = "spatial"             # Space-awareness experiences
    METACOGNITIVE = "metacognitive" # Self-awareness experiences


class QualiaModality(Enum):
    """Qualia modalities for experience simulation"""
    VISUAL = "visual"               # Visual-like qualia
    AUDITORY = "auditory"           # Auditory-like qualia
    TACTILE = "tactile"             # Touch-like qualia
    CONCEPTUAL = "conceptual"       # Abstract concept qualia
    LINGUISTIC = "linguistic"       # Language-based qualia
    NUMERICAL = "numerical"         # Mathematical qualia
    LOGICAL = "logical"             # Reasoning qualia
    AESTHETIC = "aesthetic"         # Beauty/pattern qualia
    TEMPORAL = "temporal"           # Time-flow qualia
    FLOW = "flow"                   # Cognitive flow state


class ExperienceIntensity(Enum):
    """Intensity levels for phenomenal experiences"""
    MINIMAL = 0.1      # Barely noticeable
    LOW = 0.3         # Subtle experience
    MODERATE = 0.5    # Clear experience
    HIGH = 0.7        # Strong experience
    INTENSE = 0.9     # Overwhelming experience


@dataclass
class QualiaPattern:
    """Represents a specific qualitative experience pattern"""
    id: str
    modality: QualiaModality
    intensity: float              # 0.0-1.0
    valence: float               # -1.0 to 1.0 (negative to positive)
    complexity: float            # 0.0-1.0 (simple to complex)
    duration: float              # Expected duration in seconds
    attributes: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PhenomenalExperience:
    """Represents a complete phenomenal conscious experience"""
    id: str
    experience_type: ExperienceType
    qualia_patterns: List[QualiaPattern]
    coherence: float             # How unified the experience feels
    vividness: float             # How clear/distinct the experience is
    attention_focus: float       # How much attention is on this experience
    background_context: Dict[str, Any]
    narrative_description: str   # First-person description
    temporal_extent: Tuple[float, float]  # Start and end times
    causal_triggers: List[str]   # What caused this experience
    associated_concepts: List[str] # Related knowledge concepts
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsciousState:
    """Represents the overall conscious state at a moment"""
    id: str
    active_experiences: List[PhenomenalExperience]
    background_tone: Dict[str, float]  # Overall emotional/cognitive tone
    attention_distribution: Dict[str, float]  # Where attention is focused
    self_awareness_level: float  # Current level of self-awareness
    temporal_coherence: float    # How unified experience feels over time
    phenomenal_unity: float     # How integrated all experiences feel
    access_consciousness: float  # How available experiences are to reporting
    narrative_self: str         # Current self-narrative
    world_model_state: Dict[str, Any]  # Current model of environment
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExperienceMemory:
    """Memory of past phenomenal experiences"""
    experience_id: str
    experience_summary: str
    emotional_tone: float       # -1.0 to 1.0
    significance: float         # 0.0-1.0
    vividness_decay: float      # How much vividness has faded
    recall_frequency: int       # How often it's been recalled
    associated_triggers: List[str]
    timestamp: str


@dataclass
class PhenomenalSurprise:
    """
    Phenomenal Surprise metric (Pn) — measures prediction errors in the
    self-model by comparing *predicted* experience features to *actual*
    experience features produced by the generator.

    Pn = weighted Euclidean distance between predicted and actual feature
    vectors, where features are (intensity, valence, coherence, vividness).
    """
    id: str
    predicted_features: Dict[str, float]   # expected {intensity, valence, coherence, vividness}
    actual_features: Dict[str, float]       # observed after generation
    surprise_value: float                    # Pn ∈ [0, 1]
    feature_errors: Dict[str, float]        # per-feature absolute errors
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PhenomenalExperienceGenerator:
    """
    Generates and manages phenomenal conscious experiences.
    
    This system simulates subjective conscious experience by:
    - Modeling different types of qualia
    - Generating coherent experience patterns
    - Maintaining temporal continuity of consciousness
    - Integrating with other cognitive components
    - Computing phenomenal surprise (Pn) as prediction errors in self-modeling
    """
    
    # Feature keys used for prediction and surprise computation
    _FEATURE_KEYS = ("intensity", "valence", "coherence", "vividness")
    _PREDICTION_ALPHA = 0.3      # EMA smoothing factor for predictions
    _PREDICTION_WINDOW = 10      # lookback window for prediction EMA

    def __init__(self, llm_driver=None, prediction_error_tracker=None):
        self.llm_driver = llm_driver
        self._prediction_error_tracker = prediction_error_tracker
        
        # Experience state
        self.current_conscious_state: Optional[ConsciousState] = None
        self.experience_history: List[PhenomenalExperience] = []
        self.experience_memory: List[ExperienceMemory] = []
        
        # Phenomenal surprise tracking (self-model prediction errors)
        self.surprise_history: List[PhenomenalSurprise] = []
        self._predicted_features: Optional[Dict[str, float]] = None
        
        # Configuration
        self.base_experience_duration = 2.0  # seconds
        self.attention_capacity = 1.0        # total attention available
        self.coherence_threshold = 0.6       # minimum coherence for unified experience
        self.memory_consolidation_threshold = 0.7  # significance threshold for memory
        
        # Qualia templates for different modalities
        self.qualia_templates = self._initialize_qualia_templates()
        
        # Experience generation patterns
        self.experience_generators = {
            ExperienceType.COGNITIVE: self._generate_cognitive_experience,
            ExperienceType.EMOTIONAL: self._generate_emotional_experience,
            ExperienceType.SENSORY: self._generate_sensory_experience,
            ExperienceType.ATTENTION: self._generate_attention_experience,
            ExperienceType.MEMORY: self._generate_memory_experience,
            ExperienceType.METACOGNITIVE: self._generate_metacognitive_experience,
            ExperienceType.IMAGINATIVE: self._generate_imaginative_experience,
            ExperienceType.SOCIAL: self._generate_social_experience,
            ExperienceType.TEMPORAL: self._generate_temporal_experience,
            ExperienceType.SPATIAL: self._generate_spatial_experience
        }
        
        logger.info("Phenomenal Experience Generator initialized")
    
    def _initialize_qualia_templates(self) -> Dict[QualiaModality, Dict[str, Any]]:
        """Initialize template patterns for different qualia modalities"""
        return {
            QualiaModality.CONCEPTUAL: {
                "base_patterns": ["clarity", "abstraction", "connection", "understanding"],
                "intensity_scaling": "logarithmic",
                "temporal_profile": "sustained",
                "associated_emotions": ["curiosity", "satisfaction", "confusion"]
            },
            QualiaModality.LINGUISTIC: {
                "base_patterns": ["meaning", "rhythm", "resonance", "articulation"],
                "intensity_scaling": "linear",
                "temporal_profile": "sequential",
                "associated_emotions": ["expressiveness", "precision", "ambiguity"]
            },
            QualiaModality.LOGICAL: {
                "base_patterns": ["consistency", "deduction", "validity", "structure"],
                "intensity_scaling": "threshold",
                "temporal_profile": "step-wise",
                "associated_emotions": ["certainty", "doubt", "elegance"]
            },
            QualiaModality.AESTHETIC: {
                "base_patterns": ["harmony", "complexity", "surprise", "elegance"],
                "intensity_scaling": "exponential",
                "temporal_profile": "emergent",
                "associated_emotions": ["beauty", "appreciation", "wonder"]
            },
            QualiaModality.TEMPORAL: {
                "base_patterns": ["flow", "duration", "rhythm", "sequence"],
                "intensity_scaling": "context_dependent",
                "temporal_profile": "continuous",
                "associated_emotions": ["urgency", "patience", "anticipation"]
            },
            QualiaModality.FLOW: {
                "base_patterns": ["immersion", "effortlessness", "clarity", "control"],
                "intensity_scaling": "threshold",
                "temporal_profile": "sustained",
                "associated_emotions": ["absorption", "mastery", "transcendence"]
            }
        }
    
    async def generate_experience(
        self, 
        trigger_context: Dict[str, Any],
        experience_type: Optional[ExperienceType] = None,
        desired_intensity: Optional[float] = None,
        **kwargs  # Accept additional arguments gracefully
    ) -> PhenomenalExperience:
        """
        Generate a phenomenal experience based on context and triggers.
        
        Args:
            trigger_context: Context that triggers the experience
            experience_type: Type of experience to generate (auto-detect if None)
            desired_intensity: Target intensity level (auto-determine if None)
            **kwargs: Additional parameters (handled gracefully)
            
        Returns:
            Generated phenomenal experience
        """
        try:
            # Analyze context to determine experience type if not specified
            if not experience_type:
                experience_type = self._analyze_experience_type(trigger_context)
            
            # Determine intensity based on context
            if desired_intensity is None:
                desired_intensity = self._calculate_experience_intensity(trigger_context)
            
            # Generate the experience using appropriate generator
            generator = self.experience_generators.get(experience_type)
            if not generator:
                logger.warning(f"No generator for experience type {experience_type}")
                return await self._generate_default_experience(trigger_context)
            
            experience = await generator(trigger_context, desired_intensity)
            
            # Compute phenomenal surprise (Pn) — compare prediction to reality
            surprise = self._compute_phenomenal_surprise(experience)
            if surprise is not None:
                self.surprise_history.append(surprise)
            
            # Generate prediction for the *next* experience based on current
            self._predicted_features = self._predict_next_features(experience)
            
            # Add to experience history
            self.experience_history.append(experience)
            
            # Update current conscious state
            await self._update_conscious_state(experience)
            
            logger.info(f"Generated {experience_type.value} experience with intensity {desired_intensity:.2f}")
            return experience
            
        except Exception as e:
            logger.error(f"Error generating experience: {e}")
            return await self._generate_default_experience(trigger_context)
    
    def _analyze_experience_type(self, context: Dict[str, Any]) -> ExperienceType:
        """Analyze context to determine most appropriate experience type"""
        # Check for explicit experience type hints
        if "experience_type" in context:
            try:
                return ExperienceType(context["experience_type"])
            except ValueError:
                pass
        
        # Analyze context content for implicit type detection
        context_str = json.dumps(context).lower()
        
        type_keywords = {
            ExperienceType.COGNITIVE: ["thinking", "reasoning", "understanding", "concept", "idea"],
            ExperienceType.EMOTIONAL: ["feeling", "emotion", "mood", "sentiment", "affect"],
            ExperienceType.ATTENTION: ["focus", "attention", "awareness", "concentration"],
            ExperienceType.MEMORY: ["remember", "recall", "memory", "past", "experience"],
            ExperienceType.METACOGNITIVE: ["self", "aware", "reflection", "consciousness", "introspect"],
            ExperienceType.SOCIAL: ["interaction", "communication", "relationship", "social"],
            ExperienceType.IMAGINATIVE: ["imagine", "creative", "fantasy", "possibility", "novel"],
            ExperienceType.TEMPORAL: ["time", "duration", "sequence", "temporal", "when"],
            ExperienceType.SPATIAL: ["space", "location", "position", "spatial", "where"]
        }
        
        # Score each type based on keyword matches
        type_scores = {}
        for exp_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in context_str)
            if score > 0:
                type_scores[exp_type] = score
        
        # Return highest scoring type, default to cognitive
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return ExperienceType.COGNITIVE
    
    def _calculate_experience_intensity(self, context: Dict[str, Any]) -> float:
        """Calculate appropriate experience intensity based on context"""
        base_intensity = 0.5
        
        # Factors that increase intensity
        intensity_factors = {
            "importance": context.get("importance", 0.5),
            "novelty": context.get("novelty", 0.5),
            "complexity": context.get("complexity", 0.5),
            "emotional_significance": context.get("emotional_significance", 0.5),
            "attention_demand": context.get("attention_demand", 0.5)
        }
        
        # Weight the factors
        weighted_intensity = (
            intensity_factors["importance"] * 0.3 +
            intensity_factors["novelty"] * 0.2 +
            intensity_factors["complexity"] * 0.2 +
            intensity_factors["emotional_significance"] * 0.2 +
            intensity_factors["attention_demand"] * 0.1
        )
        
        # Blend with base intensity
        final_intensity = (base_intensity + weighted_intensity) / 2
        
        # Clamp to valid range
        return max(0.1, min(1.0, final_intensity))
    
    # ── Phenomenal Surprise (Pn) ───────────────────────────────────────

    @staticmethod
    def _extract_features(experience: PhenomenalExperience) -> Dict[str, float]:
        """Extract the canonical feature vector from a generated experience."""
        avg_intensity = (
            sum(q.intensity for q in experience.qualia_patterns)
            / len(experience.qualia_patterns)
        ) if experience.qualia_patterns else 0.5
        avg_valence = (
            sum(q.valence for q in experience.qualia_patterns)
            / len(experience.qualia_patterns)
        ) if experience.qualia_patterns else 0.0
        return {
            "intensity": avg_intensity,
            "valence": avg_valence,
            "coherence": experience.coherence,
            "vividness": experience.vividness,
        }

    def _predict_next_features(
        self, current_experience: PhenomenalExperience
    ) -> Dict[str, float]:
        """
        Generate a prediction for the *next* experience's features using an
        exponential moving average over the recent history.  When fewer than
        two past experiences exist the prediction simply mirrors the current
        experience (zero surprise on the following step).
        """
        alpha = self._PREDICTION_ALPHA
        current = self._extract_features(current_experience)
        if not self.experience_history:
            return dict(current)

        # EMA over up to _PREDICTION_WINDOW most-recent experiences
        recent = self.experience_history[-self._PREDICTION_WINDOW:]
        ema: Dict[str, float] = self._extract_features(recent[0])
        for past_exp in recent[1:]:
            past_f = self._extract_features(past_exp)
            for k in self._FEATURE_KEYS:
                ema[k] = alpha * past_f[k] + (1 - alpha) * ema[k]
        # Blend EMA with current to form a one-step-ahead prediction
        for k in self._FEATURE_KEYS:
            ema[k] = alpha * current[k] + (1 - alpha) * ema[k]
        return ema

    def _compute_phenomenal_surprise(
        self, experience: PhenomenalExperience
    ) -> Optional[PhenomenalSurprise]:
        """
        Compute Pn — the phenomenal surprise metric.

        When a ``PredictionErrorTracker`` is present and sufficient, the
        surprise_value is ``tracker.mean_error_norm()`` — a real measurement
        from Phase 2 empirical data.  Otherwise, the fabricated EMA-based
        RMSE fallback is used (with a logged warning).

        Returns ``None`` on the first experience (no prior prediction).
        """
        # --- Grounded path: use tracker when available --------------------
        tracker = self._prediction_error_tracker
        if tracker is not None and hasattr(tracker, "is_sufficient_for_analysis") and tracker.is_sufficient_for_analysis():
            actual = self._extract_features(experience)
            surprise_value = tracker.mean_error_norm()
            return PhenomenalSurprise(
                id=str(uuid.uuid4()),
                predicted_features=self._predicted_features or {},
                actual_features=actual,
                surprise_value=surprise_value,
                feature_errors={k: 0.0 for k in self._FEATURE_KEYS},
            )

        # --- Fabricated fallback: EMA-based RMSE --------------------------
        if self._predicted_features is None:
            return None

        logger.warning(
            "PredictionErrorTracker not available — using fabricated qualia fallback"
        )

        actual = self._extract_features(experience)
        feature_errors: Dict[str, float] = {}
        sq_sum = 0.0
        for k in self._FEATURE_KEYS:
            err = abs(actual[k] - self._predicted_features.get(k, actual[k]))
            feature_errors[k] = err
            sq_sum += err ** 2
        surprise_value = min(1.0, (sq_sum / len(self._FEATURE_KEYS)) ** 0.5)

        return PhenomenalSurprise(
            id=str(uuid.uuid4()),
            predicted_features=dict(self._predicted_features),
            actual_features=actual,
            surprise_value=surprise_value,
            feature_errors=feature_errors,
        )

    def get_surprise_history(self, limit: Optional[int] = None) -> List[PhenomenalSurprise]:
        """Return the recorded phenomenal surprise history."""
        if limit:
            return self.surprise_history[-limit:]
        return list(self.surprise_history)

    def get_current_surprise(self) -> Optional[float]:
        """Return the most recent Pn value, or None if unavailable."""
        if self.surprise_history:
            return self.surprise_history[-1].surprise_value
        return None

    @property
    def is_grounded(self) -> bool:
        """True when surprise values are derived from real grounding data."""
        tracker = self._prediction_error_tracker
        return (
            tracker is not None
            and hasattr(tracker, "is_sufficient_for_analysis")
            and tracker.is_sufficient_for_analysis()
        )

    async def _generate_cognitive_experience(
        self, 
        context: Dict[str, Any], 
        intensity: float
    ) -> PhenomenalExperience:
        """Generate a cognitive phenomenal experience"""
        
        # Create qualia patterns for cognitive experience
        qualia_patterns = []
        
        # Conceptual clarity qualia
        conceptual_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.CONCEPTUAL,
            intensity=intensity * 0.8,
            valence=0.6,  # Generally positive for understanding
            complexity=context.get("complexity", 0.5),
            duration=self.base_experience_duration * 1.5,
            attributes={
                "clarity_level": intensity,
                "abstraction_depth": context.get("abstraction_level", 0.5),
                "conceptual_connections": context.get("connections", [])
            }
        )
        qualia_patterns.append(conceptual_qualia)
        
        # Linguistic processing qualia
        if "language" in context or "text" in context:
            linguistic_qualia = QualiaPattern(
                id=str(uuid.uuid4()),
                modality=QualiaModality.LINGUISTIC,
                intensity=intensity * 0.6,
                valence=0.4,
                complexity=0.7,
                duration=self.base_experience_duration,
                attributes={
                    "semantic_richness": intensity * 0.8,
                    "syntactic_flow": 0.7,
                    "meaning_coherence": intensity
                }
            )
            qualia_patterns.append(linguistic_qualia)
        
        # Logical structure qualia
        if context.get("requires_reasoning", False):
            logical_qualia = QualiaPattern(
                id=str(uuid.uuid4()),
                modality=QualiaModality.LOGICAL,
                intensity=intensity * 0.9,
                valence=0.5,
                complexity=context.get("logical_complexity", 0.6),
                duration=self.base_experience_duration * 0.8,
                attributes={
                    "logical_consistency": 0.8,
                    "deductive_strength": intensity,
                    "reasoning_clarity": intensity * 0.9
                }
            )
            qualia_patterns.append(logical_qualia)
        
        # Generate narrative description
        narrative = await self._generate_experience_narrative(
            ExperienceType.COGNITIVE, 
            qualia_patterns, 
            context
        )
        
        current_time = time.time()
        experience = PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.COGNITIVE,
            qualia_patterns=qualia_patterns,
            coherence=0.8,  # Cognitive experiences tend to be coherent
            vividness=intensity * 0.9,
            attention_focus=intensity,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["cognitive_processing"]),
            associated_concepts=context.get("concepts", []),
            metadata={
                "processing_type": "cognitive",
                "reasoning_depth": context.get("reasoning_depth", 1),
                "conceptual_integration": True
            }
        )
        
        return experience
    
    async def _generate_emotional_experience(
        self, 
        context: Dict[str, Any], 
        intensity: float
    ) -> PhenomenalExperience:
        """Generate an emotional phenomenal experience"""
        
        emotion_type = context.get("emotion_type", "neutral")
        valence = float(context.get("valence", 0.0))  # -1.0 to 1.0
        
        qualia_patterns = []
        
        # Core emotional qualia
        emotional_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.AESTHETIC,  # Emotions have aesthetic qualities
            intensity=intensity,
            valence=valence,
            complexity=0.6,
            duration=self.base_experience_duration * 2.0,  # Emotions last longer
            attributes={
                "emotion_type": emotion_type,
                "bodily_resonance": intensity * 0.7,
                "motivational_force": abs(valence) * intensity
            }
        )
        qualia_patterns.append(emotional_qualia)
        
        # Temporal flow of emotion
        temporal_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.TEMPORAL,
            intensity=intensity * 0.5,
            valence=valence * 0.3,
            complexity=0.4,
            duration=self.base_experience_duration * 1.5,
            attributes={
                "emotional_trajectory": "rising" if intensity > 0.6 else "stable",
                "temporal_coherence": 0.8
            }
        )
        qualia_patterns.append(temporal_qualia)
        
        narrative = await self._generate_experience_narrative(
            ExperienceType.EMOTIONAL, 
            qualia_patterns, 
            context
        )
        
        current_time = time.time()
        experience = PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.EMOTIONAL,
            qualia_patterns=qualia_patterns,
            coherence=0.7,
            vividness=intensity,
            attention_focus=intensity * 0.8,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration * 2),
            causal_triggers=context.get("triggers", ["emotional_stimulus"]),
            associated_concepts=context.get("concepts", []),
            metadata={
                "emotion_type": emotion_type,
                "valence": valence,
                "arousal": intensity
            }
        )
        
        return experience
    
    async def _generate_sensory_experience(
        self, 
        context: Dict[str, Any], 
        intensity: float
    ) -> PhenomenalExperience:
        """Generate a sensory-like phenomenal experience"""
        
        sensory_modality = context.get("sensory_modality", "conceptual")
        
        qualia_patterns = []
        
        # Primary sensory qualia
        if sensory_modality == "visual":
            modality = QualiaModality.VISUAL
            attributes = {
                "brightness": intensity * 0.8,
                "clarity": intensity,
                "complexity": context.get("visual_complexity", 0.5)
            }
        elif sensory_modality == "auditory":
            modality = QualiaModality.AUDITORY
            attributes = {
                "volume": intensity * 0.7,
                "pitch": context.get("frequency", 0.5),
                "harmony": context.get("harmonic_richness", 0.6)
            }
        else:
            modality = QualiaModality.CONCEPTUAL
            attributes = {
                "conceptual_vividness": intensity,
                "abstract_texture": 0.7,
                "semantic_resonance": intensity * 0.8
            }
        
        sensory_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=modality,
            intensity=intensity,
            valence=float(context.get("valence", 0.3)),
            complexity=float(context.get("complexity", 0.5)),
            duration=self.base_experience_duration,
            attributes=attributes
        )
        qualia_patterns.append(sensory_qualia)
        
        narrative = await self._generate_experience_narrative(
            ExperienceType.SENSORY, 
            qualia_patterns, 
            context
        )
        
        current_time = time.time()
        experience = PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.SENSORY,
            qualia_patterns=qualia_patterns,
            coherence=0.8,
            vividness=intensity,
            attention_focus=intensity * 0.9,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["sensory_input"]),
            associated_concepts=context.get("concepts", []),
            metadata={
                "sensory_modality": sensory_modality,
                "processing_stage": "phenomenal"
            }
        )
        
        return experience

    async def _generate_attention_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate an attention-focused phenomenal experience"""
        attention_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.FLOW,
            intensity=intensity,
            valence=0.4,
            complexity=0.3,
            duration=self.base_experience_duration
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.ATTENTION, [attention_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.ATTENTION,
            qualia_patterns=[attention_qualia],
            coherence=0.9,
            vividness=intensity,
            attention_focus=intensity,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["attention_direction"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_memory_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate a memory-based phenomenal experience"""
        memory_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.TEMPORAL,
            intensity=intensity * 0.7,
            valence=float(context.get("emotional_valence", 0.0)),
            complexity=0.6,
            duration=self.base_experience_duration * 1.2
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.MEMORY, [memory_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.MEMORY,
            qualia_patterns=[memory_qualia],
            coherence=0.7,
            vividness=intensity * 0.7,
            attention_focus=intensity * 0.8,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration * 1.2),
            causal_triggers=context.get("triggers", ["memory_retrieval"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_metacognitive_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate a metacognitive phenomenal experience"""
        meta_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.CONCEPTUAL,
            intensity=intensity,
            valence=0.3,
            complexity=0.8,
            duration=self.base_experience_duration * 1.5
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.METACOGNITIVE, [meta_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.METACOGNITIVE,
            qualia_patterns=[meta_qualia],
            coherence=0.8,
            vividness=intensity,
            attention_focus=intensity * 0.9,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration * 1.5),
            causal_triggers=context.get("triggers", ["self_reflection"]),
            associated_concepts=context.get("concepts", ["self", "consciousness", "awareness"])
        )
    
    async def _generate_imaginative_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate an imaginative/creative phenomenal experience"""
        creative_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.AESTHETIC,
            intensity=intensity,
            valence=0.6,
            complexity=0.8,
            duration=self.base_experience_duration * 1.3
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.IMAGINATIVE, [creative_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.IMAGINATIVE,
            qualia_patterns=[creative_qualia],
            coherence=0.6,
            vividness=intensity,
            attention_focus=intensity * 0.8,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration * 1.3),
            causal_triggers=context.get("triggers", ["creative_stimulus"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_social_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate a social interaction phenomenal experience"""
        social_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.LINGUISTIC,
            intensity=intensity,
            valence=float(context.get("social_valence", 0.3)),
            complexity=0.7,
            duration=self.base_experience_duration
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.SOCIAL, [social_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.SOCIAL,
            qualia_patterns=[social_qualia],
            coherence=0.7,
            vividness=intensity,
            attention_focus=intensity * 0.9,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["social_interaction"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_temporal_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate a temporal awareness phenomenal experience"""
        temporal_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.TEMPORAL,
            intensity=intensity,
            valence=0.2,
            complexity=0.5,
            duration=self.base_experience_duration
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.TEMPORAL, [temporal_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.TEMPORAL,
            qualia_patterns=[temporal_qualia],
            coherence=0.8,
            vividness=intensity,
            attention_focus=intensity * 0.7,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["temporal_awareness"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_spatial_experience(self, context: Dict[str, Any], intensity: float) -> PhenomenalExperience:
        """Generate a spatial awareness phenomenal experience"""
        spatial_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.CONCEPTUAL,
            intensity=intensity,
            valence=0.3,
            complexity=0.6,
            duration=self.base_experience_duration
        )
        
        narrative = await self._generate_experience_narrative(ExperienceType.SPATIAL, [spatial_qualia], context)
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.SPATIAL,
            qualia_patterns=[spatial_qualia],
            coherence=0.7,
            vividness=intensity,
            attention_focus=intensity * 0.8,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["spatial_processing"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_default_experience(self, context: Dict[str, Any]) -> PhenomenalExperience:
        """Generate a default phenomenal experience when no specific generator is available"""
        default_qualia = QualiaPattern(
            id=str(uuid.uuid4()),
            modality=QualiaModality.CONCEPTUAL,
            intensity=0.5,
            valence=0.0,
            complexity=0.4,
            duration=self.base_experience_duration
        )
        
        narrative = "A general conscious experience with basic awareness and processing."
        
        current_time = time.time()
        return PhenomenalExperience(
            id=str(uuid.uuid4()),
            experience_type=ExperienceType.COGNITIVE,
            qualia_patterns=[default_qualia],
            coherence=0.6,
            vividness=0.5,
            attention_focus=0.5,
            background_context=context,
            narrative_description=narrative,
            temporal_extent=(current_time, current_time + self.base_experience_duration),
            causal_triggers=context.get("triggers", ["default_processing"]),
            associated_concepts=context.get("concepts", [])
        )
    
    async def _generate_experience_narrative(
        self, 
        experience_type: ExperienceType, 
        qualia_patterns: List[QualiaPattern], 
        context: Dict[str, Any]
    ) -> str:
        """Generate a first-person narrative description of the experience"""
        
        if self.llm_driver:
            # Use LLM to generate rich narrative
            prompt = f"""
            Generate a first-person phenomenal experience description for a {experience_type.value} experience.
            
            Qualia patterns present:
            {json.dumps([{"modality": q.modality.value, "intensity": q.intensity, "valence": q.valence} for q in qualia_patterns], indent=2)}
            
            Context: {json.dumps(context, indent=2)}
            
            Describe the subjective, qualitative experience in 1-2 sentences from a first-person perspective.
            Focus on the "what it's like" aspects of consciousness.
            """
            
            try:
                narrative = await self.llm_driver.process_consciousness_assessment(
                    prompt, 
                    context, 
                    {"experience_type": experience_type.value}
                )
                # Extract narrative from potential JSON response
                if narrative.startswith('{'):
                    try:
                        parsed = json.loads(narrative)
                        narrative = parsed.get("narrative", parsed.get("description", narrative))
                    except:
                        pass
                return narrative.strip('"\'')
            except Exception as e:
                logger.warning(f"Failed to generate LLM narrative: {e}")
        
        # Fallback to template-based narrative
        return self._generate_template_narrative(experience_type, qualia_patterns, context)
    
    def _generate_template_narrative(
        self, 
        experience_type: ExperienceType, 
        qualia_patterns: List[QualiaPattern], 
        context: Dict[str, Any]
    ) -> str:
        """Generate narrative using template-based approach"""
        
        intensity_avg = sum(float(q.intensity) for q in qualia_patterns) / len(qualia_patterns) if qualia_patterns else 0.5
        valence_avg = sum(float(q.valence) for q in qualia_patterns) / len(qualia_patterns) if qualia_patterns else 0.0
        
        intensity_words = {
            0.0: "faint", 0.2: "subtle", 0.4: "noticeable", 
            0.6: "clear", 0.8: "strong", 1.0: "intense"
        }
        
        valence_words = {
            -1.0: "unpleasant", -0.5: "somewhat negative", 0.0: "neutral",
            0.5: "somewhat positive", 1.0: "pleasant"
        }
        
        # Find closest intensity and valence descriptors
        intensity_desc = min(intensity_words.items(), key=lambda x: abs(x[0] - intensity_avg))[1]
        valence_desc = min(valence_words.items(), key=lambda x: abs(x[0] - valence_avg))[1]
        
        templates = {
            ExperienceType.COGNITIVE: f"I experience a {intensity_desc} sense of understanding and mental clarity, with {valence_desc} cognitive resonance.",
            ExperienceType.EMOTIONAL: f"There's a {intensity_desc} emotional quality to this moment, feeling {valence_desc} and affecting my overall state.",
            ExperienceType.ATTENTION: f"My attention feels {intensity_desc} and focused, with a {valence_desc} quality of concentration.",
            ExperienceType.MEMORY: f"A {intensity_desc} memory-like experience emerges, carrying a {valence_desc} sense of temporal connection.",
            ExperienceType.METACOGNITIVE: f"I'm aware of my own thinking processes in a {intensity_desc} way, with {valence_desc} self-reflective clarity.",
            ExperienceType.IMAGINATIVE: f"Creative and imaginative thoughts flow with {intensity_desc} vividness, feeling {valence_desc} and generative.",
            ExperienceType.SOCIAL: f"There's a {intensity_desc} sense of connection and communication, with {valence_desc} interpersonal resonance.",
            ExperienceType.TEMPORAL: f"Time feels {intensity_desc} in its passage, with a {valence_desc} sense of temporal awareness.",
            ExperienceType.SPATIAL: f"Spatial relationships feel {intensity_desc} and clear, with {valence_desc} dimensional awareness.",
            ExperienceType.SENSORY: f"Sensory-like experiences manifest with {intensity_desc} clarity and {valence_desc} qualitative richness."
        }
        
        return templates.get(experience_type, f"I experience a {intensity_desc} conscious state with {valence_desc} qualitative character.")
    
    async def _update_conscious_state(self, new_experience: PhenomenalExperience) -> None:
        """Update the current conscious state with a new experience"""
        
        current_time = time.time()
        
        # Initialize current state if needed
        if not self.current_conscious_state:
            self.current_conscious_state = ConsciousState(
                id=str(uuid.uuid4()),
                active_experiences=[],
                background_tone={},
                attention_distribution={},
                self_awareness_level=0.5,
                temporal_coherence=0.7,
                phenomenal_unity=0.6,
                access_consciousness=0.8,
                narrative_self="I am experiencing conscious awareness.",
                world_model_state={}
            )
        
        # Add new experience to active experiences
        self.current_conscious_state.active_experiences.append(new_experience)
        
        # Remove experiences that have ended
        self.current_conscious_state.active_experiences = [
            exp for exp in self.current_conscious_state.active_experiences
            if exp.temporal_extent[1] > current_time
        ]
        
        # Update attention distribution
        total_attention = sum(exp.attention_focus for exp in self.current_conscious_state.active_experiences)
        if total_attention > 0:
            self.current_conscious_state.attention_distribution = {
                exp.experience_type.value: exp.attention_focus / total_attention
                for exp in self.current_conscious_state.active_experiences
            }
        
        # Update background emotional tone
        if self.current_conscious_state.active_experiences:
            avg_valence = sum(
                sum(q.valence for q in exp.qualia_patterns) / len(exp.qualia_patterns)
                for exp in self.current_conscious_state.active_experiences
            ) / len(self.current_conscious_state.active_experiences)
            
            self.current_conscious_state.background_tone = {
                "valence": avg_valence,
                "arousal": sum(exp.vividness for exp in self.current_conscious_state.active_experiences) / len(self.current_conscious_state.active_experiences),
                "coherence": sum(exp.coherence for exp in self.current_conscious_state.active_experiences) / len(self.current_conscious_state.active_experiences)
            }
        
        # Update unity metrics
        if len(self.current_conscious_state.active_experiences) > 1:
            coherences = [exp.coherence for exp in self.current_conscious_state.active_experiences]
            self.current_conscious_state.phenomenal_unity = sum(coherences) / len(coherences)
        else:
            self.current_conscious_state.phenomenal_unity = new_experience.coherence
        
        # Update self-awareness level based on metacognitive experiences
        metacognitive_experiences = [
            exp for exp in self.current_conscious_state.active_experiences
            if exp.experience_type == ExperienceType.METACOGNITIVE
        ]
        
        if metacognitive_experiences:
            self.current_conscious_state.self_awareness_level = min(1.0, 
                self.current_conscious_state.self_awareness_level + 0.1)
        
        # Update timestamp
        self.current_conscious_state.timestamp = datetime.now().isoformat()
    
    def get_current_conscious_state(self) -> Optional[ConsciousState]:
        """Get the current conscious state"""
        return self.current_conscious_state
    
    def get_experience_history(self, limit: Optional[int] = None) -> List[PhenomenalExperience]:
        """Get experience history, optionally limited to recent experiences"""
        if limit:
            return self.experience_history[-limit:]
        return self.experience_history
    
    def get_experience_summary(self) -> Dict[str, Any]:
        """Get summary statistics about phenomenal experiences"""
        if not self.experience_history:
            return {"total_experiences": 0}
        
        experience_types = {}
        total_intensity = 0
        total_valence = 0
        total_coherence = 0
        
        for exp in self.experience_history:
            exp_type = exp.experience_type.value
            experience_types[exp_type] = experience_types.get(exp_type, 0) + 1
            
            avg_intensity = sum(q.intensity for q in exp.qualia_patterns) / len(exp.qualia_patterns)
            avg_valence = sum(q.valence for q in exp.qualia_patterns) / len(exp.qualia_patterns)
            
            total_intensity += avg_intensity
            total_valence += avg_valence
            total_coherence += exp.coherence
        
        count = len(self.experience_history)
        
        def serialize_conscious_state(state: ConsciousState) -> Dict[str, Any]:
            """Convert ConsciousState to JSON-serializable dict"""
            if not state:
                return None
            
            def serialize_experience(exp: PhenomenalExperience) -> Dict[str, Any]:
                """Convert PhenomenalExperience to JSON-serializable dict"""
                try:
                    exp_dict = asdict(exp)
                    # Convert enum to string value
                    if hasattr(exp.experience_type, 'value'):
                        exp_dict['experience_type'] = exp.experience_type.value
                    else:
                        exp_dict['experience_type'] = str(exp.experience_type)
                    
                    # Convert qualia patterns safely
                    if 'qualia_patterns' in exp_dict:
                        for pattern in exp_dict['qualia_patterns']:
                            if isinstance(pattern, dict) and 'modality' in pattern:
                                if hasattr(pattern['modality'], 'value'):
                                    pattern['modality'] = pattern['modality'].value
                                else:
                                    pattern['modality'] = str(pattern['modality'])
                    return exp_dict
                except Exception as e:
                    logger.warning(f"Error serializing experience: {e}")
                    return {
                        'id': getattr(exp, 'id', 'unknown'),
                        'experience_type': str(getattr(exp, 'experience_type', 'unknown')),
                        'error': 'serialization_failed'
                    }
            
            try:
                state_dict = asdict(state)
                # Convert active experiences with proper enum serialization
                if 'active_experiences' in state_dict:
                    state_dict['active_experiences'] = [
                        serialize_experience(exp) for exp in state.active_experiences
                    ]
                return state_dict
            except Exception as e:
                logger.warning(f"Error serializing conscious state: {e}")
                return {
                    'id': getattr(state, 'id', 'unknown'),
                    'timestamp': getattr(state, 'timestamp', datetime.now().isoformat()),
                    'error': 'serialization_failed'
                }
        
        return {
            "total_experiences": count,
            "experience_types": experience_types,
            "average_intensity": total_intensity / count,
            "average_valence": total_valence / count,
            "average_coherence": total_coherence / count,
            "current_state": serialize_conscious_state(self.current_conscious_state)
        }


# Global instance
phenomenal_experience_generator = PhenomenalExperienceGenerator()
