# KiteLMS

KiteLMS is a learning management system that allows users to create, manage, and track courses.

## Features

- Create and manage courses
- Track course progress
- Assign and grade assignments
- Communicate with students and instructors
- Integrate with external tools and platforms

## Test Coverage

| File | Statements | Missing | Coverage |
|------|------------|---------|----------|
| backend/core/settings.py | 29 | 0 | 100% |
| backend/main.py | 28 | 2 | 93% |
| backend/models/database.py | 87 | 0 | 100% |
| backend/models/engine.py | 6 | 2 | 67% |
| backend/modules/auth/auth_methods.py | 36 | 17 | 53% |
| backend/modules/auth/auth_routes.py | 38 | 3 | 92% |
| backend/modules/auth/auth_schema.py | 15 | 0 | 100% |
| backend/modules/courses/course_methods.py | 98 | 9 | 91% |
| backend/modules/courses/course_routes.py | 71 | 9 | 87% |
| backend/modules/courses/course_schema.py | 38 | 0 | 100% |
| backend/modules/discussions/discussion_methods.py | 64 | 3 | 95% |
| backend/modules/discussions/discussion_routes.py | 52 | 10 | 81% |
| backend/modules/discussions/discussion_schema.py | 21 | 0 | 100% |
| backend/modules/enrollments/enrollment_methods.py | 73 | 12 | 84% |
| backend/modules/enrollments/enrollment_routes.py | 57 | 21 | 63% |
| backend/modules/enrollments/enrollment_schema.py | 41 | 0 | 100% |
| backend/modules/lessons/lesson_methods.py | 92 | 3 | 97% |
| backend/modules/lessons/lesson_routes.py | 64 | 11 | 83% |
| backend/modules/lessons/lesson_schema.py | 33 | 0 | 100% |
| backend/modules/sections/section_methods.py | 83 | 1 | 99% |
| backend/modules/sections/section_routes.py | 64 | 11 | 83% |
| backend/modules/sections/section_schema.py | 41 | 0 | 100% |
| backend/modules/timeline/timeline_methods.py | 127 | 18 | 86% |
| backend/modules/timeline/timeline_routes.py | 95 | 31 | 67% |
| backend/modules/timeline/timeline_schema.py | 43 | 0 | 100% |
| backend/modules/users/user_methods.py | 105 | 12 | 89% |
| backend/modules/users/user_routes.py | 86 | 16 | 81% |
| backend/modules/users/user_schema.py | 23 | 0 | 100% |
| backend/utils/ids.py | 3 | 0 | 100% |
| backend/utils/models.py | 8 | 0 | 100% |

---

TOTAL 1621 191 88%
