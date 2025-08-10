# KiteLMS

KiteLMS is a learning management system that allows users to create, manage, and track courses.

## Features

- Create and manage courses
- Track course progress
- Assign and grade assignments
- Communicate with students and instructors
- Integrate with external tools and platforms

# API Endpoints

This document lists all available API endpoints in the KiteLMS backend with their parameters and request bodies.

## Authentication Endpoints

### `POST /auth/register`

**Body:**

```json
{
  "name": "string",
  "email": "string",
  "password": "string"
}
```

### `POST /auth/login`

**Body:**

```json
{
  "email": "string",
  "password": "string"
}
```

## Course Endpoints

### `POST /courses/`

**Body:**

```json
{
  "name": "string",
  "description": "string",
  "cover_image_url": "string (optional)",
  "video_preview_url": "string (optional)",
  "price": "number (optional, default: 0.0)",
  "category": "string (optional)",
  "tags": "string (optional)",
  "is_published": "boolean (optional, default: false)"
}
```

### `GET /courses/`

**Query Parameters:**

- `skip`: integer (optional, default: 0) - Number of records to skip
- `limit`: integer (optional, default: 10, max: 100) - Number of records to return
- `user_id`: string (optional) - Filter by user ID
- `is_published`: boolean (optional) - Filter by publication status
- `category`: string (optional) - Filter by category
- `search`: string (optional) - Search in name, description, or tags
- `my_courses`: boolean (optional, default: false) - Filter by current user's courses

### `GET /courses/{course_id}`

**Path Parameters:**

- `course_id`: string - Course ID

### `PUT /courses/{course_id}`

**Path Parameters:**

- `course_id`: string - Course ID

**Body:**

```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "cover_image_url": "string (optional)",
  "video_preview_url": "string (optional)",
  "price": "number (optional)",
  "category": "string (optional)",
  "tags": "string (optional)",
  "is_published": "boolean (optional)"
}
```

### `DELETE /courses/{course_id}`

**Path Parameters:**

- `course_id`: string - Course ID

### `POST /courses/{course_id}/publish`

**Path Parameters:**

- `course_id`: string - Course ID

### `POST /courses/{course_id}/unpublish`

**Path Parameters:**

- `course_id`: string - Course ID

## Section Endpoints

### `POST /sections/`

**Body:**

```json
{
  "name": "string",
  "description": "string (optional)",
  "order": "integer",
  "course_id": "string"
}
```

### `GET /sections/`

**Query Parameters:**

- `skip`: integer (optional, default: 0) - Number of records to skip
- `limit`: integer (optional, default: 10, max: 100) - Number of records to return
- `course_id`: string (optional) - Filter by course ID

### `GET /sections/{section_id}/with-lessons`

**Path Parameters:**

- `section_id`: string - Section ID

### `PUT /sections/{section_id}`

**Path Parameters:**

- `section_id`: string - Section ID

**Body:**

```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "order": "integer (optional)"
}
```

### `DELETE /sections/{section_id}`

**Path Parameters:**

- `section_id`: string - Section ID

### `PUT /sections/reorder`

**Body:**

```json
{
  "course_id": "string",
  "section_orders": [
    {
      "id": "string",
      "order": "integer"
    }
  ]
}
```

## Lesson Endpoints

### `POST /lessons/`

**Body:**

```json
{
  "title": "string",
  "content": "string (optional)",
  "video_url": "string (optional)",
  "order": "integer",
  "section_id": "string"
}
```

### `GET /lessons/`

**Query Parameters:**

- `skip`: integer (optional, default: 0) - Number of records to skip
- `limit`: integer (optional, default: 10, max: 100) - Number of records to return
- `section_id`: string (optional) - Filter by section ID

### `GET /lessons/{lesson_id}`

**Path Parameters:**

- `lesson_id`: string - Lesson ID

### `PUT /lessons/{lesson_id}`

**Path Parameters:**

- `lesson_id`: string - Lesson ID

**Body:**

```json
{
  "title": "string (optional)",
  "content": "string (optional)",
  "video_url": "string (optional)",
  "order": "integer (optional)"
}
```

### `DELETE /lessons/{lesson_id}`

**Path Parameters:**

- `lesson_id`: string - Lesson ID

### `PUT /lessons/reorder`

**Body:**

```json
{
  "section_id": "string",
  "lesson_orders": [
    {
      "id": "string",
      "order": "integer"
    }
  ]
}
```

## User Endpoints

### `GET /users/`

**Query Parameters:**

- `skip`: integer (optional, default: 0) - Number of records to skip
- `limit`: integer (optional, default: 10, max: 100) - Number of records to return
- `search`: string (optional) - Search in user name or email
- `role`: string (optional) - Filter by user role
- `include_deleted`: boolean (optional, default: false) - Include deleted users

**Note:** Only admins can access this endpoint.

### `GET /users/{user_id}`

**Path Parameters:**

- `user_id`: string - User ID

**Note:** Users can only access their own profile unless they are admin.

### `PATCH /users/{user_id}`

**Path Parameters:**

- `user_id`: string - User ID

**Body:**

```json
{
  "name": "string (optional)",
  "email": "string (optional)",
  "password": "string (optional)",
  "role": "string (optional)"
}
```

**Note:** Users can only update their own profile unless they are admin.

### `DELETE /users/{user_id}`

**Path Parameters:**

- `user_id`: string - User ID

**Note:** Only admins can delete users.

### `POST /users/{user_id}/ban`

**Path Parameters:**

- `user_id`: string - User ID

**Body:**

```json
{
  "reason": "string (optional)"
}
```

**Note:** Only admins can ban users.

### `POST /users/{user_id}/unban`

**Path Parameters:**

- `user_id`: string - User ID

**Note:** Only admins can unban users.
