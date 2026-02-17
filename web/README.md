# TechCare Bot - Web Frontend

Next.js 14 Frontend mit TypeScript, Tailwind CSS und shadcn/ui.

## Features

✅ **Modern Stack** - Next.js 14 App Router + TypeScript
✅ **Beautiful UI** - Tailwind CSS + shadcn/ui Components
✅ **Authentication** - JWT-based Auth mit Context
✅ **SSE Streaming** - Real-time Chat Responses
✅ **Responsive** - Mobile-first Design
✅ **Dark Mode Ready** - CSS Variables für Theming

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: React Context + SWR
- **Icons**: Lucide React
- **Markdown**: react-markdown + remark-gfm

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000

# Run dev server
npm run dev
```

Frontend läuft auf: **http://localhost:3000**

### Production Build

```bash
# Build
npm run build

# Start
npm start
```

### Docker

```bash
# Build
docker build -t techcare-web:latest \
  --build-arg NEXT_PUBLIC_API_URL=http://api:8000 \
  -f Dockerfile .

# Run
docker run -p 3000:3000 techcare-web:latest
```

## Project Structure

```
web/
├── app/                      # Next.js 14 App Router
│   ├── layout.tsx           # Root Layout (AuthProvider)
│   ├── page.tsx             # Landing / Login Page
│   ├── register/            # Registration Page
│   ├── dashboard/           # Dashboard Layout
│   │   ├── layout.tsx      # Dashboard Layout (Sidebar)
│   │   ├── page.tsx        # Dashboard Home
│   │   └── chat/           # Chat Routes
│   └── globals.css          # Global Styles (Tailwind)
│
├── components/               # React Components
│   ├── ui/                  # Base UI Components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   └── auth/                # Auth Components
│       └── login-form.tsx
│
├── contexts/                 # React Contexts
│   └── auth-context.tsx    # Global Auth State
│
├── lib/                      # Utilities
│   ├── api.ts              # API Client (fetch wrapper)
│   └── utils.ts            # Helper Functions
│
├── types/                    # TypeScript Types
│   └── index.ts            # API Response Types
│
├── hooks/                    # Custom Hooks
│   └── use-toast.ts        # Toast Notifications
│
├── public/                   # Static Assets
├── package.json              # Dependencies
├── tailwind.config.ts       # Tailwind Config
├── tsconfig.json            # TypeScript Config
└── next.config.js           # Next.js Config
```

## Pages & Routes

### Public Routes

- `/` - Landing / Login Page
- `/register` - Registration Page

### Protected Routes (Auth required)

- `/dashboard` - Dashboard Home
- `/dashboard/chat/new` - New Chat
- `/dashboard/chat/[id]` - Chat View

## Components Overview

### UI Components (shadcn/ui)

Base components aus Radix UI:

- `Button` - Primary actions
- `Input` - Form inputs
- `Label` - Form labels
- `Toast` - Notifications
- `Dialog` - Modals (TODO)
- `Avatar` - User avatars (TODO)
- `Dropdown` - Menus (TODO)

### Auth Components

- `LoginForm` - Email + Password Login
- Auth Context - Global authentication state

### Chat Components (TODO)

- `ChatInterface` - Main chat UI
- `MessageList` - Message history
- `MessageInput` - User input with send button
- `MessageBubble` - Individual message display
- `StreamingMessage` - SSE streaming indicator

## API Integration

### API Client (`lib/api.ts`)

Fetch wrapper mit:
- JWT Token Management (localStorage)
- Request/Response interceptors
- Type-safe methods
- SSE Streaming support

**Usage:**

```typescript
import { api } from '@/lib/api'

// Auth
await api.login(email, password)
await api.register(email, password, name)
const user = await api.getMe()
api.logout()

// Conversations
const conversations = await api.getConversations()
const conv = await api.createConversation(title, description)
const messages = await api.getMessages(convId)
await api.deleteConversation(convId)

// Chat Streaming
for await (const chunk of api.chatStream(convId, message)) {
  console.log(chunk)
}
```

### Auth Context (`contexts/auth-context.tsx`)

Global authentication state:

```typescript
import { useAuth } from '@/contexts/auth-context'

function Component() {
  const { user, loading, login, logout, register, refreshUser } = useAuth()

  if (loading) return <Loader />
  if (!user) return <LoginForm />

  return <Dashboard user={user} />
}
```

## Styling

### Tailwind CSS

Utility-first CSS framework mit Custom Config:

```tsx
<div className="flex items-center gap-4 p-6 bg-card rounded-lg border">
  <Button variant="default" size="lg">Primary</Button>
  <Button variant="outline" size="sm">Secondary</Button>
</div>
```

### CSS Variables

Theming via CSS variables (`app/globals.css`):

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... */
}

.dark {
  --primary: 217.2 91.2% 59.8%;
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... */
}
```

### Custom Classes

- `.message-fade-in` - Message animation
- `.prose` - Markdown styling
- Custom scrollbar styling

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

In Docker/Production:

```bash
NEXT_PUBLIC_API_URL=http://api:8000
# oder
NEXT_PUBLIC_API_URL=https://techcare.ihrefirma.de
```

## Development Tips

### Add new shadcn/ui component

```bash
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add dropdown-menu
```

### Type-safe API calls

All API responses are typed in `types/index.ts`:

```typescript
import { User, Conversation, Message } from '@/types'

const user: User = await api.getMe()
const conv: Conversation = await api.getConversation(id)
```

### Toast Notifications

```typescript
import { useToast } from '@/hooks/use-toast'

const { toast } = useToast()

toast({
  title: 'Erfolg',
  description: 'Operation erfolgreich',
})

toast({
  title: 'Fehler',
  description: 'Etwas ist schief gelaufen',
  variant: 'destructive',
})
```

## TODO

### High Priority

- [ ] Chat Interface (SSE Streaming)
- [ ] Message List Component
- [ ] Message Input Component
- [ ] Conversation List (Sidebar)
- [ ] Tool Execution Display
- [ ] State Badge (AUDIT, PLAN, LOCKED, etc.)

### Medium Priority

- [ ] Dark Mode Toggle
- [ ] User Settings Page
- [ ] Learning Dashboard (Cases)
- [ ] Admin Panel
- [ ] Search Conversations

### Low Priority

- [ ] Export Chat History
- [ ] Keyboard Shortcuts
- [ ] Mobile Optimization
- [ ] PWA Support

## Testing

```bash
# Unit Tests (TODO)
npm test

# E2E Tests (TODO)
npm run test:e2e
```

## Build & Deploy

### Vercel

```bash
vercel
```

### Docker Compose

See `../docker-compose.yml`

### Manual

```bash
npm run build
npm start
```

## License

Proprietary - Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
