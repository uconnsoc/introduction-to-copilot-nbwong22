"""
Integration tests for the FastAPI application.
Tests multi-step workflows and interactions between endpoints.
"""

import pytest


def test_signup_then_verify_activity_list(client, fresh_activities):
    """
    Integration test: Sign up for an activity, then verify it appears
    in the activities list with updated participant count.
    """
    # Initial state: Track and Field has 0 participants
    response = client.get("/activities")
    activities = response.json()
    assert len(activities["Track and Field"]["participants"]) == 0
    
    # Sign up for Track and Field
    signup_response = client.post(
        "/activities/Track%20and%20Field/signup",
        params={"email": "runner@mergington.edu"}
    )
    assert signup_response.status_code == 200
    
    # Verify the activity list now shows the new participant
    response = client.get("/activities")
    activities = response.json()
    assert len(activities["Track and Field"]["participants"]) == 1
    assert "runner@mergington.edu" in activities["Track and Field"]["participants"]


def test_multiple_signups_maintain_state(client, fresh_activities):
    """
    Integration test: Multiple users signing up for different activities
    maintains correct state for each activity.
    """
    # Sign up user 1 for Activity A
    client.post(
        "/activities/Debate%20Team/signup",
        params={"email": "debater1@mergington.edu"}
    )
    
    # Sign up user 2 for Activity B
    client.post(
        "/activities/Visual%20Arts%20Studio/signup",
        params={"email": "artist1@mergington.edu"}
    )
    
    # Sign up user 3 for Activity A (same as user 1)
    client.post(
        "/activities/Debate%20Team/signup",
        params={"email": "debater2@mergington.edu"}
    )
    
    # Verify final state
    response = client.get("/activities")
    activities = response.json()
    
    # Debate Team should have 2 new participants
    assert len(activities["Debate Team"]["participants"]) == 2
    assert "debater1@mergington.edu" in activities["Debate Team"]["participants"]
    assert "debater2@mergington.edu" in activities["Debate Team"]["participants"]
    
    # Visual Arts Studio should have 1 new participant
    assert len(activities["Visual Arts Studio"]["participants"]) == 1
    assert "artist1@mergington.edu" in activities["Visual Arts Studio"]["participants"]


def test_fixture_isolation_between_tests(client, fresh_activities):
    """
    Integration test: Verify that fixtures properly isolate state between tests.
    Each test should get a fresh copy of activities data.
    """
    # Sign up a student
    client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "temporary_student@mergington.edu"}
    )
    
    # Verify the signup worked
    response = client.get("/activities")
    activities = response.json()
    assert "temporary_student@mergington.edu" in activities["Chess Club"]["participants"]
    
    # Note: When the next test runs with fresh_activities fixture,
    # it will get a fresh database without this temporary_student


def test_activity_exists_after_signup_attempt(client, fresh_activities):
    """
    Integration test: Verify that attempting to sign up for a non-existent
    activity doesn't affect existing activities.
    """
    # Try to sign up for non-existent activity
    client.post(
        "/activities/Fake%20Club/signup",
        params={"email": "student@mergington.edu"}
    )
    
    # Verify all valid activities still exist
    response = client.get("/activities")
    activities = response.json()
    
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Gym Class" in activities
    assert "Volleyball Team" in activities
    assert "Track and Field" in activities
    assert "Theater Club" in activities
    assert "Visual Arts Studio" in activities
    assert "Science Club" in activities
    assert "Debate Team" in activities


def test_concurrent_signup_attempts_different_activities(client, fresh_activities):
    """
    Integration test: Multiple signups to different activities
    are processed correctly without conflicts.
    """
    activities_to_signup = [
        ("Chess%20Club", "chess_fan@mergington.edu"),
        ("Programming%20Class", "coder@mergington.edu"),
        ("Gym%20Class", "athlete@mergington.edu"),
        ("Theater%20Club", "actor@mergington.edu"),
        ("Science%20Club", "scientist@mergington.edu"),
    ]
    
    # Perform all signups
    for activity, email in activities_to_signup:
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all signups were recorded
    response = client.get("/activities")
    activities = response.json()
    
    assert "chess_fan@mergington.edu" in activities["Chess Club"]["participants"]
    assert "coder@mergington.edu" in activities["Programming Class"]["participants"]
    assert "athlete@mergington.edu" in activities["Gym Class"]["participants"]
    assert "actor@mergington.edu" in activities["Theater Club"]["participants"]
    assert "scientist@mergington.edu" in activities["Science Club"]["participants"]


def test_error_doesnt_corrupt_database(client, fresh_activities):
    """
    Integration test: Verify that failed operations (like duplicate signup)
    don't corrupt or modify the database state.
    """
    # Get initial state of Chess Club
    response = client.get("/activities")
    initial_participants = response.json()["Chess Club"]["participants"].copy()
    
    # Attempt duplicate signup (should fail)
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 400
    
    # Verify participants list is unchanged after failed signup
    response = client.get("/activities")
    current_participants = response.json()["Chess Club"]["participants"]
    
    assert current_participants == initial_participants


def test_mixed_success_and_failure_operations(client, fresh_activities):
    """
    Integration test: Series of operations with both successes and failures
    maintains correct database state.
    """
    # Successful signup
    r1 = client.post(
        "/activities/Programming%20Class/signup",
        params={"email": "new_coder@mergington.edu"}
    )
    assert r1.status_code == 200
    
    # Failed signup (duplicate)
    r2 = client.post(
        "/activities/Programming%20Class/signup",
        params={"email": "emma@mergington.edu"}
    )
    assert r2.status_code == 400
    
    # Successful signup (different activity)
    r3 = client.post(
        "/activities/Volleyball%20Team/signup",
        params={"email": "volleyball_player@mergington.edu"}
    )
    assert r3.status_code == 200
    
    # Failed signup (non-existent activity)
    r4 = client.post(
        "/activities/Fake%20Club/signup",
        params={"email": "nobody@mergington.edu"}
    )
    assert r4.status_code == 404
    
    # Verify final state is correct
    response = client.get("/activities")
    activities = response.json()
    
    prog_class = activities["Programming Class"]
    assert len(prog_class["participants"]) == 3  # emma, sophia, new_coder
    assert "new_coder@mergington.edu" in prog_class["participants"]
    
    volleyball = activities["Volleyball Team"]
    assert len(volleyball["participants"]) == 1
    assert "volleyball_player@mergington.edu" in volleyball["participants"]
