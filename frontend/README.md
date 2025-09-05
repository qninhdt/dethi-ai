# DethiAI Frontend

A modern Next.js application for AI-powered exam generation from uploaded documents.

## Features

- 🔐 **Firebase Authentication** - Google sign-in only
- 📄 **Document Upload** - Support for PDF and DOCX files  
- 🧠 **AI Processing** - OCR and question extraction with real-time status
- ❓ **Question Management** - View and select extracted questions
- 🎯 **Exam Generation** - Create new exams based on selected questions
- 📊 **Real-time Progress** - Live status updates for generation process
- 🎨 **Markdown Rendering** - Full Markdown support for mathematical content
- 🌙 **Dark Mode** - System-aware theme switching
- 📱 **Responsive Design** - Works on all devices
- 🚀 **Modern UI** - Built with ShadCN components

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS + ShadCN UI components
- **Authentication**: Firebase Auth
- **Markdown**: Markdown.js for mathematical rendering
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Firebase project with Google authentication enabled

### Installation

1. **Clone and navigate**:
   ```bash
   git clone <repository>
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your Firebase configuration:
   ```env
   NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
app/                    # Next.js App Router pages
├── documents/         # Document management pages
│   ├── [docId]/      # Document detail page
│   │   └── exams/    # Generated exam pages
│   └── page.tsx      # Documents list
├── upload/           # Document upload page
├── layout.tsx        # Root layout with providers
└── page.tsx         # Homepage

components/            # Reusable components
├── ui/              # ShadCN UI components
├── auth-provider.tsx # Authentication context
├── theme-provider.tsx# Theme management
├── header.tsx       # Navigation header
├── markdown.tsx        # Markdown rendering component
├── loading.tsx      # Loading states
└── sign-in.tsx     # Sign-in component

lib/                  # Utilities and configuration
├── api.ts           # API client functions
├── firebase.ts      # Firebase configuration
└── utils.ts        # Utility functions
```

## Key Features

### Authentication
- Google-only authentication via Firebase
- Automatic redirect for unauthenticated users
- User profile management in header

### Document Management
- Drag-and-drop file upload
- File validation (PDF/DOCX, 50MB max)
- Real-time processing status tracking
- OCR and extraction progress visualization

### Question System
- Markdown-rendered mathematical content
- Multiple question types (multiple choice, true/false, short answer)
- Question selection for exam generation
- Bulk select/deselect functionality

### Exam Generation
- Real-time generation progress
- Per-question status tracking
- Show/hide answers toggle
- Export to Markdown, PDF, and DOCX formats

### Markdown Support
- Full mathematical formula rendering
- Inline and display math modes
- Custom styling for dark mode
- Error fallback to plain text

## API Integration

The frontend communicates with the DethiAI backend API:

- **Upload**: `POST /documents` with multipart file
- **Document Info**: `GET /documents/{id}`
- **Questions**: `GET /documents/{id}/questions`
- **Generate**: `POST /documents/{id}/generate`
- **Exam Status**: `GET /documents/{id}/exams/{genId}`
- **Export**: `GET /documents/{id}/exams/{genId}/export`

All requests include Firebase ID token for authentication.

## Theming

The application uses CSS custom properties for theming:

- Light/dark mode support
- System preference detection
- Semantic color tokens (primary, secondary, accent, etc.)
- No hardcoded colors in components

## Development

### Adding New Components
1. Create component in appropriate directory
2. Use semantic color classes (e.g., `text-primary`, `bg-secondary`)
3. Include TypeScript interfaces
4. Add proper error handling

### Markdown Integration

For Markdown content, use the `<Markdown>` component:

```tsx
import { Markdown } from '@/components/markdown';

// Inline math
<Markdown>$x^2 + y^2 = z^2$</Markdown>

// Display math
<Markdown displayMode>$$\int_0^\infty e^{-x} dx = 1$$</Markdown>
```

### State Management

- Authentication: React Context (`useAuth`)
- Theme: React Context (`useTheme`)
- API state: Local component state with useEffect
- Forms: React Hook Form with Zod schemas

## Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment Variables

Required for production:
- All Firebase configuration variables
- API base URL pointing to production backend
- Any additional analytics or monitoring keys

### Considerations

- Ensure Firebase project has correct domains configured
- Backend API must handle CORS for your domain
- Consider implementing proper error tracking (Sentry, etc.)
- Set up monitoring for performance and uptime

## Contributing

1. Follow the existing code style
2. Use TypeScript strictly
3. Add proper error handling
4. Test Markdown rendering thoroughly
5. Ensure responsive design
6. Follow accessibility best practices

## License

This project is part of the DethiAI application suite.
