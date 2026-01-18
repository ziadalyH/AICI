# MongoDB Database Structure

## Database Overview

**Database Name**: `hybrid_rag_qa` (configurable via `MONGODB_DB_NAME` env var)  
**Connection**: `mongodb://mongodb:27017/` (in Docker) or `mongodb://localhost:27017/` (local)

---

## Collections

### 1. `users` Collection

Stores user authentication information.

#### Document Structure

```json
{
  "_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "password_hash": "$2b$12$KIXxLV8Hn8FqVqP.Zx9Zxe...",
  "created_at": "2026-01-18T10:30:00.000Z"
}
```

#### Fields

| Field           | Type          | Description                | Required | Unique |
| --------------- | ------------- | -------------------------- | -------- | ------ |
| `_id`           | String (UUID) | User ID (primary key)      | Yes      | Yes    |
| `username`      | String        | Username for login         | Yes      | Yes    |
| `password_hash` | String        | Bcrypt hashed password     | Yes      | No     |
| `created_at`    | DateTime      | Account creation timestamp | Yes      | No     |

#### Indexes

- **Unique index** on `username` (ascending)
- **Primary key** on `_id`

#### Example Documents

```json
// User 1
{
  "_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "architect_user",
  "password_hash": "$2b$12$abcdefghijklmnopqrstuvwxyz123456789",
  "created_at": "2026-01-15T08:00:00.000Z"
}

// User 2
{
  "_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "username": "designer_user",
  "password_hash": "$2b$12$zyxwvutsrqponmlkjihgfedcba987654321",
  "created_at": "2026-01-16T14:30:00.000Z"
}
```

---

### 2. `user_objects` Collection

Stores ephemeral drawing JSON objects per user session.

#### Document Structure

```json
{
  "_id": "ObjectId('65a7f8b9c1d2e3f4a5b6c7d8')",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "objects": [
    {
      "type": "POLYLINE",
      "layer": "Walls",
      "points": [
        [0, 0],
        [10000, 0],
        [10000, 8000],
        [0, 8000]
      ],
      "closed": true
    },
    {
      "type": "POLYLINE",
      "layer": "Plot Boundary",
      "points": [
        [0, 0],
        [20000, 0],
        [20000, 20000],
        [0, 20000]
      ],
      "closed": true
    }
  ],
  "created_at": "2026-01-18T10:30:00.000Z",
  "updated_at": "2026-01-18T11:45:00.000Z"
}
```

#### Fields

| Field        | Type          | Description                    | Required | Unique |
| ------------ | ------------- | ------------------------------ | -------- | ------ |
| `_id`        | ObjectId      | MongoDB auto-generated ID      | Yes      | Yes    |
| `user_id`    | String (UUID) | Reference to user              | Yes      | No     |
| `objects`    | Array         | List of drawing objects (JSON) | Yes      | No     |
| `created_at` | DateTime      | First upload timestamp         | Yes      | No     |
| `updated_at` | DateTime      | Last update timestamp          | Yes      | No     |

#### Indexes

- **Index** on `user_id` (ascending)

#### Objects Array Structure

Each object in the `objects` array can have any structure (flexible schema), but typically contains:

```json
{
  "type": "POLYLINE",           // Drawing element type
  "layer": "Walls",             // Layer name
  "points": [[x1, y1], [x2, y2]], // Coordinates
  "closed": true,               // Whether shape is closed
  "properties": {               // Optional properties
    "color": "#000000",
    "lineWeight": 0.25
  }
}
```

#### Example Documents

