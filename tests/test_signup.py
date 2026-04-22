"""
Tests for the POST /activities/{activity_name}/signup endpoint.
Validates successful signups and error handling for various scenarios.
"""

import pytest


def test_successful_signup(client, fresh_activities):
    """Test that a student can successfully sign up for an activity."""
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new_student@mergington.edu"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "new_student@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]


def test_signup_updates_participants(client, fresh_activities):
    """Test that successful signup adds student to participants list."""
    # Sign up for Volleyball Team (which starts empty)
    client.post(
        "/activities/Volleyball%20Team/signup",
        params={"email": "alexis@mergington.edu"}
    )
    
    # Verify the student appears in the participants list
    response = client.get("/activities")
    activities = response.json()
    
    assert "alexis@mergington.edu" in activities["Volleyball Team"]["participants"]
    assert len(activities["Volleyball Team"]["participants"]) == 1


def test_signup_nonexistent_activity(client, fresh_activities):
    """Test that signing up for non-existent activity returns 404."""
    response = client.post(
        "/activities/Fake%20Club/signup",
        params={"email": "student@mergington.edu"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_duplicate_signup_returns_400(client, fresh_activities):
    """Test that signing up twice for same activity returns 400."""
    email = "michael@mergington.edu"
    
    # Try to sign up with an email already registered for Chess Club
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already" in data["detail"].lower()


def test_signup_multiple_students_same_activity(client, fresh_activities):
    """Test that multiple different students can sign up for the same activity."""
    activity = "Theater%20Club"
    
    # Sign up first student
    response1 = client.post(
        f"/activities/{activity}/signup",
        params={"email": "student1@mergington.edu"}
    )
    assert response1.status_code == 200
    
    # Sign up second student
    response2 = client.post(
        f"/activities/{activity}/signup",
        params={"email": "student2@mergington.edu"}
    )
    assert response2.status_code == 200
    
    # Verify both are in participants
    response = client.get("/activities")
    activities = response.json()
    participants = activities["Theater Club"]["participants"]
    
    assert len(participants) == 2
    assert "student1@mergington.edu" in participants
    assert "student2@mergington.edu" in participants


def test_signup_with_special_characters_email(client, fresh_activities):
    """Test signup with email containing special characters."""
    response = client.post(
        "/activities/Science%20Club/signup",
        params={"email": "student+test@mergington.edu"}
    )
    
    # Should succeed - special chars in email are valid
    assert response.status_code == 200


def test_signup_activity_name_url_encoding(client, fresh_activities):
    """Test that activity names are properly URL decoded."""
    response = client.post(
        "/activities/Science%20Club/signup",
        params={"email": "physicist@mergington.edu"}
    )
    
    assert response.status_code == 200
    
    # Verify student is added to the correct activity
    response = client.get("/activities")
    activities = response.json()
    assert "physicist@mergington.edu" in activities["Science Club"]["participants"]


def test_signup_empty_email_params(client, fresh_activities):
    """Test signup with missing email parameter."""
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={}
    )
    
    # Missing email should cause an error
    assert response.status_code in [400, 422]  # 422 for FastAPI validation, 400 for custom validation


def test_signup_preserves_existing_participants(client, fresh_activities):
    """Test that adding a new participant doesn't remove existing ones."""
    # Get original participants for Chess Club
    response = client.get("/activities")
    activities = response.json()
    original_participants = activities["Chess Club"]["participants"].copy()
    
    # Sign up a new student
    client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "newest_student@mergington.edu"}
    )
    
    # Verify original participants are still there plus the new one
    response = client.get("/activities")
    activities = response.json()
    new_participants = activities["Chess Club"]["participants"]
    
    assert len(new_participants) == len(original_participants) + 1
    for original in original_participants:
        assert original in new_participants
