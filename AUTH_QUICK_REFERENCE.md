# Authentication - Quick Reference

## ✅ What You Have Now

### JWT Token System
- **Expiration**: 12 hours
- **Storage**: sessionStorage (default) or localStorage ("Remember Me")
- **Format**: Bearer token in Authorization header
- **Validation**: Automatic on every request

### Security Features
- ✅ Token expires in 12 hours
- ✅ Automatic logout on expiration
- ✅ Warning 1 hour before expiration
- ✅ All endpoints protected (except `/auth/*`)
- ✅ User ID extracted from token
- ✅ Passwords hashed with bcrypt

---

## Frontend Usage

### Check if User is Logged In

```typescript
import { useAuth } from '@/contexts/auth-context';

function MyComponent() {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <Spinner />;

  if (!isAuthenticated) {
    return <div>Please login</div>;
  }

  return <div>Welcome, {user.name}!</div>;
}
```

### Login

```typescript
const { login } = useAuth();

try {
  await login(email, password);
  // User is now logged in, token stored automatically
  router.push('/dashboard');
} catch (error) {
  // Show error message
}
```

### Logout

```typescript
const { logout } = useAuth();

await logout();
// Token removed, user redirected to login
```

### Make Authenticated API Calls

```typescript
import { api } from '@/lib/api';

// Token is automatically included in all requests
const letters = await api.letters.getAll();
const letter = await api.letters.getById(letterId);
```

---

## Backend Usage

### Protect an Endpoint

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user_id

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(user_id: str = Depends(get_current_user_id)):
    # user_id is automatically extracted from JWT token
    # 401 returned if token is invalid/expired

    return {"user_id": user_id, "data": "..."}
```

### Get Full User Object

```python
from app.dependencies import get_current_user

@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    # Full user object from database
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"]
    }
```

---

## API Endpoints

### Authentication Endpoints (No Token Required)

```bash
# Register
POST /auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "user_id": "uuid",
    "name": "John Doe",
    "email": "john@example.com"
  }
}

# Login
POST /auth/login
{
  "email": "john@example.com",
  "password": "securepassword123"
}

# Response (same as register)
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "user_id": "...", "name": "...", "email": "..." }
}
```

### Protected Endpoints (Token Required)

All other endpoints require Authorization header:

```bash
# Get current user
GET /auth/me
Headers: Authorization: Bearer {token}

# Get letters
GET /letters
Headers: Authorization: Bearer {token}

# Create reminder
POST /reminders
Headers: Authorization: Bearer {token}
Body: { "letter_id": "...", "reminder_time": 1234567890 }
```

---

## Token Flow

### Login/Register
1. User submits credentials
2. Backend validates and generates JWT (12 hours)
3. Frontend receives token
4. Token stored in browser (sessionStorage or localStorage)
5. User redirected to dashboard

### API Request
1. Frontend retrieves token from storage
2. Token added to Authorization header: `Bearer {token}`
3. Request sent to backend
4. Backend validates JWT signature and expiration
5. Backend extracts user_id from token
6. Request processed with authenticated user context
7. Response returned

### Token Expiration
1. Frontend checks token every minute
2. If expired: Automatic logout
3. If expiring soon (< 1 hour): Warning toast
4. Backend always validates on each request
5. If 401 returned: Frontend auto-logout

---

## Common Patterns

### Redirect Unauthenticated Users

```typescript
// In your page component
const { isAuthenticated, isLoading } = useAuth();

useEffect(() => {
  if (!isLoading && !isAuthenticated) {
    router.push('/auth');
  }
}, [isAuthenticated, isLoading]);
```

### Protect a Page

```typescript
// middleware.ts or page guard
export default function ProtectedPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" />;
  }

  return <YourPageContent />;
}
```

### Handle Expired Sessions

Frontend automatically handles this, but you can add custom behavior:

```typescript
import { setUnauthorizedHandler } from '@/lib/api';

// In your App or Layout component
useEffect(() => {
  setUnauthorizedHandler(() => {
    // Custom behavior on 401
    console.log('Session expired');
    router.push('/auth?expired=true');
  });
}, []);
```

---

## Testing

### Test Login Flow

```bash
# 1. Register/Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Save the token from response

# 2. Use token for protected endpoint
curl http://localhost:8000/letters \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 3. Test with invalid token (should return 401)
curl http://localhost:8000/letters \
  -H "Authorization: Bearer invalid-token"
```

---

## Environment Variables

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)

```env
SECRET_KEY=your-secret-key-min-32-chars-long-for-jwt-signing
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=12
```

---

## Troubleshooting

### "Session Expired" appearing immediately after login
- Check system clock (timezone issues)
- Verify `JWT_EXPIRATION_HOURS=12` in backend .env
- Check browser console for token expiration time

### 401 on all requests
- Verify token is being saved: Check browser DevTools → Application → Storage
- Check Authorization header in Network tab
- Verify backend is using same SECRET_KEY

### Token not persisting across page refreshes
- Check if token is in sessionStorage or localStorage
- Verify TokenStorage.setToken() is being called correctly
- Check browser storage is not disabled

---

## Key Files

### Frontend
- `frontend/lib/token-storage.ts` - Token storage logic
- `frontend/lib/api.ts` - API client with auth
- `frontend/contexts/auth-context.tsx` - Auth state management

### Backend
- `backend/app/services/auth.py` - JWT creation/validation
- `backend/app/dependencies.py` - Auth dependencies
- `backend/app/api/auth.py` - Auth endpoints
- `backend/.env` - JWT configuration

---

## Summary

✅ JWT tokens expire in 12 hours
✅ Tokens stored securely in browser
✅ All API requests include token automatically
✅ Backend validates every request
✅ Automatic logout on expiration
✅ User ID available in all protected endpoints

**You're all set!** The authentication system is fully functional and production-ready. 🎉
