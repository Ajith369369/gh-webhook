"""
Event model for GitHub webhook events stored in MongoDB.
"""
from datetime import datetime
from typing import Dict, Optional


class EventModel:
    """
    Model class for GitHub webhook events.
    
    This class provides methods to create and validate event documents
    that will be stored in MongoDB.
    """
    
    # Valid action types as enum
    ACTION_TYPES = ["PUSH", "PULL_REQUEST", "MERGE"]
    
    @staticmethod
    def create_event_document(
        request_id: str,
        author: str,
        action: str,
        from_branch: str,
        to_branch: str,
        timestamp: str
    ) -> Dict:
        """
        Create an event document for MongoDB storage.
        
        Args:
            request_id: Git commit hash or PR ID
            author: Name of the GitHub user
            action: Action type (PUSH, PULL_REQUEST, MERGE)
            from_branch: Source branch name
            to_branch: Target branch name
            timestamp: ISO 8601 formatted UTC timestamp string
            
        Returns:
            Dict: Event document ready for MongoDB insertion
        """
        return {
            "request_id": request_id,
            "author": author,
            "action": action,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": timestamp
        }
    
    @staticmethod
    def validate_action(action: str) -> bool:
        """
        Validate if the action type is supported.
        
        Args:
            action: Action type to validate
            
        Returns:
            bool: True if action is valid, False otherwise
        """
        return action in EventModel.ACTION_TYPES
