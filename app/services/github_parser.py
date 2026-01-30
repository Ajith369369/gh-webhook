"""
GitHub webhook event parser service.

This module handles parsing GitHub webhook payloads and extracting
relevant information for storage in MongoDB.
"""
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple


class GitHubParser:
    """
    Parser for GitHub webhook events.
    
    Converts GitHub webhook payloads into normalized event documents
    suitable for MongoDB storage.
    """
    
    @staticmethod
    def parse_push_event(payload: Dict) -> Optional[Dict]:
        """
        Parse a GitHub push event payload.
        
        Args:
            payload: GitHub webhook payload for push event
            
        Returns:
            Dict: Parsed event data or None if parsing fails
        """
        try:
            # Extract author name
            author = payload.get('pusher', {}).get('name', 'Unknown')
            if not author or author == 'Unknown':
                # Fallback to commit author
                commits = payload.get('commits', [])
                if commits:
                    author = commits[0].get('author', {}).get('name', 'Unknown')
            
            # Extract branch information
            ref = payload.get('ref', '')
            branch = ref.replace('refs/heads/', '') if ref.startswith('refs/heads/') else ref
            
            # Extract commit hash (use head commit)
            head_commit = payload.get('head_commit', {})
            request_id = head_commit.get('id', '')[:7] if head_commit.get('id') else ''
            
            # Extract timestamp (convert to UTC ISO 8601)
            timestamp_str = payload.get('head_commit', {}).get('timestamp')
            if not timestamp_str:
                timestamp_str = payload.get('repository', {}).get('pushed_at', datetime.utcnow().isoformat())
            
            # Convert to UTC datetime and format as ISO 8601 string
            timestamp = GitHubParser._parse_github_timestamp(timestamp_str)
            
            return {
                'request_id': request_id,
                'author': author,
                'action': 'PUSH',
                'from_branch': branch,
                'to_branch': branch,
                'timestamp': timestamp
            }
        except Exception as e:
            print(f"Error parsing push event: {e}")
            return None
    
    @staticmethod
    def parse_pull_request_event(payload: Dict) -> Optional[Dict]:
        """
        Parse a GitHub pull request event payload.
        
        Handles both opened and merged PR events.
        
        Args:
            payload: GitHub webhook payload for pull_request event
            
        Returns:
            Dict: Parsed event data or None if parsing fails
        """
        try:
            action_type = payload.get('action', '').lower()
            pr_data = payload.get('pull_request', {})
            
            # Extract author
            author = pr_data.get('user', {}).get('login', 'Unknown')
            
            # Extract branch information
            from_branch = pr_data.get('head', {}).get('ref', '')
            to_branch = pr_data.get('base', {}).get('ref', '')
            
            # Extract PR ID
            request_id = str(pr_data.get('number', ''))
            
            # Extract timestamp
            if action_type == 'closed' and pr_data.get('merged'):
                # This is a merge event
                timestamp_str = pr_data.get('merged_at')
                if not timestamp_str:
                    timestamp_str = pr_data.get('updated_at', datetime.utcnow().isoformat())
                action = 'MERGE'
            else:
                # This is a pull request opened event
                timestamp_str = pr_data.get('created_at', datetime.utcnow().isoformat())
                action = 'PULL_REQUEST'
            
            # Convert to UTC datetime and format as ISO 8601 string
            timestamp = GitHubParser._parse_github_timestamp(timestamp_str)
            
            return {
                'request_id': request_id,
                'author': author,
                'action': action,
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': timestamp
            }
        except Exception as e:
            print(f"Error parsing pull request event: {e}")
            return None
    
    @staticmethod
    def parse_webhook_event(event_type: str, payload: Dict) -> Optional[Dict]:
        """
        Parse a GitHub webhook event based on event type.
        
        Args:
            event_type: GitHub event type (push, pull_request, etc.)
            payload: GitHub webhook payload
            
        Returns:
            Dict: Parsed event data or None if event type is unsupported
        """
        event_type_lower = event_type.lower()
        
        if event_type_lower == 'push':
            return GitHubParser.parse_push_event(payload)
        elif event_type_lower == 'pull_request':
            return GitHubParser.parse_pull_request_event(payload)
        else:
            # Unsupported event type
            return None
    
    @staticmethod
    def _parse_github_timestamp(timestamp_str: str) -> str:
        """
        Parse GitHub timestamp string and convert to UTC ISO 8601 format.
        
        GitHub timestamps are typically in ISO 8601 format but may include
        timezone information. This method ensures we store UTC timestamps.
        
        Args:
            timestamp_str: GitHub timestamp string
            
        Returns:
            str: ISO 8601 formatted UTC timestamp string
        """
        try:
            # Normalize 'Z' to '+00:00' so fromisoformat parses it (Python < 3.11)
            normalized = timestamp_str.strip().replace('Z', '+00:00')
            # Parse with timezone (handles +05:30, +00:00, etc.)
            dt = datetime.fromisoformat(normalized)
            # If naive (no timezone), assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            # Convert to UTC and format as ISO 8601
            utc_dt = dt.astimezone(timezone.utc)
            return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception as e:
            print(f"Error parsing timestamp {timestamp_str}: {e}")
            return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')