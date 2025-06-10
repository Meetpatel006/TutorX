"""
Student profile data models for TutorX-MCP.

This module defines data structures for storing and managing
student learning profiles, preferences, and characteristics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class LearningStyle(Enum):
    """Learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class LearningPace(Enum):
    """Learning pace preferences."""
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    ADAPTIVE = "adaptive"


class DifficultyPreference(Enum):
    """Difficulty progression preferences."""
    GRADUAL = "gradual"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class FeedbackPreference(Enum):
    """Feedback delivery preferences."""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    SUMMARY = "summary"
    MINIMAL = "minimal"


@dataclass
class LearningPreferences:
    """Student learning preferences and settings."""
    learning_style: LearningStyle = LearningStyle.MULTIMODAL
    learning_pace: LearningPace = LearningPace.ADAPTIVE
    difficulty_preference: DifficultyPreference = DifficultyPreference.ADAPTIVE
    feedback_preference: FeedbackPreference = FeedbackPreference.IMMEDIATE
    
    # Session preferences
    preferred_session_length: int = 30  # minutes
    max_session_length: int = 60  # minutes
    break_frequency: int = 20  # minutes between breaks
    
    # Content preferences
    gamification_enabled: bool = True
    hints_enabled: bool = True
    explanations_enabled: bool = True
    examples_enabled: bool = True
    
    # Notification preferences
    reminders_enabled: bool = True
    progress_notifications: bool = True
    achievement_notifications: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'learning_style': self.learning_style.value,
            'learning_pace': self.learning_pace.value,
            'difficulty_preference': self.difficulty_preference.value,
            'feedback_preference': self.feedback_preference.value,
            'preferred_session_length': self.preferred_session_length,
            'max_session_length': self.max_session_length,
            'break_frequency': self.break_frequency,
            'gamification_enabled': self.gamification_enabled,
            'hints_enabled': self.hints_enabled,
            'explanations_enabled': self.explanations_enabled,
            'examples_enabled': self.examples_enabled,
            'reminders_enabled': self.reminders_enabled,
            'progress_notifications': self.progress_notifications,
            'achievement_notifications': self.achievement_notifications
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningPreferences':
        """Create from dictionary."""
        return cls(
            learning_style=LearningStyle(data.get('learning_style', 'multimodal')),
            learning_pace=LearningPace(data.get('learning_pace', 'adaptive')),
            difficulty_preference=DifficultyPreference(data.get('difficulty_preference', 'adaptive')),
            feedback_preference=FeedbackPreference(data.get('feedback_preference', 'immediate')),
            preferred_session_length=data.get('preferred_session_length', 30),
            max_session_length=data.get('max_session_length', 60),
            break_frequency=data.get('break_frequency', 20),
            gamification_enabled=data.get('gamification_enabled', True),
            hints_enabled=data.get('hints_enabled', True),
            explanations_enabled=data.get('explanations_enabled', True),
            examples_enabled=data.get('examples_enabled', True),
            reminders_enabled=data.get('reminders_enabled', True),
            progress_notifications=data.get('progress_notifications', True),
            achievement_notifications=data.get('achievement_notifications', True)
        )


@dataclass
class StudentGoals:
    """Student learning goals and objectives."""
    target_concepts: List[str] = field(default_factory=list)
    target_mastery_level: float = 0.8
    target_completion_date: Optional[datetime] = None
    daily_time_goal: int = 30  # minutes per day
    weekly_concept_goal: int = 2  # concepts per week
    
    # Long-term goals
    grade_level_target: Optional[str] = None
    subject_focus_areas: List[str] = field(default_factory=list)
    career_interests: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'target_concepts': self.target_concepts,
            'target_mastery_level': self.target_mastery_level,
            'target_completion_date': self.target_completion_date.isoformat() if self.target_completion_date else None,
            'daily_time_goal': self.daily_time_goal,
            'weekly_concept_goal': self.weekly_concept_goal,
            'grade_level_target': self.grade_level_target,
            'subject_focus_areas': self.subject_focus_areas,
            'career_interests': self.career_interests
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentGoals':
        """Create from dictionary."""
        target_date = None
        if data.get('target_completion_date'):
            target_date = datetime.fromisoformat(data['target_completion_date'])
        
        return cls(
            target_concepts=data.get('target_concepts', []),
            target_mastery_level=data.get('target_mastery_level', 0.8),
            target_completion_date=target_date,
            daily_time_goal=data.get('daily_time_goal', 30),
            weekly_concept_goal=data.get('weekly_concept_goal', 2),
            grade_level_target=data.get('grade_level_target'),
            subject_focus_areas=data.get('subject_focus_areas', []),
            career_interests=data.get('career_interests', [])
        )


