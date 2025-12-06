"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities GET endpoint"""

    def test_get_activities_success(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_have_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup POST endpoint"""

    def test_signup_success(self):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student(self):
        """Test that a student cannot sign up twice for the same activity"""
        email = "duplicate@mergington.edu"
        activity = "Chess Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_full(self):
        """Test that students cannot sign up for a full activity"""
        # Get current activity details
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Find an activity to fill up
        test_activity = "Chess Club"
        activity = activities[test_activity]
        max_participants = activity["max_participants"]
        current_count = len(activity["participants"])
        
        # Fill up the activity
        spots_available = max_participants - current_count
        for i in range(spots_available):
            email = f"filler{i}@mergington.edu"
            response = client.post(
                f"/activities/{test_activity}/signup",
                params={"email": email}
            )
            if response.status_code != 200:
                break
        
        # Try to sign up when full
        response = client.post(
            f"/activities/{test_activity}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister POST endpoint"""

    def test_unregister_success(self):
        """Test successfully unregistering from an activity"""
        email = "unregister@mergington.edu"
        activity = "Programming Class"
        
        # First sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify they're no longer in the list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered(self):
        """Test unregistering a student who isn't registered"""
        response = client.post(
            "/activities/Drama%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"]


class TestRootEndpoint:
    """Tests for the root / endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
