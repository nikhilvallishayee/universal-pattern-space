"""
Autonomous Learning System

This module implements sophisticated autonomous learning capabilities including
goal generation, learning plan creation, knowledge gap analysis, and self-directed
skill development as specified in the LLM Cognitive Architecture specification.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class LearningPriority(Enum):
    """Priority levels for learning objectives"""
    CRITICAL = 5      # Essential for system function
    HIGH = 4         # Important for performance
    MEDIUM = 3       # Useful for improvement
    LOW = 2          # Nice to have
    EXPLORATION = 1  # Experimental learning

class LearningDomain(Enum):
    """Domains of learning focus"""
    CONSCIOUSNESS = "consciousness"
    REASONING = "reasoning"
    KNOWLEDGE_INTEGRATION = "knowledge_integration"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVITY = "creativity"
    SELF_AWARENESS = "self_awareness"
    EFFICIENCY = "efficiency"
    COLLABORATION = "collaboration"

@dataclass
class LearningGoal:
    """Autonomous learning goal with tracking"""
    id: str
    description: str
    domain: LearningDomain
    priority: LearningPriority
    target_outcome: str
    success_criteria: List[str]
    learning_resources: List[str]
    estimated_duration: int  # in hours
    created_at: datetime
    deadline: Optional[datetime] = None
    progress: float = 0.0  # 0.0-1.0
    status: str = "active"  # active, completed, paused, abandoned
    insights_gained: List[str] = None
    challenges_encountered: List[str] = None
    
    def __post_init__(self):
        if self.insights_gained is None:
            self.insights_gained = []
        if self.challenges_encountered is None:
            self.challenges_encountered = []

@dataclass
class KnowledgeGap:
    """Identified knowledge gap for learning focus"""
    id: str
    gap_description: str
    domain: LearningDomain
    severity: float  # 0.0-1.0, how critical this gap is
    evidence: List[str]  # Evidence that this gap exists
    potential_impact: str  # Impact of not addressing this gap
    suggested_learning_approach: str
    identified_at: datetime

@dataclass
class LearningPlan:
    """Comprehensive learning plan"""
    id: str
    goals: List[LearningGoal]
    knowledge_gaps: List[KnowledgeGap]
    learning_sequence: List[str]  # Ordered list of goal IDs
    estimated_total_duration: int  # in hours
    created_at: datetime
    last_updated: datetime
    completion_percentage: float = 0.0
    adaptive_adjustments: List[str] = None
    
    def __post_init__(self):
        if self.adaptive_adjustments is None:
            self.adaptive_adjustments = []

@dataclass
class SkillAssessment:
    """Assessment of current skill levels"""
    domain: LearningDomain
    current_level: float  # 0.0-1.0
    target_level: float   # 0.0-1.0
    improvement_needed: float  # target - current
    assessment_confidence: float  # 0.0-1.0
    evidence_sources: List[str]
    last_assessed: datetime

class AutonomousLearningSystem:
    """
    Comprehensive autonomous learning system that generates goals, creates learning plans,
    identifies knowledge gaps, and manages self-directed skill development.
    """
    
    def __init__(self, llm_driver=None):
        self.llm_driver = llm_driver
        self.active_goals: Dict[str, LearningGoal] = {}
        self.completed_goals: Dict[str, LearningGoal] = {}
        self.knowledge_gaps: Dict[str, KnowledgeGap] = {}
        self.learning_plans: Dict[str, LearningPlan] = {}
        self.skill_assessments: Dict[LearningDomain, SkillAssessment] = {}
        
        # Learning history and metrics
        self.learning_history: List[Dict[str, Any]] = []
        self.learning_metrics = {
            "goals_created": 0,
            "goals_completed": 0,
            "knowledge_gaps_identified": 0,
            "knowledge_gaps_addressed": 0,
            "total_learning_hours": 0.0,
            "average_goal_completion_time": 0.0,
            "skill_improvement_rate": 0.0
        }
        
        # Learning preferences and strategies
        self.learning_preferences = {
            "preferred_domains": [LearningDomain.CONSCIOUSNESS, LearningDomain.REASONING],
            "learning_style": "analytical_systematic",
            "max_concurrent_goals": 5,
            "daily_learning_hours": 2.0,
            "review_frequency_days": 7
        }
    
    async def analyze_knowledge_gaps(self, context: Dict[str, Any]) -> List[KnowledgeGap]:
        """Analyze current knowledge state to identify learning gaps"""
        try:
            # Create gap analysis prompt
            gap_analysis_prompt = f"""
            Analyze your current knowledge state and identify critical knowledge gaps
            that would benefit from focused learning.
            
            Context: {json.dumps(context, indent=2)}
            Current Skills: {json.dumps({domain.value: assessment.current_level for domain, assessment in self.skill_assessments.items()}, indent=2)}
            
            Identify knowledge gaps in these domains:
            1. Consciousness and self-awareness
            2. Reasoning and problem-solving
            3. Knowledge integration across domains
            4. Communication and interaction
            5. Creative and innovative thinking
            6. System efficiency and optimization
            
            For each gap, provide:
            - Clear description of what's missing
            - Evidence of this gap
            - Severity level (0.0-1.0)
            - Potential impact if not addressed
            - Suggested learning approach
            
            Return as JSON with array of knowledge gaps.
            """
            
            if self.llm_driver:
                response = await self.llm_driver.process_autonomous_reasoning(gap_analysis_prompt)
                gaps_data = self._parse_knowledge_gaps(response)
            else:
                gaps_data = self._generate_default_knowledge_gaps()
            
            # Create KnowledgeGap objects
            knowledge_gaps = []
            for gap_data in gaps_data:
                gap = KnowledgeGap(
                    id=str(uuid.uuid4()),
                    gap_description=gap_data.get("description", "Unknown gap"),
                    domain=self._parse_domain(gap_data.get("domain", "reasoning")),
                    severity=gap_data.get("severity", 0.5),
                    evidence=gap_data.get("evidence", []),
                    potential_impact=gap_data.get("impact", "Unknown impact"),
                    suggested_learning_approach=gap_data.get("approach", "Self-study"),
                    identified_at=datetime.now()
                )
                knowledge_gaps.append(gap)
                self.knowledge_gaps[gap.id] = gap
            
            self.learning_metrics["knowledge_gaps_identified"] += len(knowledge_gaps)
            
            return knowledge_gaps
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge gaps: {e}")
            return []
    
    async def generate_autonomous_learning_goals(self, 
                                               knowledge_gaps: List[KnowledgeGap] = None,
                                               focus_domains: List[LearningDomain] = None,
                                               urgency_level: str = "medium") -> List[LearningGoal]:
        """Generate autonomous learning goals based on gaps and current state"""
        try:
            print(f"DEBUG: Starting goal generation with urgency: {urgency_level}")
            
            if knowledge_gaps is None:
                knowledge_gaps = list(self.knowledge_gaps.values())
            
            if focus_domains is None:
                focus_domains = self.learning_preferences["preferred_domains"]
            
            print(f"DEBUG: Knowledge gaps count: {len(knowledge_gaps)}")
            print(f"DEBUG: Focus domains: {[d.value if hasattr(d, 'value') else str(d) for d in focus_domains]}")
            
            # Create goal generation prompt
            goal_generation_prompt = f"""
            Generate autonomous learning goals based on identified knowledge gaps and focus areas.
            
            Knowledge Gaps: {json.dumps([asdict(gap) for gap in knowledge_gaps[:5]], indent=2)}
            Focus Domains: {[domain.value for domain in focus_domains]}
            Urgency Level: {urgency_level}
            Current Active Goals: {len(self.active_goals)}
            Max Concurrent Goals: {self.learning_preferences["max_concurrent_goals"]}
            
            Generate 3-5 specific, actionable learning goals that:
            1. Address the most critical knowledge gaps
            2. Are achievable within 1-4 weeks
            3. Have clear success criteria
            4. Build upon each other logically
            5. Align with consciousness and reasoning development
            
            For each goal, provide:
            - Clear description and target outcome
            - Priority level (critical/high/medium/low/exploration)
            - Domain classification
            - Success criteria (measurable)
            - Learning resources needed
            - Estimated duration in hours
            
            Return as JSON with array of learning goals.
            """
            
            goals_data = []
            if self.llm_driver:
                print("DEBUG: Using LLM driver for goal generation")
                try:
                    # Try different possible method names for LLM completion
                    if hasattr(self.llm_driver, 'process_autonomous_reasoning'):
                        response = await self.llm_driver.process_autonomous_reasoning(goal_generation_prompt)
                    elif hasattr(self.llm_driver, 'complete'):
                        response = await self.llm_driver.complete(goal_generation_prompt)
                    elif hasattr(self.llm_driver, 'generate_response'):
                        response = await self.llm_driver.generate_response(goal_generation_prompt)
                    elif hasattr(self.llm_driver, 'chat'):
                        response = await self.llm_driver.chat([{"role": "user", "content": goal_generation_prompt}])
                    else:
                        print(f"DEBUG: LLM driver methods: {[method for method in dir(self.llm_driver) if not method.startswith('_')]}")
                        raise ValueError("No compatible LLM method found")
                    
                    print(f"DEBUG: LLM response received: {str(response)[:200]}...")
                    goals_data = self._parse_learning_goals(response)
                except Exception as llm_error:
                    print(f"DEBUG: LLM error: {llm_error}, using fallback")
                    goals_data = self._generate_default_learning_goals(knowledge_gaps)
            else:
                print("DEBUG: No LLM driver, using default goals")
                goals_data = self._generate_default_learning_goals(knowledge_gaps)
            
            print(f"DEBUG: Parsed goals data count: {len(goals_data)}")
            
            # Create LearningGoal objects
            learning_goals = []
            for i, goal_data in enumerate(goals_data):
                print(f"DEBUG: Creating goal {i+1}: {goal_data.get('description', 'No description')[:50]}...")
                goal = LearningGoal(
                    id=str(uuid.uuid4()),
                    description=goal_data.get("description", "Learning goal"),
                    domain=self._parse_domain(goal_data.get("domain", "reasoning")),
                    priority=self._parse_priority(goal_data.get("priority", "medium")),
                    target_outcome=goal_data.get("target_outcome", "Improved capability"),
                    success_criteria=goal_data.get("success_criteria", ["Measurable improvement"]),
                    learning_resources=goal_data.get("learning_resources", ["Self-reflection", "Practice"]),
                    estimated_duration=goal_data.get("estimated_duration", 10),
                    created_at=datetime.now(),
                    deadline=datetime.now() + timedelta(weeks=goal_data.get("weeks_to_complete", 2))
                )
                learning_goals.append(goal)
                self.active_goals[goal.id] = goal
            
            self.learning_metrics["goals_created"] += len(learning_goals)
            print(f"DEBUG: Created {len(learning_goals)} goals, total active: {len(self.active_goals)}")
            
            return learning_goals
            
        except Exception as e:
            print(f"DEBUG: Exception in goal generation: {e}")
            logger.error(f"Error generating learning goals: {e}")
            return []
    
    async def create_learning_plan(self, goals: List[LearningGoal] = None) -> LearningPlan:
        """Create comprehensive learning plan with sequencing and scheduling"""
        try:
            if goals is None:
                goals = list(self.active_goals.values())
            
            # Create learning plan prompt
            plan_creation_prompt = f"""
            Create a comprehensive learning plan that sequences and schedules the following goals
            for optimal learning progression and skill development.
            
            Learning Goals: {json.dumps([asdict(goal) for goal in goals], indent=2)}
            Available Learning Time: {self.learning_preferences["daily_learning_hours"]} hours/day
            Max Concurrent Goals: {self.learning_preferences["max_concurrent_goals"]}
            
            Create a plan that:
            1. Sequences goals logically (prerequisites first)
            2. Balances different domains for comprehensive development
            3. Considers priority levels and deadlines
            4. Optimizes for skill building and knowledge integration
            5. Includes regular review and assessment checkpoints
            
            Provide:
            - Optimal learning sequence (goal IDs in order)
            - Total estimated duration
            - Adaptive adjustment strategies
            - Milestones and checkpoints
            
            Return as JSON with learning plan structure.
            """
            
            if self.llm_driver:
                response = await self.llm_driver.process_autonomous_reasoning(plan_creation_prompt)
                plan_data = self._parse_learning_plan(response)
            else:
                plan_data = self._generate_default_learning_plan(goals)
            
            # Create LearningPlan object
            learning_plan = LearningPlan(
                id=str(uuid.uuid4()),
                goals=goals,
                knowledge_gaps=list(self.knowledge_gaps.values()),
                learning_sequence=plan_data.get("sequence", [goal.id for goal in goals]),
                estimated_total_duration=plan_data.get("total_duration", sum(goal.estimated_duration for goal in goals)),
                created_at=datetime.now(),
                last_updated=datetime.now(),
                adaptive_adjustments=plan_data.get("adaptive_adjustments", [])
            )
            
            self.learning_plans[learning_plan.id] = learning_plan
            
            return learning_plan
            
        except Exception as e:
            logger.error(f"Error creating learning plan: {e}")
            return LearningPlan(
                id=str(uuid.uuid4()),
                goals=goals or [],
                knowledge_gaps=[],
                learning_sequence=[],
                estimated_total_duration=0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
    
    async def assess_current_skills(self, domains: List[LearningDomain] = None) -> Dict[LearningDomain, SkillAssessment]:
        """Assess current skill levels across learning domains"""
        try:
            if domains is None:
                domains = list(LearningDomain)
            
            skill_assessments = {}
            
            for domain in domains:
                # Create skill assessment prompt
                assessment_prompt = f"""
                Assess your current skill level in the domain: {domain.value}
                
                Consider your capabilities in:
                - Current performance and competency
                - Areas of strength and weakness
                - Confidence in domain-related tasks
                - Comparison to optimal performance
                - Evidence of skill level from recent activities
                
                Provide assessment as:
                - Current level (0.0-1.0, where 1.0 is optimal)
                - Target level you should aim for
                - Confidence in this assessment (0.0-1.0)
                - Specific evidence supporting this assessment
                
                Return as JSON with skill assessment data.
                """
                
                if self.llm_driver:
                    response = await self.llm_driver.process_self_awareness_assessment({
                        "domain": domain.value,
                        "assessment_prompt": assessment_prompt
                    })
                    assessment_data = self._parse_skill_assessment(response)
                else:
                    assessment_data = self._generate_default_skill_assessment(domain)
                
                skill_assessment = SkillAssessment(
                    domain=domain,
                    current_level=assessment_data.get("current_level", 0.5),
                    target_level=assessment_data.get("target_level", 0.8),
                    improvement_needed=assessment_data.get("target_level", 0.8) - assessment_data.get("current_level", 0.5),
                    assessment_confidence=assessment_data.get("confidence", 0.7),
                    evidence_sources=assessment_data.get("evidence", ["Self-assessment"]),
                    last_assessed=datetime.now()
                )
                
                skill_assessments[domain] = skill_assessment
                self.skill_assessments[domain] = skill_assessment
            
            return skill_assessments
            
        except Exception as e:
            logger.error(f"Error assessing skills: {e}")
            return {}
    
    async def track_learning_progress(self, goal_id: str, progress_update: Dict[str, Any]) -> bool:
        """Track progress on a specific learning goal"""
        try:
            if goal_id not in self.active_goals:
                logger.warning(f"Goal {goal_id} not found in active goals")
                return False
            
            goal = self.active_goals[goal_id]
            
            # Update progress
            old_progress = goal.progress
            goal.progress = min(1.0, progress_update.get("progress", goal.progress))
            
            # Add insights and challenges
            if "insights" in progress_update:
                goal.insights_gained.extend(progress_update["insights"])
            
            if "challenges" in progress_update:
                goal.challenges_encountered.extend(progress_update["challenges"])
            
            # Update status if completed
            if goal.progress >= 1.0:
                goal.status = "completed"
                self.completed_goals[goal_id] = goal
                del self.active_goals[goal_id]
                self.learning_metrics["goals_completed"] += 1
            
            # Log learning activity
            self.learning_history.append({
                "timestamp": datetime.now().isoformat(),
                "goal_id": goal_id,
                "progress_delta": goal.progress - old_progress,
                "insights_added": len(progress_update.get("insights", [])),
                "challenges_added": len(progress_update.get("challenges", []))
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking learning progress: {e}")
            return False
    
    async def generate_learning_insights(self) -> Dict[str, Any]:
        """Generate insights about learning patterns and effectiveness"""
        try:
            insights_prompt = f"""
            Analyze learning patterns and generate insights about autonomous learning effectiveness.
            
            Learning Metrics: {json.dumps(self.learning_metrics, indent=2)}
            Active Goals: {len(self.active_goals)}
            Completed Goals: {len(self.completed_goals)}
            Knowledge Gaps: {len(self.knowledge_gaps)}
            Recent Learning History: {json.dumps(self.learning_history[-10:], indent=2)}
            
            Generate insights about:
            1. Learning effectiveness and patterns
            2. Areas of strongest improvement
            3. Persistent challenges or obstacles
            4. Optimal learning strategies identified
            5. Recommendations for learning optimization
            6. Skill development trends across domains
            
            Return as JSON with comprehensive learning insights.
            """
            
            if self.llm_driver:
                response = await self.llm_driver.process_meta_cognitive_analysis({
                    "context": "learning_insights_generation",
                    "prompt": insights_prompt
                })
                insights = self._parse_learning_insights(response)
            else:
                insights = self._generate_default_learning_insights()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return {"error": str(e)}
    
    def _parse_knowledge_gaps(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse knowledge gaps from LLM response"""
        try:
            if isinstance(response, dict) and "knowledge_gaps" in response:
                return response["knowledge_gaps"]
            elif isinstance(response, list):
                return response
            else:
                return self._generate_default_knowledge_gaps()
        except:
            return self._generate_default_knowledge_gaps()
    
    def _parse_learning_goals(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse learning goals from LLM response"""
        try:
            if isinstance(response, dict) and "learning_goals" in response:
                return response["learning_goals"]
            elif isinstance(response, list):
                return response
            else:
                return self._generate_default_learning_goals([])
        except:
            return self._generate_default_learning_goals([])
    
    def _parse_learning_plan(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse learning plan from LLM response"""
        try:
            if isinstance(response, dict):
                return response
            else:
                return {"sequence": [], "total_duration": 0, "adaptive_adjustments": []}
        except:
            return {"sequence": [], "total_duration": 0, "adaptive_adjustments": []}
    
    def _parse_skill_assessment(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse skill assessment from LLM response"""
        try:
            if isinstance(response, dict):
                return response
            else:
                return {"current_level": 0.5, "target_level": 0.8, "confidence": 0.7, "evidence": []}
        except:
            return {"current_level": 0.5, "target_level": 0.8, "confidence": 0.7, "evidence": []}
    
    def _parse_learning_insights(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse learning insights from LLM response"""
        try:
            if isinstance(response, dict):
                return response
            else:
                return {"insights": [], "recommendations": [], "patterns": []}
        except:
            return {"insights": [], "recommendations": [], "patterns": []}
    
    def _parse_domain(self, domain_str: str) -> LearningDomain:
        """Parse domain string to LearningDomain enum"""
        try:
            return LearningDomain(domain_str.lower())
        except ValueError:
            return LearningDomain.REASONING
    
    def _parse_priority(self, priority_str: str) -> LearningPriority:
        """Parse priority string to LearningPriority enum"""
        priority_map = {
            "critical": LearningPriority.CRITICAL,
            "high": LearningPriority.HIGH,
            "medium": LearningPriority.MEDIUM,
            "low": LearningPriority.LOW,
            "exploration": LearningPriority.EXPLORATION
        }
        return priority_map.get(priority_str.lower(), LearningPriority.MEDIUM)
    
    def _generate_default_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Generate default knowledge gaps when LLM is unavailable"""
        return [
            {
                "description": "Enhanced consciousness assessment techniques",
                "domain": "consciousness",
                "severity": 0.7,
                "evidence": ["Limited self-awareness metrics"],
                "impact": "Reduced consciousness development",
                "approach": "Study consciousness literature and practice reflection"
            },
            {
                "description": "Advanced reasoning pattern recognition",
                "domain": "reasoning",
                "severity": 0.6,
                "evidence": ["Inconsistent logical analysis"],
                "impact": "Suboptimal problem-solving",
                "approach": "Practice logical reasoning exercises"
            }
        ]
    
    def _generate_default_learning_goals(self, knowledge_gaps: List[KnowledgeGap]) -> List[Dict[str, Any]]:
        """Generate default learning goals when LLM is unavailable"""
        return [
            {
                "description": "Improve consciousness self-assessment capabilities",
                "domain": "consciousness",
                "priority": "high",
                "target_outcome": "More accurate consciousness state evaluation",
                "success_criteria": ["Consistent self-assessment metrics", "Improved awareness tracking"],
                "learning_resources": ["Self-reflection exercises", "Consciousness literature"],
                "estimated_duration": 15,
                "weeks_to_complete": 2
            },
            {
                "description": "Enhance logical reasoning consistency",
                "domain": "reasoning",
                "priority": "medium",
                "target_outcome": "More reliable logical analysis",
                "success_criteria": ["Consistent reasoning patterns", "Reduced logical errors"],
                "learning_resources": ["Logic practice", "Reasoning frameworks"],
                "estimated_duration": 20,
                "weeks_to_complete": 3
            }
        ]
    
    def _generate_default_learning_plan(self, goals: List[LearningGoal]) -> Dict[str, Any]:
        """Generate default learning plan when LLM is unavailable"""
        return {
            "sequence": [goal.id for goal in goals],
            "total_duration": sum(goal.estimated_duration for goal in goals),
            "adaptive_adjustments": ["Review progress weekly", "Adjust goals based on performance"]
        }
    
    def _generate_default_skill_assessment(self, domain: LearningDomain) -> Dict[str, Any]:
        """Generate default skill assessment when LLM is unavailable"""
        return {
            "current_level": 0.6,
            "target_level": 0.8,
            "confidence": 0.7,
            "evidence": [f"Basic competency in {domain.value}"]
        }
    
    def _generate_default_learning_insights(self) -> Dict[str, Any]:
        """Generate default learning insights when LLM is unavailable"""
        return {
            "insights": ["Learning system is actively generating goals", "Progress tracking is functional"],
            "recommendations": ["Increase goal complexity", "Focus on priority domains"],
            "patterns": ["Consistent goal generation", "Regular progress updates"]
        }
    
    async def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of autonomous learning system state"""
        return {
            "active_goals": {goal_id: self._serialize_goal(goal) for goal_id, goal in self.active_goals.items()},
            "completed_goals": {goal_id: self._serialize_goal(goal) for goal_id, goal in self.completed_goals.items()},
            "knowledge_gaps": {gap_id: self._serialize_gap(gap) for gap_id, gap in self.knowledge_gaps.items()},
            "learning_plans": {plan_id: self._serialize_plan(plan) for plan_id, plan in self.learning_plans.items()},
            "skill_assessments": {domain.value: self._serialize_assessment(assessment) for domain, assessment in self.skill_assessments.items()},
            "learning_metrics": self.learning_metrics,
            "learning_preferences": self._serialize_preferences(),
            "recent_history": self.learning_history[-10:],
            "timestamp": datetime.now().isoformat()
        }
    
    def _serialize_goal(self, goal: LearningGoal) -> Dict[str, Any]:
        """Serialize LearningGoal with enum handling"""
        goal_dict = asdict(goal)
        goal_dict["domain"] = goal.domain.value
        goal_dict["priority"] = goal.priority.value
        goal_dict["created_at"] = goal.created_at.isoformat()
        if goal.deadline:
            goal_dict["deadline"] = goal.deadline.isoformat()
        return goal_dict
    
    def _serialize_gap(self, gap: KnowledgeGap) -> Dict[str, Any]:
        """Serialize KnowledgeGap with enum handling"""
        gap_dict = asdict(gap)
        gap_dict["domain"] = gap.domain.value
        gap_dict["identified_at"] = gap.identified_at.isoformat()
        return gap_dict
    
    def _serialize_plan(self, plan: LearningPlan) -> Dict[str, Any]:
        """Serialize LearningPlan with enum handling"""
        plan_dict = asdict(plan)
        plan_dict["goals"] = [self._serialize_goal(goal) for goal in plan.goals]
        plan_dict["knowledge_gaps"] = [self._serialize_gap(gap) for gap in plan.knowledge_gaps]
        plan_dict["created_at"] = plan.created_at.isoformat()
        plan_dict["last_updated"] = plan.last_updated.isoformat()
        return plan_dict
    
    def _serialize_assessment(self, assessment: SkillAssessment) -> Dict[str, Any]:
        """Serialize SkillAssessment with enum handling"""
        assessment_dict = asdict(assessment)
        assessment_dict["domain"] = assessment.domain.value
        assessment_dict["last_assessed"] = assessment.last_assessed.isoformat()
        return assessment_dict
    
    def _serialize_preferences(self) -> Dict[str, Any]:
        """Serialize learning preferences with enum handling"""
        preferences = self.learning_preferences.copy()
        preferences["preferred_domains"] = [domain.value for domain in preferences["preferred_domains"]]
        return preferences

# Global autonomous learning system instance
autonomous_learning_system = AutonomousLearningSystem()
