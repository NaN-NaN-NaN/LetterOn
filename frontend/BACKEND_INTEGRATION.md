# LetterOn Frontend - Backend Integration Guide

## Backend API Configuration

The LetterOn backend server is running at `http://localhost:8000` (development).

### Environment Variables

Configure the API URL in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Endpoints Available

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user info

#### Letters
- `POST /letters/process-images` - Upload and process letter images
- `GET /letters` - List letters (with filters)
- `GET /letters/{id}` - Get letter details
- `PATCH /letters/{id}` - Update letter
- `DELETE /letters/{id}` - Delete letter
- `POST /letters/{id}/snooze` - Snooze letter
- `POST /letters/{id}/archive` - Archive letter
- `POST /letters/{id}/restore` - Restore letter
- `POST /letters/{id}/translate` - Translate letter

#### Chat
- `POST /chat` - Chat with AI about a letter

#### Search
- `GET /search?q=query` - Search letters

#### Reminders
- `POST /reminders` - Create reminder
- `GET /reminders` - List reminders
- `PATCH /reminders/{id}` - Update reminder
- `DELETE /reminders/{id}` - Delete reminder

## Usage Examples

### 1. User Registration

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function register(name: string, email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, email, password }),
  });

  if (!response.ok) {
    throw new Error('Registration failed');
  }

  const data = await response.json();
  // Save token to localStorage
  localStorage.setItem('token', data.token);
  return data;
}
```

### 2. User Login

```typescript
async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();
  localStorage.setItem('token', data.token);
  return data;
}
```

### 3. Upload Letter Images

```typescript
async function uploadLetterImages(files: File[]) {
  const token = localStorage.getItem('token');

  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_URL}/letters/process-images`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return await response.json();
}
```

### 4. Get Letters

```typescript
async function getLetters(filters?: {
  archived?: boolean;
  deleted?: boolean;
  category?: string;
}) {
  const token = localStorage.getItem('token');

  const params = new URLSearchParams();
  if (filters?.archived !== undefined) params.set('archived', String(filters.archived));
  if (filters?.deleted !== undefined) params.set('deleted', String(filters.deleted));
  if (filters?.category) params.set('category', filters.category);

  const response = await fetch(`${API_URL}/letters?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch letters');
  }

  return await response.json();
}
```

### 5. Update Letter

```typescript
async function updateLetter(letterId: string, updates: {
  subject?: string;
  letterCategory?: string;
  actionStatus?: string;
  flagged?: boolean;
  read?: boolean;
}) {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_URL}/letters/${letterId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error('Failed to update letter');
  }

  return await response.json();
}
```

### 6. Chat with AI

```typescript
async function chatAboutLetter(letterId: string, message: string) {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      letter_id: letterId,
      message: message,
    }),
  });

  if (!response.ok) {
    throw new Error('Chat request failed');
  }

  return await response.json();
}
```

### 7. Search Letters

```typescript
async function searchLetters(query: string) {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Search failed');
  }

  return await response.json();
}
```

### 8. Create Reminder

```typescript
async function createReminder(letterId: string, reminderTime: number, message?: string) {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_URL}/reminders`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      letter_id: letterId,
      reminder_time: reminderTime,
      message: message || '',
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to create reminder');
  }

  return await response.json();
}
```

## API Service Helper

