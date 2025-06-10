"""
In-memory storage implementation for TutorX-MCP.

This module provides in-memory storage for development and testing.
In production, this would be replaced with database-backed storage.
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import threading
from collections import defaultdict

from ..models.student_profile import StudentProfile


class MemoryStore:
    """
    In-memory storage implementation for adaptive learning data.
    
    This provides a simple storage layer for development and testing.
    In production, this would be replaced with a proper database.
    """
    
    def __init__(self, persistence_file: Optional[str] = None):
        """
        Initialize the memory store.
        
        Args:
            persistence_file: Optional file path for data persistence
        """
        self.persistence_file = persistence_file
        self._lock = threading.RLock()
        
        # Storage containers
        self.student_profiles: Dict[str, StudentProfile] = {}
        self.performance_data: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.analytics_cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.adaptation_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Load persisted data if available
        if self.persistence_file:
            self._load_from_file()
    
    def _load_from_file(self):
        """Load data from persistence file."""
        try:
            if Path(self.persistence_file).exists():
                with open(self.persistence_file, 'rb') as f:
                    data = pickle.load(f)
                    
                self.student_profiles = data.get('student_profiles', {})
                self.performance_data = data.get('performance_data', defaultdict(dict))
                self.session_data = data.get('session_data', {})
                self.analytics_cache = data.get('analytics_cache', defaultdict(dict))
                self.adaptation_history = data.get('adaptation_history', defaultdict(list))
                
                print(f"Loaded data from {self.persistence_file}")
        except Exception as e:
            print(f"Error loading data from {self.persistence_file}: {e}")
    
    def _save_to_file(self):
        """Save data to persistence file."""
        if not self.persistence_file:
            return
        
        try:
            data = {
                'student_profiles': self.student_profiles,
                'performance_data': dict(self.performance_data),
                'session_data': self.session_data,
                'analytics_cache': dict(self.analytics_cache),
                'adaptation_history': dict(self.adaptation_history)
            }
            
            with open(self.persistence_file, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            print(f"Error saving data to {self.persistence_file}: {e}")
    
    # Student Profile Operations
    def save_student_profile(self, profile: StudentProfile) -> bool:
        """Save a student profile."""
        with self._lock:
            try:
                self.student_profiles[profile.student_id] = profile
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error saving student profile: {e}")
                return False
    
    def get_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Get a student profile by ID."""
        with self._lock:
            return self.student_profiles.get(student_id)
    
    def update_student_profile(self, student_id: str, updates: Dict[str, Any]) -> bool:
        """Update a student profile with new data."""
        with self._lock:
            try:
                if student_id not in self.student_profiles:
                    return False
                
                profile = self.student_profiles[student_id]
                
                # Update profile attributes
                for key, value in updates.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                
                profile.last_updated = datetime.utcnow()
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error updating student profile: {e}")
                return False
    
    def delete_student_profile(self, student_id: str) -> bool:
        """Delete a student profile."""
        with self._lock:
            try:
                if student_id in self.student_profiles:
                    del self.student_profiles[student_id]
                    self._save_to_file()
                    return True
                return False
            except Exception as e:
                print(f"Error deleting student profile: {e}")
                return False
    
    def list_student_profiles(self, active_only: bool = False, 
                            days: int = 30) -> List[StudentProfile]:
        """List student profiles, optionally filtering by activity."""
        with self._lock:
            profiles = list(self.student_profiles.values())
            
            if active_only:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                profiles = [
                    p for p in profiles 
                    if p.last_active and p.last_active >= cutoff_date
                ]
            
            return profiles
    
    # Performance Data Operations
    def save_performance_data(self, student_id: str, concept_id: str, 
                            data: Dict[str, Any]) -> bool:
        """Save performance data for a student and concept."""
        with self._lock:
            try:
                if student_id not in self.performance_data:
                    self.performance_data[student_id] = {}
                
                self.performance_data[student_id][concept_id] = {
                    **data,
                    'last_updated': datetime.utcnow().isoformat()
                }
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error saving performance data: {e}")
                return False
    
    def get_performance_data(self, student_id: str, 
                           concept_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get performance data for a student and optionally a specific concept."""
        with self._lock:
            if student_id not in self.performance_data:
                return None
            
            if concept_id:
                return self.performance_data[student_id].get(concept_id)
            else:
                return self.performance_data[student_id]
    
    def update_performance_data(self, student_id: str, concept_id: str,
                              updates: Dict[str, Any]) -> bool:
        """Update performance data for a student and concept."""
        with self._lock:
            try:
                if student_id not in self.performance_data:
                    self.performance_data[student_id] = {}
                
                if concept_id not in self.performance_data[student_id]:
                    self.performance_data[student_id][concept_id] = {}
                
                self.performance_data[student_id][concept_id].update(updates)
                self.performance_data[student_id][concept_id]['last_updated'] = datetime.utcnow().isoformat()
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error updating performance data: {e}")
                return False
    
    # Session Data Operations
    def save_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Save session data."""
        with self._lock:
            try:
                self.session_data[session_id] = {
                    **data,
                    'saved_at': datetime.utcnow().isoformat()
                }
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error saving session data: {e}")
                return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        with self._lock:
            return self.session_data.get(session_id)
    
    def delete_session_data(self, session_id: str) -> bool:
        """Delete session data."""
        with self._lock:
            try:
                if session_id in self.session_data:
                    del self.session_data[session_id]
                    self._save_to_file()
                    return True
                return False
            except Exception as e:
                print(f"Error deleting session data: {e}")
                return False
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Clean up old session data."""
        with self._lock:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                sessions_to_delete = []
                
                for session_id, data in self.session_data.items():
                    saved_at_str = data.get('saved_at')
                    if saved_at_str:
                        saved_at = datetime.fromisoformat(saved_at_str)
                        if saved_at < cutoff_date:
                            sessions_to_delete.append(session_id)
                
                for session_id in sessions_to_delete:
                    del self.session_data[session_id]
                
                if sessions_to_delete:
                    self._save_to_file()
                
                return len(sessions_to_delete)
            except Exception as e:
                print(f"Error cleaning up old sessions: {e}")
                return 0
    
    # Analytics Cache Operations
    def cache_analytics_result(self, cache_key: str, data: Dict[str, Any],
                             ttl_minutes: int = 60) -> bool:
        """Cache analytics result with TTL."""
        with self._lock:
            try:
                expiry_time = datetime.utcnow() + timedelta(minutes=ttl_minutes)
                self.analytics_cache[cache_key] = {
                    'data': data,
                    'expires_at': expiry_time.isoformat(),
                    'cached_at': datetime.utcnow().isoformat()
                }
                return True
            except Exception as e:
                print(f"Error caching analytics result: {e}")
                return False
    
    def get_cached_analytics(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics result if not expired."""
        with self._lock:
            if cache_key not in self.analytics_cache:
                return None
            
            cached_item = self.analytics_cache[cache_key]
            expires_at = datetime.fromisoformat(cached_item['expires_at'])
            
            if datetime.utcnow() > expires_at:
                # Cache expired, remove it
                del self.analytics_cache[cache_key]
                return None
            
            return cached_item['data']
    
    def clear_analytics_cache(self, pattern: Optional[str] = None) -> int:
        """Clear analytics cache, optionally matching a pattern."""
        with self._lock:
            try:
                if pattern is None:
                    count = len(self.analytics_cache)
                    self.analytics_cache.clear()
                    return count
                else:
                    keys_to_delete = [
                        key for key in self.analytics_cache.keys()
                        if pattern in key
                    ]
                    for key in keys_to_delete:
                        del self.analytics_cache[key]
                    return len(keys_to_delete)
            except Exception as e:
                print(f"Error clearing analytics cache: {e}")
                return 0
    
    # Adaptation History Operations
    def add_adaptation_record(self, student_id: str, record: Dict[str, Any]) -> bool:
        """Add an adaptation record for a student."""
        with self._lock:
            try:
                self.adaptation_history[student_id].append({
                    **record,
                    'recorded_at': datetime.utcnow().isoformat()
                })
                
                # Keep only last 100 records per student
                if len(self.adaptation_history[student_id]) > 100:
                    self.adaptation_history[student_id] = self.adaptation_history[student_id][-100:]
                
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error adding adaptation record: {e}")
                return False
    
    def get_adaptation_history(self, student_id: str, 
                             days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get adaptation history for a student."""
        with self._lock:
            if student_id not in self.adaptation_history:
                return []
            
            records = self.adaptation_history[student_id]
            
            if days is not None:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                records = [
                    record for record in records
                    if datetime.fromisoformat(record['recorded_at']) >= cutoff_date
                ]
            
            return records
    
    # Utility Operations
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            return {
                'student_profiles_count': len(self.student_profiles),
                'performance_data_students': len(self.performance_data),
                'total_performance_records': sum(
                    len(concepts) for concepts in self.performance_data.values()
                ),
                'active_sessions': len(self.session_data),
                'cached_analytics': len(self.analytics_cache),
                'adaptation_records': sum(
                    len(records) for records in self.adaptation_history.values()
                ),
                'persistence_enabled': self.persistence_file is not None,
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def export_data(self, format: str = 'json') -> Union[str, bytes]:
        """Export all data in specified format."""
        with self._lock:
            data = {
                'student_profiles': {
                    sid: profile.to_dict() 
                    for sid, profile in self.student_profiles.items()
                },
                'performance_data': dict(self.performance_data),
                'session_data': self.session_data,
                'analytics_cache': dict(self.analytics_cache),
                'adaptation_history': dict(self.adaptation_history),
                'exported_at': datetime.utcnow().isoformat()
            }
            
            if format.lower() == 'json':
                return json.dumps(data, indent=2)
            elif format.lower() == 'pickle':
                return pickle.dumps(data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
    
    def import_data(self, data: Union[str, bytes], format: str = 'json') -> bool:
        """Import data from specified format."""
        with self._lock:
            try:
                if format.lower() == 'json':
                    imported_data = json.loads(data)
                elif format.lower() == 'pickle':
                    imported_data = pickle.loads(data)
                else:
                    raise ValueError(f"Unsupported import format: {format}")
                
                # Import student profiles
                if 'student_profiles' in imported_data:
                    for sid, profile_data in imported_data['student_profiles'].items():
                        profile = StudentProfile.from_dict(profile_data)
                        self.student_profiles[sid] = profile
                
                # Import other data
                if 'performance_data' in imported_data:
                    self.performance_data.update(imported_data['performance_data'])
                
                if 'session_data' in imported_data:
                    self.session_data.update(imported_data['session_data'])
                
                if 'analytics_cache' in imported_data:
                    self.analytics_cache.update(imported_data['analytics_cache'])
                
                if 'adaptation_history' in imported_data:
                    self.adaptation_history.update(imported_data['adaptation_history'])
                
                self._save_to_file()
                return True
            except Exception as e:
                print(f"Error importing data: {e}")
                return False
