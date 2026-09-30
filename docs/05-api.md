# 5. REST API

[← Contents](README.md)

The live, always-current reference is Swagger at **`/swagger/`** (or ReDoc at `/redoc/`). This page gives an overview by domain.

## General rules

| Topic | Behavior |
|---|---|
| **Auth** | `Authorization: Bearer <access JWT>`. Access token lives 10 days, refresh token 20 days (rotated on refresh). |
| **Default permission** | `IsAuthenticated`. Public endpoints set `AllowAny` explicitly. |
| **Pagination** | `CursorPagination`, page size 20. Some lists use `PageNumberPagination` (publishers, auto-follow). |
| **Format** | JSON only (`JSONRenderer`). |
| **Versioning** | Three URL namespaces: `/api/` (v1), `/api/v2/` (newer versions of v1 endpoints), `/api_v2/` (v2 content model). |
| **Identifiers** | Paths take `global_id` (UUID), not the DB `id`. |

## Authentication — `/auth/`

| Method | Path | Description |
|---|---|---|
| POST | `/auth/jwt/create/` | Log in with email + password, returns `access` / `refresh` |
| POST | `/auth/jwt/refresh/` | Refresh tokens (custom serializer) |
| POST | `/auth/jwt/verify/` | Verify a token |
| POST | `/auth/social/<provider>/` | Social login (google-oauth2, facebook, apple-id) |
| POST | `/auth/social/<provider>/<partial_token>` | Finish social registration (username, birthday, etc.) |
| * | `/auth/users/…` | djoser `UserViewSet`: sign-up, `me`, password reset, deletion |

## Registration helpers — `/api/`

| Method | Path | Description |
|---|---|---|
| POST | `is_valid_username` | Check username availability and format |
| POST | `draft_user` | Send an email confirmation code |
| POST | `draft_user/<code>` | Confirm the code |
| GET | `auto_follow` | Accounts suggested for auto-follow |
| GET | `env_var` | Current Android app version (public) |
| GET | `join_link` | Invite link (public) |

## Profile — `/api/profile…`, `/api/v2/profile…`

| Method | Path | Description |
|---|---|---|
| GET / PATCH / DELETE | `profile` | Own profile |
| GET | `profile/<global_id or username>?option=username` | Another user's profile |
| POST | `profile_image` | Upload an avatar |
| GET | `profile_qrcode` | Profile QR code |
| GET | `profile/following`, `profile/followers`, `profile/subscriptions` | Following / followers / follows |
| PUT / DELETE | `profile/categories_subscription/<id>` | Follow / unfollow a category |
| PUT / DELETE | `profile/publishers_subscription/<id>` | Follow / unfollow a publisher or user |
| GET | `api/v2/profile/categories_subscription/`, `…/publishers_subscription/` | List own follows |
| POST | `profile/report/` | Report a user |
| GET / POST | `profile/block/` | Blocked list / block a user |
| DELETE | `profile/block/<global_id>` | Unblock |
| GET | `profile/web/<username>` | Public web profile (no auth) |
| GET / POST | `profile/creators/socials` | Creator's connected socials |
| DELETE | `profile/creators/socials/<id>` | Disconnect a social |

## Catalogs

| Method | Path | Description |
|---|---|---|
| GET | `api/categories` | All categories (public) |
| GET | `api/categories/main` | Main categories |
| GET | `api/popular/categories` | Navigation categories (name kept for iOS) |
| GET | `api/favorite/categories` | Favorite categories |
| GET | `api/subcategories/<global_id>` | Subcategories |
| GET | `api/publishers` | All active accounts, searchable (`?search=`) |
| GET | `api/newsstand` | Publishers only (`is_source=True`) |
| GET | `api/vylo_publishers` | Users and creators only |
| GET | `api/search_trending` | Trending searches |

## Posts

### v1 (`ColumnNews`)
| Method | Path | Description |
|---|---|---|
| GET | `api/news` | Own posts (excluding Draft/Deleted), sorted by `-published` |
| PUT / PATCH / DELETE | `api/news_update/<global_id>` | Edit or delete own post (`IsNewsOwner`) |
| POST | `api/news_report` | Report a post |
| GET | `api/generate_presigned_url/<ext>?file_type=video\|audio` | Create a draft and get an S3 presigned URL |
| PUT | `api/generate_presigned_url_cover/<global_id>` | Update the thumbnail |
| GET | `api/v2/news`, `api/v2/news/<global_id>` | v2 serialization with reply counters |

Legacy aliases `my_columnnews*` and `columnnews_*` are marked "TODO delete".

### v2 (`UserNews`)
| Method | Path | Description |
|---|---|---|
| GET | `api_v2/generate_presigned_url/?file_type=&duration=&width=&height=&thumbnail_file_ext=&lineup_global_id=` | Create `UserNews` + media, return two presigned URLs (content and thumbnail) |
| PUT / DELETE | `api_v2/news_update/<global_id>/` | Publish, edit or delete a post |

Example `generate_presigned_url` response:

```json
{
  "news_record_id": 123,
  "news_record_global_id": "…uuid…",
  "media_record_id": 456,
  "media_record_global_id": "…uuid…",
  "content_file_name": "<media_global_id>.mp4",
  "content_presigned_url": "https://…s3…",
  "thumbnail_presigned_url": "https://…s3…",
  "lineup_global_id": null
}
```

## Comments

| Method | Path | Description |
|---|---|---|
| POST | `api/comments` | Create a comment (v1) |
| GET / PUT / DELETE | `api/comments/<global_id>` | v1 comment |
| POST | `api_v2/comments/` | Create a comment (v2, tree) |
| DELETE | `api_v2/comments/<global_id>/` | Delete a comment (v2) |