Create a reusable API service (`lib/api.ts`):

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private getToken(): string | null {
    return localStorage.getItem('token');
  }

  private async request(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<any> {
    const token = this.getToken();

    const headers: HeadersInit = {
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: 'Request failed',
      }));
      throw new Error(error.detail || error.message || 'Request failed');
    }

    return await response.json();
  }

  // Auth
  async register(name: string, email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
  }

  async login(email: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async logout() {
    return this.request('/auth/logout', { method: 'POST' });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Letters
  async uploadLetters(files: File[]) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    return this.request('/letters/process-images', {
      method: 'POST',
      body: formData,
    });
  }

  async getLetters(params?: Record<string, any>) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/letters${query ? `?${query}` : ''}`);
  }

  async getLetter(id: string) {
    return this.request(`/letters/${id}`);
  }

  async updateLetter(id: string, updates: Record<string, any>) {
    return this.request(`/letters/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteLetter(id: string, permanent = false) {
    return this.request(`/letters/${id}?permanent=${permanent}`, {
      method: 'DELETE',
    });
  }

  async snoozeLetter(id: string, snoozeUntil: string) {
    return this.request(`/letters/${id}/snooze`, {
      method: 'POST',
      body: JSON.stringify({ snooze_until: snoozeUntil }),
    });
  }

  async archiveLetter(id: string) {
    return this.request(`/letters/${id}/archive`, { method: 'POST' });
  }

  async restoreLetter(id: string) {
    return this.request(`/letters/${id}/restore`, { method: 'POST' });
  }

  // Chat
  async chat(letterId: string, message: string) {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({ letter_id: letterId, message }),
    });
  }

  // Search
  async search(query: string) {
    return this.request(`/search?q=${encodeURIComponent(query)}`);
  }

  // Reminders
  async createReminder(letterId: string, reminderTime: number, message?: string) {
    return this.request('/reminders', {
      method: 'POST',
      body: JSON.stringify({
        letter_id: letterId,
        reminder_time: reminderTime,
        message: message || '',
      }),
    });
  }

  async getReminders() {
    return this.request('/reminders');
  }

  async updateReminder(id: string, updates: Record<string, any>) {
    return this.request(`/reminders/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteReminder(id: string) {
    return this.request(`/reminders/${id}`, { method: 'DELETE' });
  }
}

export const api = new APIClient();
```

## Error Handling

```typescript
import { toast } from 'sonner';

async function handleAPICall<T>(apiCall: Promise<T>): Promise<T | null> {
  try {
    return await apiCall;
  } catch (error) {
    if (error instanceof Error) {
      toast.error(error.message);
    } else {
      toast.error('An unexpected error occurred');
    }
    return null;
  }
}

// Usage
const result = await handleAPICall(api.getLetters());
if (result) {
  // Handle success
}
```

## Running the Full Stack

1. **Start Backend** (Terminal 1):
   ```bash
   cd letteron-server
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Start Frontend** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Data Flow Example

```
User uploads images → Frontend
                    ↓
                 FormData (multipart/form-data)
                    ↓
           POST /letters/process-images
                    ↓
              Backend receives
                    ↓
         Uploads to S3 → Gets S3 keys
                    ↓
      Calls LetterOnOCRHandler Lambda
                    ↓
           Receives OCR text
                    ↓
      Calls LetterOnLLMHandler Lambda
                    ↓
      Receives analysis (category, status, etc.)
                    ↓
        Saves to DynamoDB
                    ↓
   Returns structured letter data to Frontend
                    ↓
     Frontend displays processed letter
```

## Testing the Integration

1. **Register a user**:
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"name":"Test","email":"test@example.com","password":"test123456"}'
   ```

2. **Login**:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123456"}'
   ```

3. **Test from frontend**:
   - Open browser console
   - Use `api` object to make calls
   - Check Network tab for requests/responses

## Troubleshooting

### CORS Errors
If you see CORS errors, check:
1. Backend `.env` has correct `CORS_ORIGINS`
2. Frontend URL matches CORS origin
3. Backend server is running

### 401 Unauthorized
- Token expired (24 hours by default)
- Token not in localStorage
- Invalid token format
- Solution: Re-login

### Connection Refused
- Backend not running
- Wrong port in `.env.local`
- Check: `http://localhost:8000/health`

### Upload Fails
- File too large (max 1MB per file)
- More than 3 files
- Invalid file type
- No token in request

## Next Steps

1. Implement the API service in `lib/api.ts`
2. Create auth context for token management
3. Add loading states during API calls
4. Implement error toasts
5. Add retry logic for failed requests
6. Cache data using React Query or SWR

Happy coding! 🚀