```json
// Simple drawing with walls and plot
{
  "_id": "ObjectId('65a7f8b9c1d2e3f4a5b6c7d8')",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "objects": [
    {
      "type": "POLYLINE",
      "layer": "Walls",
      "points": [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
      "closed": true
    },
    {
      "type": "POLYLINE",
      "layer": "Plot Boundary",
      "points": [[0, 0], [20000, 0], [20000, 20000], [0, 20000]],
      "closed": true
    }
  ],
  "created_at": "2026-01-18T10:30:00.000Z",
  "updated_at": "2026-01-18T10:30:00.000Z"
}

// Complex drawing with extension
{
  "_id": "ObjectId('65a7f8b9c1d2e3f4a5b6c7d9')",
  "user_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "objects": [
    {
      "type": "POLYLINE",
      "layer": "Walls",
      "points": [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
      "closed": true
    },
    {
      "type": "POLYLINE",
      "layer": "Walls",
      "points": [[3000, 8000], [7000, 8000], [7000, 15000], [3000, 15000]],
      "closed": true
    },
    {
      "type": "POLYLINE",
      "layer": "Plot Boundary",
      "points": [[0, 0], [20000, 0], [20000, 20000], [0, 20000]],
      "closed": true
    },
    {
      "type": "LINE",
      "layer": "Highway",
      "points": [[-5000, 0], [25000, 0]]
    }
  ],
  "created_at": "2026-01-17T09:00:00.000Z",
  "updated_at": "2026-01-18T11:45:00.000Z"
}
```

---

## Database Operations

### User Operations

#### Create User

```python
user = db.create_user(username="john_doe", password="secure_password")
# Returns: User(id="uuid", username="john_doe", ...)
```

#### Get User by Username

```python
user = db.get_user_by_username(username="john_doe")
# Returns: User object or None
```

#### Get User by ID

```python
user = db.get_user_by_id(user_id="uuid")
# Returns: User object or None
```

#### Verify Password

```python
is_valid = db.verify_password(plain_password="password", hashed_password=user.password_hash)
# Returns: True or False
```

### Object Operations

#### Save Objects (Upsert)

```python
db.save_user_objects(
    user_id="uuid",
    objects=[
        {"type": "POLYLINE", "layer": "Walls", "points": [[0,0], [10,0]]},
        {"type": "POLYLINE", "layer": "Plot Boundary", "points": [[0,0], [20,0]]}
    ]
)
# Creates new document or updates existing one
```

#### Get Objects

```python
result = db.get_user_objects(user_id="uuid")
# Returns: {
#   "objects": [...],
#   "created_at": datetime,
#   "updated_at": datetime
# }
```

#### Delete Objects

```python
db.delete_user_objects(user_id="uuid")
# Removes all objects for the user
```

---

## API Endpoints Using MongoDB

### Authentication Endpoints

#### POST `/api/auth/register`

**MongoDB Operation**: `users.insert_one()`

```json
Request:
{
  "username": "john_doe",
  "password": "secure_password"
}

Response:
{
  "message": "User registered successfully",
  "user_id": "uuid"
}
```

#### POST `/api/auth/login`

**MongoDB Operation**: `users.find_one({"username": ...})`

```json
Request:
{
  "username": "john_doe",
  "password": "secure_password"
}

Response:
{
  "token": "jwt_token_here",
  "token_type": "bearer"
}
```

#### GET `/api/auth/me`

**MongoDB Operation**: `users.find_one({"_id": ...})`

```json
Response:
{
  "id": "uuid",
  "username": "john_doe",
  "created_at": "2026-01-18T10:30:00.000Z"
}
```

### Session Endpoints

#### POST `/api/session/objects`

**MongoDB Operation**: `user_objects.update_one(..., upsert=True)`

```json
Request:
{
  "objects": [
    {"type": "POLYLINE", "layer": "Walls", "points": [[0,0], [10,0]]}
  ]
}

Response:
{
  "message": "Objects saved successfully",
  "count": 1,
  "updated_at": "2026-01-18T11:45:00.000Z"
}
```

#### GET `/api/session/objects`

**MongoDB Operation**: `user_objects.find_one({"user_id": ...})`

```json
Response:
{
  "objects": [...],
  "created_at": "2026-01-18T10:30:00.000Z",
  "updated_at": "2026-01-18T11:45:00.000Z"
}
```

