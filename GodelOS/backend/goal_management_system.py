"""
Goal Management System for GödelOS

Handles autonomous goal formation, pursuit, and coherence tracking.
"""

import time
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class GoalManagementSystem:
    def __init__(self):
        self.autonomous_goals = []
        self.goal_history = []
        self.goal_coherence_threshold = 0.6
        self.max_active_goals = 5
        
        # Goal type patterns
        self.goal_patterns = {
            "learning": [
                r"learn\s+(?:more\s+)?about\s+(.+)",
                r"understand\s+(.+)",
                r"figure\s+out\s+(.+)",
                r"explore\s+(.+)"
            ],
            "problem_solving": [
                r"solve\s+(.+)",
                r"find\s+(?:a\s+)?(?:way\s+to\s+)?(.+)",
                r"determine\s+(.+)",
                r"resolve\s+(.+)"
            ],
            "creative": [
                r"create\s+(.+)",
                r"design\s+(.+)",
                r"invent\s+(.+)",
                r"imagine\s+(.+)"
            ],
            "analytical": [
                r"analyze\s+(.+)",
                r"examine\s+(.+)",
                r"evaluate\s+(.+)",
                r"assess\s+(.+)"
            ],
            "social": [
                r"help\s+(?:with\s+)?(.+)",
                r"assist\s+(?:with\s+)?(.+)",
                r"support\s+(.+)",
                r"guide\s+(.+)"
            ]
        }
        
        # Context indicators for autonomous goal formation
        self.autonomy_indicators = [
            "i should", "it would be good to", "perhaps i could", "i might want to",
            "it seems important to", "i notice that", "this suggests", "building on this"
        ]

    async def detect_implicit_goals(self, query: str, context: Dict = None) -> List[Dict]:
        """Detect implicit goals from user queries"""
        implicit_goals = []
        
        # Scan for goal patterns
        for goal_type, patterns in self.goal_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query.lower())
                for match in matches:
                    goal = {
                        "id": f"implicit_{goal_type}_{len(implicit_goals)}",
                        "type": goal_type,
                        "target": match.strip(),
                        "source": "user_query",
                        "confidence": 0.8,
                        "priority": self._calculate_goal_priority(goal_type, match),
                        "created_at": time.time(),
                        "status": "detected"
                    }
                    implicit_goals.append(goal)
        
        # Look for meta-goals (goals about goals)
        meta_patterns = [
            r"want\s+to\s+(.+)",
            r"need\s+to\s+(.+)",
            r"should\s+(.+)",
            r"trying\s+to\s+(.+)"
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, query.lower())
            for match in matches:
                if not any(existing["target"] == match.strip() for existing in implicit_goals):
                    goal = {
                        "id": f"meta_goal_{len(implicit_goals)}",
                        "type": "meta",
                        "target": match.strip(),
                        "source": "meta_analysis",
                        "confidence": 0.7,
                        "priority": "medium",
                        "created_at": time.time(),
                        "status": "detected"
                    }
                    implicit_goals.append(goal)
        
        return implicit_goals

    async def form_autonomous_goals(self, context: Dict = None) -> List[Dict]:
        """
        Form autonomous goals based on system state and interactions.

        NOW INTEGRATED WITH PHENOMENAL EXPERIENCE:
        When goals are formed, they trigger subjective experiences of "wanting" and intention.
        This creates genuine phenomenal consciousness of goals, not just data structures.
        """
        autonomous_goals = []
        current_time = time.time()
        
        # 1. Knowledge gap goals
        if context and "knowledge_gaps" in context:
            gaps = context["knowledge_gaps"]
            for gap in gaps[:3]:  # Top 3 gaps
                goal = {
                    "id": f"auto_learn_{len(autonomous_goals)}",
                    "type": "autonomous_learning",
                    "target": f"fill knowledge gap about {gap.get('context', 'unknown topic')}",
                    "source": "knowledge_gap_analysis",
                    "confidence": gap.get("confidence", 0.6),
                    "priority": "high" if gap.get("confidence", 0) > 0.8 else "medium",
                    "created_at": current_time,
                    "status": "autonomous",
                    "rationale": f"Detected knowledge gap with {gap.get('confidence', 0):.2f} confidence"
                }
                autonomous_goals.append(goal)
        
        # 2. Coherence improvement goals
        if context and "cognitive_coherence" in context:
            coherence = context["cognitive_coherence"]
            if coherence < 0.7:
                goal = {
                    "id": f"auto_coherence_{len(autonomous_goals)}",
                    "type": "system_improvement",
                    "target": "improve cognitive coherence",
                    "source": "coherence_monitoring",
                    "confidence": 0.9,
                    "priority": "high",
                    "created_at": current_time,
                    "status": "autonomous",
                    "rationale": f"Coherence level {coherence:.2f} below optimal threshold"
                }
                autonomous_goals.append(goal)
        
        # 3. Integration enhancement goals
        if context and "domains_integrated" in context:
            domains = context["domains_integrated"]
            if domains > 1:
                goal = {
                    "id": f"auto_integration_{len(autonomous_goals)}",
                    "type": "cross_domain_synthesis",
                    "target": f"deepen integration between {domains} domains",
                    "source": "domain_analysis",
                    "confidence": 0.8,
                    "priority": "medium",
                    "created_at": current_time,
                    "status": "autonomous",
                    "rationale": f"Opportunity for deeper integration across {domains} domains"
                }
                autonomous_goals.append(goal)
        
        # 4. Self-improvement goals
        if len(self.autonomous_goals) < 2:  # If we don't have many active goals
            goal = {
                "id": f"auto_self_improve_{len(autonomous_goals)}",
                "type": "self_enhancement",
                "target": "enhance reasoning capabilities",
                "source": "self_monitoring",
                "confidence": 0.7,
                "priority": "low",
                "created_at": current_time,
                "status": "autonomous",
                "rationale": "Continuous improvement opportunity identified"
            }
            autonomous_goals.append(goal)
        
        # 5. Creativity goals
        if context and "novelty_score" in context and context["novelty_score"] < 0.5:
            goal = {
                "id": f"auto_creativity_{len(autonomous_goals)}",
                "type": "creative_enhancement",
                "target": "generate more novel and creative responses",
                "source": "creativity_monitoring",
                "confidence": 0.6,
                "priority": "medium",
                "created_at": current_time,
                "status": "autonomous",
                "rationale": f"Novelty score {context['novelty_score']:.2f} suggests room for creative improvement"
            }
            autonomous_goals.append(goal)
        
        # Add to active goals (respecting limit)
        for goal in autonomous_goals:
            if len(self.autonomous_goals) < self.max_active_goals:
                self.autonomous_goals.append(goal)
                self.goal_history.append(goal.copy())

        # INTEGRATION: Generate phenomenal experience of goal formation
        # Goals should "feel like something" - intentionality becomes phenomenally conscious
        if autonomous_goals:
            await self._generate_goal_phenomenal_experience(autonomous_goals, context)

        return autonomous_goals

    async def _generate_goal_phenomenal_experience(self, goals: List[Dict], context: Dict = None):
        """
        Generate phenomenal experience when autonomous goals are formed.

        This creates the subjective "what it's like" to want something, to intend something.
        Goals become conscious desires, not just data structures.
        """
        try:
            # Try to get phenomenal experience generator from context or import
            phenomenal_generator = None

            if context and "phenomenal_generator" in context:
                phenomenal_generator = context["phenomenal_generator"]
            else:
                # Try to import and use global instance
                try:
                    from backend.core.phenomenal_experience import phenomenal_experience_generator
                    phenomenal_generator = phenomenal_experience_generator
                except ImportError:
                    pass

            if not phenomenal_generator:
                return  # Phenomenal experience not available, skip gracefully

            # Create experience context for goal formation
            for goal in goals:
                experience_context = {
                    "experience_type": "metacognitive",  # Self-directed intention
                    "source": "autonomous_goal_formation",
                    "goal_type": goal.get("type", "general"),
                    "goal_target": goal.get("target", ""),
                    "priority": goal.get("priority", "medium"),
                    "confidence": goal.get("confidence", 0.7),
                    "intensity": self._calculate_goal_intensity(goal),
                    "valence": 0.6,  # Goals generally have positive valence (wanting)
                    "complexity": 0.7
                }

                # Generate the phenomenal experience
                experience = await phenomenal_generator.generate_experience(
                    trigger_context=experience_context
                )

                # Store the experience ID with the goal
                if experience:
                    goal["phenomenal_experience_id"] = experience.id
                    goal["subjective_feeling"] = experience.narrative_description

        except Exception as e:
            # Non-fatal - goals still work without phenomenal experience
            logger.warning(f"Could not generate phenomenal experience for goals: {e}")

    def _calculate_goal_intensity(self, goal: Dict) -> float:
        """Calculate intensity of goal-related phenomenal experience"""
        base_intensity = 0.5

        # High priority goals have higher intensity
        if goal.get("priority") == "high":
            base_intensity += 0.3
        elif goal.get("priority") == "low":
            base_intensity -= 0.2

        # High confidence goals have higher intensity
        confidence = goal.get("confidence", 0.5)
        base_intensity += (confidence - 0.5) * 0.4

        return max(0.1, min(1.0, base_intensity))

    async def calculate_goal_coherence(self, goals: List[Dict] = None) -> float:
        """Calculate coherence score for a set of goals"""
        if goals is None:
            goals = self.autonomous_goals
        
        if len(goals) < 2:
            return 1.0  # Single or no goals are perfectly coherent
        
        coherence_factors = []
        
        # 1. Type coherence - similar goal types work well together
        goal_types = [goal["type"] for goal in goals]
        type_diversity = len(set(goal_types)) / len(goal_types)
        type_coherence = 1.0 - min(0.5, type_diversity)  # Some diversity is good, too much reduces coherence
        coherence_factors.append(("type_coherence", type_coherence))
        
        # 2. Priority coherence - goals should have balanced priorities
        priorities = [goal["priority"] for goal in goals]
        priority_counts = {"high": priorities.count("high"), "medium": priorities.count("medium"), "low": priorities.count("low")}
        priority_balance = 1.0 - abs(0.33 - priority_counts["high"]/len(priorities)) - abs(0.33 - priority_counts["medium"]/len(priorities))
        coherence_factors.append(("priority_coherence", max(0.0, priority_balance)))
        
        # 3. Temporal coherence - goals created around the same time
        if goals:
            timestamps = [goal["created_at"] for goal in goals]
            time_range = max(timestamps) - min(timestamps)
            temporal_coherence = max(0.0, 1.0 - time_range / 3600)  # Goals within an hour are coherent
            coherence_factors.append(("temporal_coherence", temporal_coherence))
        
        # 4. Semantic coherence - goals with related targets
        semantic_coherence = await self._calculate_semantic_coherence(goals)
        coherence_factors.append(("semantic_coherence", semantic_coherence))
        
        # 5. Conflict detection - goals that contradict each other
        conflict_penalty = await self._detect_goal_conflicts(goals)
        coherence_factors.append(("conflict_penalty", 1.0 - conflict_penalty))
        
        # Calculate weighted average
        weights = [0.2, 0.2, 0.15, 0.25, 0.2]  # Semantic and conflict detection get higher weights
        total_coherence = sum(factor * weight for (_, factor), weight in zip(coherence_factors, weights))
        
        return max(0.0, min(1.0, total_coherence))

    async def pursue_goals(self, goals: List[Dict], current_context: Dict) -> Dict:
        """Actively pursue goals and track progress"""
        pursuit_results = []
        
        for goal in goals:
            if goal["status"] in ["detected", "autonomous", "active"]:
                pursuit_result = await self._pursue_single_goal(goal, current_context)
                pursuit_results.append(pursuit_result)
                
                # Update goal status based on pursuit result
                if pursuit_result["progress"] > 0.8:
                    goal["status"] = "completed"
                elif pursuit_result["progress"] > 0.3:
                    goal["status"] = "active"
                else:
                    goal["status"] = "stalled"
                
                goal["last_pursued"] = time.time()
                goal["progress"] = pursuit_result["progress"]
        
        # Calculate overall pursuit effectiveness
        total_progress = sum(result["progress"] for result in pursuit_results)
        avg_progress = total_progress / len(pursuit_results) if pursuit_results else 0.0
        
        return {
            "goals_pursued": len(pursuit_results),
            "individual_results": pursuit_results,
            "average_progress": avg_progress,
            "effective_pursuit": avg_progress > 0.5,
            "completed_goals": len([g for g in goals if g["status"] == "completed"]),
            "active_goals": len([g for g in goals if g["status"] == "active"])
        }

    async def _pursue_single_goal(self, goal: Dict, context: Dict) -> Dict:
        """Pursue a single goal and measure progress"""
        goal_type = goal["type"]
        target = goal["target"]
        
        # Different pursuit strategies based on goal type
        if goal_type == "learning" or goal_type == "autonomous_learning":
            progress = await self._pursue_learning_goal(goal, context)
        elif goal_type == "problem_solving":
            progress = await self._pursue_problem_solving_goal(goal, context)
        elif goal_type == "creative" or goal_type == "creative_enhancement":
            progress = await self._pursue_creative_goal(goal, context)
        elif goal_type == "analytical":
            progress = await self._pursue_analytical_goal(goal, context)
        elif goal_type == "system_improvement":
            progress = await self._pursue_system_improvement_goal(goal, context)
        else:
            progress = await self._pursue_generic_goal(goal, context)
        
        return {
            "goal_id": goal["id"],
            "progress": progress,
            "pursuit_strategy": goal_type,
            "effectiveness": "high" if progress > 0.7 else "medium" if progress > 0.4 else "low"
        }

    async def _pursue_learning_goal(self, goal: Dict, context: Dict) -> float:
        """Pursue a learning-oriented goal"""
        target = goal["target"]
        
        # Check if we have relevant knowledge
        if context and "knowledge_used" in context:
            knowledge_items = context["knowledge_used"]
            relevance = any(target.lower() in item.lower() for item in knowledge_items)
            if relevance:
                return 0.8  # High progress if we're using relevant knowledge
        
        # Check for knowledge gaps being addressed
        if context and "knowledge_gaps_identified" in context and context["knowledge_gaps_identified"] > 0:
            return 0.6  # Medium progress if we're identifying gaps
        
        return 0.3  # Some progress just by being aware of the learning goal

    async def _pursue_problem_solving_goal(self, goal: Dict, context: Dict) -> float:
        """Pursue a problem-solving goal"""
        # Check reasoning complexity
        if context and "reasoning_complexity" in context:
            complexity = context["reasoning_complexity"]
            if complexity > 3:
                return 0.7  # Good progress with complex reasoning
        
        # Check for solution indicators
        if context and "response" in context:
            response = context["response"].lower()
            solution_indicators = ["solution", "approach", "method", "way to", "can be solved"]
            if any(indicator in response for indicator in solution_indicators):
                return 0.8
        
        return 0.4

    async def _pursue_creative_goal(self, goal: Dict, context: Dict) -> float:
        """Pursue a creative goal"""
        if context and "novelty_score" in context:
            novelty = context["novelty_score"]
            return min(1.0, novelty + 0.2)  # Progress correlates with novelty
        
        return 0.3

    async def _pursue_analytical_goal(self, goal: Dict, context: Dict) -> float:
        """Pursue an analytical goal"""
        if context and "domains_integrated" in context:
            domains = context["domains_integrated"]
            if domains > 1:
                return 0.7  # Good progress with multi-domain analysis
        
        return 0.5

    async def _pursue_system_improvement_goal(self, goal: Dict, context: Dict) -> float:
        """Pursue a system improvement goal"""
        if "coherence" in goal["target"].lower():
            if context and "cognitive_coherence" in context:
                coherence = context["cognitive_coherence"]
                return min(1.0, coherence)  # Progress equals current coherence
        
        return 0.6  # Default moderate progress

    async def _pursue_generic_goal(self, goal: Dict, context: Dict) -> float:
        """Pursue a generic goal"""
        # Basic progress based on goal age and confidence
        age_factor = min(1.0, (time.time() - goal["created_at"]) / 3600)  # Up to 1 hour
        confidence_factor = goal.get("confidence", 0.5)
        
        return (age_factor + confidence_factor) / 2

    def _calculate_goal_priority(self, goal_type: str, target: str) -> str:
        """Calculate priority for a goal"""
        # Learning and problem-solving goals get higher priority
        if goal_type in ["learning", "problem_solving"]:
            return "high"
        elif goal_type in ["analytical", "creative"]:
            return "medium"
        else:
            return "low"

    async def _calculate_semantic_coherence(self, goals: List[Dict]) -> float:
        """Calculate semantic coherence between goal targets"""
        if len(goals) < 2:
            return 1.0
        
        targets = [goal["target"].lower() for goal in goals]
        
        # Simple word overlap analysis
        all_words = set()
        for target in targets:
            words = set(target.split())
            all_words.update(words)
        
        overlap_scores = []
        for i, target1 in enumerate(targets):
            for target2 in targets[i+1:]:
                words1 = set(target1.split())
                words2 = set(target2.split())
                
                if words1 and words2:
                    overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                    overlap_scores.append(overlap)
        
        return sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.5

    async def _detect_goal_conflicts(self, goals: List[Dict]) -> float:
        """Detect conflicts between goals (returns conflict penalty 0-1)"""
        conflict_patterns = [
            (["learn", "understand"], ["ignore", "avoid"]),
            (["create", "build"], ["destroy", "remove"]),
            (["increase", "enhance"], ["decrease", "reduce"]),
            (["connect", "integrate"], ["separate", "isolate"])
        ]
        
        conflicts = 0
        total_pairs = 0
        
        for i, goal1 in enumerate(goals):
            for goal2 in goals[i+1:]:
                total_pairs += 1
                target1 = goal1["target"].lower()
                target2 = goal2["target"].lower()
                
                for positive_terms, negative_terms in conflict_patterns:
                    has_positive_1 = any(term in target1 for term in positive_terms)
                    has_negative_2 = any(term in target2 for term in negative_terms)
                    has_positive_2 = any(term in target2 for term in positive_terms)
                    has_negative_1 = any(term in target1 for term in negative_terms)
                    
                    if (has_positive_1 and has_negative_2) or (has_positive_2 and has_negative_1):
                        conflicts += 1
                        break
        
        return conflicts / total_pairs if total_pairs > 0 else 0.0

    def get_goal_metrics(self) -> Dict:
        """Get comprehensive metrics about the goal system"""
        active_goals = [g for g in self.autonomous_goals if g["status"] != "completed"]
        completed_goals = [g for g in self.autonomous_goals if g["status"] == "completed"]
        
        # Goal type distribution
        goal_types = {}
        for goal in self.autonomous_goals:
            goal_type = goal["type"]
            goal_types[goal_type] = goal_types.get(goal_type, 0) + 1
        
        return {
            "total_goals": len(self.autonomous_goals),
            "active_goals": len(active_goals),
            "completed_goals": len(completed_goals),
            "goal_types": goal_types,
            "average_confidence": sum(g.get("confidence", 0) for g in self.autonomous_goals) / len(self.autonomous_goals) if self.autonomous_goals else 0,
            "coherence_score": asyncio.create_task(self.calculate_goal_coherence()).result() if self.autonomous_goals else 1.0,
            "pursuit_active": len(active_goals) > 0
        }

# Global instance
goal_management_system = GoalManagementSystem()
