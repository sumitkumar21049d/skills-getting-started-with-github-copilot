import pytest
from src.app import activities


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Client ready, activities populated
        Act: GET /activities
        Assert: Returns 200 with all activities and their details
        """
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= len(expected_activities)
        for activity in expected_activities:
            assert activity in data
            assert "description" in data[activity]
            assert "schedule" in data[activity]
            assert "participants" in data[activity]
            assert "max_participants" in data[activity]

    def test_get_activities_contains_participant_info(self, client, reset_activities):
        """
        Arrange: Activities with known participants
        Act: GET /activities
        Assert: Returns participant lists correctly
        """
        # Arrange
        # (activities already populated by fixture)

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
        assert data["Programming Class"]["participants"] == ["emma@mergington.edu", "sophia@mergington.edu"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_succeeds(self, client, reset_activities):
        """
        Arrange: New email not yet registered for activity
        Act: POST signup with new email
        Assert: Returns 200 and participant added
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "alex@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert new_email in activities[activity_name]["participants"]

    def test_signup_prevents_duplicate_registration(self, client, reset_activities):
        """
        Arrange: Email already registered for activity
        Act: Try to signup with same email again
        Assert: Returns 400 with error detail
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_case_insensitive_duplicate_prevention(self, client, reset_activities):
        """
        Arrange: Email exists in different case
        Act: Try to signup with same email in different case
        Assert: Returns 400 (case-insensitive check)
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "MICHAEL@MERGINGTON.EDU"  # uppercase

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_invalid_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Activity name that doesn't exist
        Act: POST signup for non-existent activity
        Assert: Returns 404
        """
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_empty_email_returns_400(self, client, reset_activities):
        """
        Arrange: Empty email provided
        Act: POST signup with empty email
        Assert: Returns 400
        """
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": ""}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Email is required"

    def test_signup_trims_whitespace(self, client, reset_activities):
        """
        Arrange: Email with leading/trailing whitespace
        Act: POST signup with padded email
        Assert: Email stored trimmed; second signup with trimmed version is rejected
        """
        # Arrange
        activity_name = "Programming Class"
        email_with_spaces = "  test@mergington.edu  "
        email_trimmed = "test@mergington.edu"

        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_with_spaces}
        )

        # Act - Second signup with trimmed email
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_trimmed}
        )

        # Assert
        assert response1.status_code == 200
        assert email_trimmed in activities[activity_name]["participants"]
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student already signed up for this activity"


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_succeeds(self, client, reset_activities):
        """
        Arrange: Participant exists in activity
        Act: DELETE unregister with existing email
        Assert: Returns 200 and participant removed
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email_to_remove} from {activity_name}"
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email_to_remove not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        """
        Arrange: Participant not in activity
        Act: DELETE unregister with non-existent email
        Assert: Returns 404
        """
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": nonexistent_email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found in this activity"

    def test_unregister_invalid_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Activity doesn't exist
        Act: DELETE unregister from non-existent activity
        Assert: Returns 404
        """
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_empty_email_returns_400(self, client, reset_activities):
        """
        Arrange: Empty email provided
        Act: DELETE unregister with empty email
        Assert: Returns 400
        """
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": ""}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Email is required"

    def test_unregister_case_insensitive_match(self, client, reset_activities):
        """
        Arrange: Participant registered in lowercase
        Act: DELETE unregister with uppercase email
        Assert: Returns 200 and participant removed (case-insensitive)
        """
        # Arrange
        activity_name = "Chess Club"
        original_email = "michael@mergington.edu"
        uppercase_email = "MICHAEL@MERGINGTON.EDU"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": uppercase_email}
        )

        # Assert
        assert response.status_code == 200
        assert original_email not in activities[activity_name]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client, reset_activities):
        """
        Arrange: Client ready
        Act: GET /
        Assert: Returns redirect to /static/index.html
        """
        # Arrange
        # (client ready)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