@dataclass
class StudentProfile:
    """Comprehensive student learning profile."""
    student_id: str
    name: Optional[str] = None
    grade_level: Optional[str] = None
    age: Optional[int] = None
    
    # Learning characteristics
    preferences: LearningPreferences = field(default_factory=LearningPreferences)
    goals: StudentGoals = field(default_factory=StudentGoals)
    
    # Profile metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    
    # Adaptive learning state
    current_difficulty_level: float = 0.5
    learning_velocity: float = 0.0  # concepts per day
    engagement_level: float = 0.5
    
    # Performance summary
    total_concepts_attempted: int = 0
    total_concepts_mastered: int = 0
    total_learning_time: int = 0  # minutes
    average_accuracy: float = 0.0
    
    # Strengths and challenges
    strength_areas: List[str] = field(default_factory=list)
    challenge_areas: List[str] = field(default_factory=list)
    
    # Adaptive learning insights
    learning_patterns: List[str] = field(default_factory=list)
    recommended_strategies: List[str] = field(default_factory=list)
    
    def update_last_active(self):
        """Update last active timestamp."""
        self.last_active = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def update_performance_summary(self, concepts_attempted: int, concepts_mastered: int,
                                 learning_time: int, accuracy: float):
        """Update performance summary statistics."""
        self.total_concepts_attempted = concepts_attempted
        self.total_concepts_mastered = concepts_mastered
        self.total_learning_time = learning_time
        self.average_accuracy = accuracy
        self.last_updated = datetime.utcnow()
    
    def calculate_mastery_rate(self) -> float:
        """Calculate overall mastery rate."""
        if self.total_concepts_attempted == 0:
            return 0.0
        return self.total_concepts_mastered / self.total_concepts_attempted
    
    def calculate_daily_average_time(self, days: int = 30) -> float:
        """Calculate average daily learning time over specified period."""
        if days <= 0:
            return 0.0
        
        # This would need to be calculated from actual session data
        # For now, return a simple estimate
        return self.total_learning_time / max(1, days)
    
    def is_active_learner(self, days: int = 7) -> bool:
        """Check if student has been active in recent days."""
        if not self.last_active:
            return False
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.last_active >= cutoff_date
    
    def get_learning_efficiency(self) -> float:
        """Calculate learning efficiency (mastery per hour)."""
        if self.total_learning_time == 0:
            return 0.0
        
        hours = self.total_learning_time / 60.0
        return self.total_concepts_mastered / hours
    
    def add_strength_area(self, area: str):
        """Add a strength area if not already present."""
        if area not in self.strength_areas:
            self.strength_areas.append(area)
            self.last_updated = datetime.utcnow()
    
    def add_challenge_area(self, area: str):
        """Add a challenge area if not already present."""
        if area not in self.challenge_areas:
            self.challenge_areas.append(area)
            self.last_updated = datetime.utcnow()
    
    def add_learning_pattern(self, pattern: str):
        """Add a detected learning pattern."""
        if pattern not in self.learning_patterns:
            self.learning_patterns.append(pattern)
            self.last_updated = datetime.utcnow()
    
    def add_recommended_strategy(self, strategy: str):
        """Add a recommended learning strategy."""
        if strategy not in self.recommended_strategies:
            self.recommended_strategies.append(strategy)
            self.last_updated = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'student_id': self.student_id,
            'name': self.name,
            'grade_level': self.grade_level,
            'age': self.age,
            'preferences': self.preferences.to_dict(),
            'goals': self.goals.to_dict(),
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'current_difficulty_level': self.current_difficulty_level,
            'learning_velocity': self.learning_velocity,
            'engagement_level': self.engagement_level,
            'total_concepts_attempted': self.total_concepts_attempted,
            'total_concepts_mastered': self.total_concepts_mastered,
            'total_learning_time': self.total_learning_time,
            'average_accuracy': self.average_accuracy,
            'strength_areas': self.strength_areas,
            'challenge_areas': self.challenge_areas,
            'learning_patterns': self.learning_patterns,
            'recommended_strategies': self.recommended_strategies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentProfile':
        """Create from dictionary."""
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow()
        last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.utcnow()
        last_active = datetime.fromisoformat(data['last_active']) if data.get('last_active') else None
        
        preferences = LearningPreferences.from_dict(data.get('preferences', {}))
        goals = StudentGoals.from_dict(data.get('goals', {}))
        
        return cls(
            student_id=data['student_id'],
            name=data.get('name'),
            grade_level=data.get('grade_level'),
            age=data.get('age'),
            preferences=preferences,
            goals=goals,
            created_at=created_at,
            last_updated=last_updated,
            last_active=last_active,
            current_difficulty_level=data.get('current_difficulty_level', 0.5),
            learning_velocity=data.get('learning_velocity', 0.0),
            engagement_level=data.get('engagement_level', 0.5),
            total_concepts_attempted=data.get('total_concepts_attempted', 0),
            total_concepts_mastered=data.get('total_concepts_mastered', 0),
            total_learning_time=data.get('total_learning_time', 0),
            average_accuracy=data.get('average_accuracy', 0.0),
            strength_areas=data.get('strength_areas', []),
            challenge_areas=data.get('challenge_areas', []),
            learning_patterns=data.get('learning_patterns', []),
            recommended_strategies=data.get('recommended_strategies', [])
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StudentProfile':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
