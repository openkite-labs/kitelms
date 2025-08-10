def test_create_post(auth_client):
    """Test creating a new post."""
    post_data = {"content": "This is my first post!", "image_url": "https://example.com/image.jpg"}

    response = auth_client.post("/timeline/posts", json=post_data)
    assert response.status_code == 200

    data = response.json()
    assert data["content"] == post_data["content"]
    assert data["image_url"] == post_data["image_url"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_posts(client):
    """Test getting posts from timeline."""
    response = client.get("/timeline/posts")
    assert response.status_code == 200

    data = response.json()
    assert "posts" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["posts"], list)


def test_get_post_by_id(auth_client):
    """Test getting a specific post by ID."""
    # First create a post
    post_data = {"content": "Test post for retrieval"}
    create_response = auth_client.post("/timeline/posts", json=post_data)
    assert create_response.status_code == 200
    post_id = create_response.json()["id"]

    # Then retrieve it
    response = auth_client.get(f"/timeline/posts/{post_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == post_id
    assert data["content"] == post_data["content"]


def test_update_post(auth_client):
    """Test updating a post."""
    # Create a post
    post_data = {"content": "Original content"}
    create_response = auth_client.post("/timeline/posts", json=post_data)
    assert create_response.status_code == 200
    post_id = create_response.json()["id"]

    # Update the post
    update_data = {"content": "Updated content"}
    response = auth_client.put(f"/timeline/posts/{post_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["content"] == update_data["content"]


def test_delete_post(auth_client):
    """Test deleting a post."""
    # Create a post
    post_data = {"content": "Post to be deleted"}
    create_response = auth_client.post("/timeline/posts", json=post_data)
    assert create_response.status_code == 200
    post_id = create_response.json()["id"]

    # Delete the post
    response = auth_client.delete(f"/timeline/posts/{post_id}")
    assert response.status_code == 200

    # Verify it's deleted (should return 404)
    get_response = auth_client.get(f"/timeline/posts/{post_id}")
    assert get_response.status_code == 404


def test_create_comment(auth_client):
    """Test creating a comment on a post."""
    # First create a post
    post_data = {"content": "Post for commenting"}
    post_response = auth_client.post("/timeline/posts", json=post_data)
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]

    # Create a comment
    comment_data = {"content": "This is a great post!", "post_id": post_id}
    response = auth_client.post("/timeline/comments", json=comment_data)
    assert response.status_code == 200

    data = response.json()
    assert data["content"] == comment_data["content"]
    assert data["post_id"] == post_id
    assert "id" in data


def test_get_comments(client):
    """Test getting comments."""
    response = client.get("/timeline/comments")
    assert response.status_code == 200

    data = response.json()
    assert "comments" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["comments"], list)


def test_get_comments_by_post_id(auth_client):
    """Test getting comments filtered by post ID."""
    # Create a post
    post_data = {"content": "Post with comments"}
    post_response = auth_client.post("/timeline/posts", json=post_data)
    post_id = post_response.json()["id"]

    # Create multiple comments
    for i in range(3):
        comment_data = {"content": f"Comment {i + 1}", "post_id": post_id}
        auth_client.post("/timeline/comments", json=comment_data)

    # Get comments for this post
    response = auth_client.get(f"/timeline/comments?post_id={post_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 3
    for comment in data["comments"]:
        assert comment["post_id"] == post_id


def test_update_comment(auth_client):
    """Test updating a comment."""
    # Create a post and comment
    post_data = {"content": "Post for comment update"}
    post_response = auth_client.post("/timeline/posts", json=post_data)
    post_id = post_response.json()["id"]

    comment_data = {"content": "Original comment", "post_id": post_id}
    comment_response = auth_client.post("/timeline/comments", json=comment_data)
    comment_id = comment_response.json()["id"]

    # Update the comment
    update_data = {"content": "Updated comment"}
    response = auth_client.put(f"/timeline/comments/{comment_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["content"] == update_data["content"]


def test_delete_comment(auth_client):
    """Test deleting a comment."""
    # Create a post and comment
    post_data = {"content": "Post for comment deletion"}
    post_response = auth_client.post("/timeline/posts", json=post_data)
    post_id = post_response.json()["id"]

    comment_data = {"content": "Comment to be deleted", "post_id": post_id}
    comment_response = auth_client.post("/timeline/comments", json=comment_data)
    comment_id = comment_response.json()["id"]

    # Delete the comment
    response = auth_client.delete(f"/timeline/comments/{comment_id}")
    assert response.status_code == 200

    # Verify it's deleted (should return 404)
    get_response = auth_client.get(f"/timeline/comments/{comment_id}")
    assert get_response.status_code == 404


def test_unauthorized_post_creation(unauthorized_client):
    """Test that creating a post without authentication fails."""
    post_data = {"content": "Unauthorized post"}
    response = unauthorized_client.post("/timeline/posts", json=post_data)
    assert response.status_code == 403


def test_unauthorized_comment_creation(unauthorized_client):
    """Test that creating a comment without authentication fails."""
    comment_data = {"content": "Unauthorized comment", "post_id": "some-post-id"}
    response = unauthorized_client.post("/timeline/comments", json=comment_data)
    assert response.status_code == 403


def test_post_with_comments_included(auth_client):
    """Test getting a post with comments included."""
    # Create a post
    post_data = {"content": "Post with included comments"}
    post_response = auth_client.post("/timeline/posts", json=post_data)
    post_id = post_response.json()["id"]

    # Add some comments
    for i in range(2):
        comment_data = {"content": f"Included comment {i + 1}", "post_id": post_id}
        auth_client.post("/timeline/comments", json=comment_data)

    # Get post with comments
    response = auth_client.get(f"/timeline/posts/{post_id}?include_comments=true")
    assert response.status_code == 200

    data = response.json()
    assert "comments" in data
    assert len(data["comments"]) >= 2
    assert "comments_count" in data
    assert data["comments_count"] >= 2
