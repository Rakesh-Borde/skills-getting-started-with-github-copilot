"""
Tests for the Mergington High School Activities API
"""
import pytest


class TestActivitiesEndpoint:
    """Tests for the /activities GET endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that /activities endpoint returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        
    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            
    def test_activity_data_structure(self, client):
        """Test the structure of activity data"""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
        
    def test_signup_nonexistent_activity(self, client):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_signup_duplicate_participant(self, client):
        """Test signing up a participant who is already registered"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
        
    def test_signup_activity_full(self, client):
        """Test that signup still works even when activity is at capacity"""
        # Get a small activity first
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Basketball Club has max 15 participants
        basketball = activities["Basketball Club"]
        initial_count = len(basketball["participants"])
        
        # Try to add a new participant
        response = client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": "newplayer@mergington.edu"}
        )
        
        # Should still succeed (no enforcement of max capacity)
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities["Basketball Club"]["participants"]) == initial_count + 1


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_unregister_not_registered_participant(self, client):
        """Test unregistering a participant who is not registered"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
        
    def test_unregister_reduces_participant_count(self, client):
        """Test that unregistering reduces the participant count"""
        # Get initial count
        activities_response = client.get("/activities")
        initial_count = len(activities_response.json()["Chess Club"]["participants"])
        
        # Unregister a participant
        client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        # Check new count
        activities_response = client.get("/activities")
        new_count = len(activities_response.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1


class TestRootEndpoint:
    """Tests for the root / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestEmailValidation:
    """Tests for email parameter validation"""
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "student+test@mergington.edu"}
        )
        
        assert response.status_code == 200
        
        # Verify it was added correctly
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "student+test@mergington.edu" in activities["Chess Club"]["participants"]
        
    def test_unregister_with_special_characters_in_email(self, client):
        """Test unregister with special characters in email"""
        # First sign up
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "student+test@mergington.edu"}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "student+test@mergington.edu"}
        )
        
        assert response.status_code == 200


class TestActivityNameEncoding:
    """Tests for activity name URL encoding"""
    
    def test_signup_with_spaces_in_activity_name(self, client):
        """Test signup for activity with spaces in name"""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "coder@mergington.edu"}
        )
        
        assert response.status_code == 200
        
    def test_unregister_with_spaces_in_activity_name(self, client):
        """Test unregister from activity with spaces in name"""
        # First add a participant
        client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "coder@mergington.edu"}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Programming%20Class/unregister",
            params={"email": "coder@mergington.edu"}
        )
        
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""
    
    def test_signup_then_unregister_flow(self, client):
        """Test complete flow of signup and unregister"""
        email = "integration@mergington.edu"
        activity = "Soccer Team"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        check_response = client.get("/activities")
        mid_count = len(check_response.json()[activity]["participants"])
        assert mid_count == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_count
        
    def test_multiple_signups_same_activity(self, client):
        """Test multiple participants signing up for the same activity"""
        activity = "Math Olympiad"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in final_response.json()[activity]["participants"]