---

## Querying MongoDB Directly

### Connect to MongoDB Container

```bash
docker exec -it hybrid-rag-mongodb mongosh
```

### Switch to Database

```javascript
use hybrid_rag_qa
```

### View Collections

```javascript
show collections
// Output: users, user_objects
```

### Query Users

```javascript
// Find all users
db.users.find().pretty();

// Find specific user
db.users.findOne({ username: "john_doe" });

// Count users
db.users.countDocuments();
```

### Query User Objects

```javascript
// Find all user objects
db.user_objects.find().pretty();

// Find objects for specific user
db.user_objects.findOne({ user_id: "uuid" });

// Count user objects
db.user_objects.countDocuments();
```

### Useful Queries

```javascript
// Get all usernames
db.users.find({}, { username: 1, _id: 0 });

// Get users created today
db.users.find({
  created_at: {
    $gte: new Date(new Date().setHours(0, 0, 0, 0)),
  },
});

// Get users with objects
db.user_objects.aggregate([
  {
    $lookup: {
      from: "users",
      localField: "user_id",
      foreignField: "_id",
      as: "user",
    },
  },
]);

// Count objects per user
db.user_objects.aggregate([
  {
    $project: {
      user_id: 1,
      object_count: { $size: "$objects" },
    },
  },
]);
```

---

## Data Flow

```
User Registration
    ↓
POST /api/auth/register
    ↓
db.create_user()
    ↓
users.insert_one()
    ↓
Return user_id

User Login
    ↓
POST /api/auth/login
    ↓
db.get_user_by_username()
    ↓
users.find_one({username: ...})
    ↓
db.verify_password()
    ↓
Return JWT token

Upload Drawing
    ↓
POST /api/session/objects
    ↓
db.save_user_objects()
    ↓
user_objects.update_one(..., upsert=True)
    ↓
Return success

Query with Drawing
    ↓
POST /api/query
    ↓
db.get_user_objects()
    ↓
user_objects.find_one({user_id: ...})
    ↓
Send to AI Agent with drawing JSON
    ↓
Return answer
```

---

## Backup and Restore

### Backup Database

```bash
docker exec hybrid-rag-mongodb mongodump --db hybrid_rag_qa --out /tmp/backup
docker cp hybrid-rag-mongodb:/tmp/backup ./mongodb_backup
```

### Restore Database

```bash
docker cp ./mongodb_backup hybrid-rag-mongodb:/tmp/backup
docker exec hybrid-rag-mongodb mongorestore --db hybrid_rag_qa /tmp/backup/hybrid_rag_qa
```

---

## Security

### Password Hashing

- **Algorithm**: bcrypt
- **Rounds**: 12 (default)
- **Library**: passlib with bcrypt scheme

### Authentication

- **Method**: JWT tokens
- **Storage**: localStorage (frontend)
- **Transmission**: Bearer token in Authorization header

### Database Access

- **Network**: Internal Docker network only
- **Port**: 27017 (exposed for development)
- **Authentication**: None (should be added for production)

---

## Production Recommendations

1. **Enable MongoDB Authentication**

   ```yaml
   environment:
     - MONGO_INITDB_ROOT_USERNAME=admin
     - MONGO_INITDB_ROOT_PASSWORD=secure_password
   ```

2. **Add Indexes for Performance**

   ```javascript
   db.user_objects.createIndex({ updated_at: -1 });
   db.users.createIndex({ created_at: -1 });
   ```

3. **Set Up Replication**
   - Use MongoDB replica set
   - Enable automatic failover

4. **Regular Backups**
   - Automated daily backups
   - Store in secure location

5. **Monitor Performance**
   - Track query performance
   - Monitor collection sizes
   - Set up alerts

---

**Database Version**: MongoDB 7.0  
**Driver**: PyMongo  
**ORM**: None (direct MongoDB operations)
