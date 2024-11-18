import os
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime


class EventsDatabase:
    def __init__(self) -> None:
        """Initialize the events database."""
        self.filepath = os.path.join("workify", "database", "events.json")
        self._load_data()

    def _load_data(self):
        """Load events data from JSON file."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as file:
                self.data = json.load(file)
        else:
            self.data = {"events": []}

    def _save_data(self):
        """Save events data to JSON file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)

    def create_event(self, event_data: Dict, username: str) -> str:
        """Create a new event with auto-generated ID and timestamp."""
        event_id = str(uuid.uuid4())
        event_data.update(
            {
                "id": event_id,
                "created_at": datetime.now().isoformat(),
                "status": event_data.get("status", "active"),
                "who_created": username,
                **event_data,
            }
        )
        self.data["events"].append(event_data)
        self._save_data()
        return event_id

    def get_events(
        self, status: Optional[str] = None, creator: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve events with optional filtering.

        Args:
            status (Optional[str]): Filter by event status
            creator (Optional[str]): Filter by event creator

        Returns:
            List[Dict]: Filtered events
        """
        events = self.data["events"]

        if status:
            events = [event for event in events if event.get("status") == status]

        if creator:
            events = [event for event in events if event.get("who_created") == creator]

        return events

    def get_event(self, event_id: str) -> Optional[Dict]:
        """
        Get a specific event by ID.

        Args:
            event_id (str): Unique event identifier

        Returns:
            Optional[Dict]: Event details or None
        """
        return next(
            (event for event in self.data["events"] if event["id"] == event_id), None
        )

    def update_event(self, event_id: str, update_data: Dict) -> bool:
        """
        Update an existing event.

        Args:
            event_id (str): Event to update
            update_data (Dict): Fields to update

        Returns:
            bool: Update success status
        """
        for i, event in enumerate(self.data["events"]):
            if event["id"] == event_id:
                update_data["id"] = event_id
                update_data["created_at"] = event.get("created_at")

                self.data["events"][i] = {**event, **update_data}
                self._save_data()
                return True
        return False

    def delete_event(self, event_id: str) -> bool:
        """
        Soft delete an event by changing its status.

        Args:
            event_id (str): Event to delete

        Returns:
            bool: Deletion success status
        """
        for event in self.data["events"]:
            if event["id"] == event_id:
                event["status"] = "deleted"
                self._save_data()
                return True
        return False

    def add_participant(self, event_id: str, username: str) -> bool:
        """
        Add a participant to an event.

        Args:
            event_id (str): Target event
            username (str): Participant to add

        Returns:
            bool: Participation success status
        """
        event = self.get_event(event_id)
        if event and username not in event.get("participants", []):
            event["participants"].append(username)
            self.update_event(event_id, event)
            return True
        return False

    def add_comment(self, event_id: str, comment_data: Dict) -> bool:
        """
        Add a comment to an event.

        Args:
            event_id (str): Target event
            comment_data (Dict): Comment details

        Returns:
            bool: Comment addition success status
        """
        event = self.get_event(event_id)
        if event:
            comment_data["timestamp"] = datetime.now().isoformat()
            event["comments"].append(comment_data)
            self.update_event(event_id, event)
            return True
        return False


# Example usage
# def main():
#     events_db = EventsDatabase()

#     # Create an event
#     event_details = {
#         "title": "Community Cleanup Day",
#         "description": "Join us to clean up local parks",
#         "date": "2024-07-15",
#         "location": "Central Park",
#         "who_created": "JohnDoe",
#     }
#     event_id = events_db.create_event(event_details)
#     print(f"Created event with ID: {event_id}")

#     # Add a participant
#     events_db.add_participant(event_id, "AliceSmith")

#     # Add a comment
#     comment = {"author": "AliceSmith", "text": "Excited to join the cleanup!"}
#     events_db.add_comment(event_id, comment)


# if __name__ == "__main__":
#     main()
