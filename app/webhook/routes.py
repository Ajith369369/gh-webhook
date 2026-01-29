"""
Webhook routes for receiving GitHub events and polling API.
"""
from flask import Blueprint, jsonify, request, render_template
from datetime import datetime

from app.extensions import mongo
from app.services.github_parser import GitHubParser
from app.models.event_model import EventModel

webhook = Blueprint('webhook', __name__, url_prefix='/webhook')


@webhook.route('/github', methods=['POST'])
def receive_github_webhook():
    """
    Receive GitHub webhook events.
    
    This endpoint processes GitHub webhook payloads, parses them,
    and stores the relevant events in MongoDB.
    
    Returns:
        JSON response with status code
    """
    try:
        # Get event type from GitHub headers
        event_type = request.headers.get('X-GitHub-Event', '').lower()
        
        # Get payload
        payload = request.get_json()
        
        if not payload:
            return jsonify({'error': 'No payload received'}), 400
        
        # Parse the event based on type
        parsed_event = GitHubParser.parse_webhook_event(event_type, payload)
        
        if not parsed_event:
            # Unsupported event type - silently ignore
            return jsonify({'message': 'Event type not supported or ignored'}), 200
        
        # Validate action type
        if not EventModel.validate_action(parsed_event['action']):
            return jsonify({'error': 'Invalid action type'}), 400
        
        # Create event document
        event_doc = EventModel.create_event_document(
            request_id=parsed_event['request_id'],
            author=parsed_event['author'],
            action=parsed_event['action'],
            from_branch=parsed_event['from_branch'],
            to_branch=parsed_event['to_branch'],
            timestamp=parsed_event['timestamp']
        )
        
        # Store in MongoDB
        events_collection = mongo.db.events
        events_collection.insert_one(event_doc)
        
        return jsonify({
            'message': 'Event stored successfully',
            'event': parsed_event
        }), 200
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@webhook.route('/events', methods=['GET'])
def get_events():
    """
    Polling endpoint to retrieve events since a given timestamp.
    
    Query parameters:
        since: ISO 8601 formatted UTC timestamp string
        
    Returns:
        JSON array of events newer than the 'since' timestamp
    """
    try:
        # Get 'since' parameter from query string
        since_timestamp = request.args.get('since', '')
        
        if not since_timestamp:
            # If no timestamp provided, return all events
            # (for initial load)
            events = mongo.db.events.find().sort('timestamp', 1)
        else:
            # Query events newer than the given timestamp
            query = {'timestamp': {'$gt': since_timestamp}}
            events = mongo.db.events.find(query).sort('timestamp', 1)
        
        # Convert MongoDB cursor to list and format
        events_list = []
        for event in events:
            # Remove MongoDB _id and format response
            event.pop('_id', None)
            events_list.append(event)
        
        return jsonify(events_list), 200
        
    except Exception as e:
        print(f"Error retrieving events: {e}")
        return jsonify({'error': 'Internal server error'}), 500


