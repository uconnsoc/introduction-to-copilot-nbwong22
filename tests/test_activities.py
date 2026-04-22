"""
Tests for the GET /activities endpoint.
Validates that the API returns all activities with correct structure and data.
"""

import pytest


def test_get_all_activities(client, fresh_activities):
    """Test that GET /activities returns all activities."""
    response = client.get("/activities")
    
    assert response.status_code == 200
    activities = response.json()
    
    # Verify all activities are returned
    assert len(activities) == 9
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Volleyball Team" in activities


def test_activity_structure(client, fresh_activities):
    """Test that each activity has the correct structure."""
    response = client.get("/activities")
    activities = response.json()
    
    # Check a sample activity has all required fields
    chess_club = activities["Chess Club"]
    
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    
    # Verify data types
    assert isinstance(chess_club["description"], str)
    assert isinstance(chess_club["schedule"], str)
    assert isinstance(chess_club["max_participants"], int)
    assert isinstance(chess_club["participants"], list)


def test_participants_list(client, fresh_activities):
    """Test that participant lists are correctly returned."""
    response = client.get("/activities")
    activities = response.json()
    
    # Chess Club should have 2 participants
    assert len(activities["Chess Club"]["participants"]) == 2
    assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
    assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]
    
    # Volleyball Team should have 0 participants
    assert len(activities["Volleyball Team"]["participants"]) == 0


def test_activity_metadata(client, fresh_activities):
    """Test that activity metadata is correct."""
    response = client.get("/activities")
    activities = response.json()
    
    programming = activities["Programming Class"]
    
    assert programming["schedule"] == "Tuesdays and Thursdays, 3:30 PM - 4:30 PM"
    assert programming["max_participants"] == 20
    assert "programming" in programming["description"].lower()
