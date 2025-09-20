# LegalSaathi React Frontend

Modern React frontend for LegalSaathi Document Advisor with 3D animations and enhanced UX.

## Features

- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **3D Animations**: Framer Motion animations for enhanced user experience
- **Radix UI Components**: Accessible, customizable UI components
- **Dark Theme**: Modern dark theme with gradient animations
- **Responsive Design**: Mobile-first responsive design
- **Real-time Features**: Live document analysis with progress indicators
- **Accessibility**: Full keyboard navigation and screen reader support

## Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library for React
- **Radix UI** - Accessible component primitives
- **Lucide React** - Beautiful icon library

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Development Server

The development server runs on `http://localhost:3000` and proxies API requests to the Flask backend on `http://localhost:5000`.

### Build Output

The build outputs to `dist/` directory, which is copied to the Flask `static/dist/` directory for production serving.

## Project Structure

```
client/
├── src/
│   ├── components/          # React components
│   │   ├── Navigation.tsx   # Main navigation
│   │   ├── HeroSection.tsx  # Landing hero section
│   │   ├── DocumentUpload.tsx # Document upload form
│   │   ├── Results.tsx      # Analysis results display
│   │   ├── Footer.tsx       # Footer component
│   │   ├── LoadingOverlay.tsx # Loading animation
│   │   └── NotificationProvider.tsx # Toast notifications
│   ├── lib/
│   │   └── utils.ts         # Utility functions
│   ├── types/
│   │   └── global.d.ts      # TypeScript declarations
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # App entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
└── tsconfig.json            # TypeScript configuration
```

## Components

### Navigation
- Responsive navigation bar
- Connection status indicator
- AI status indicator
- Smooth animations

### HeroSection
- Animated hero section with 3D effects
- Problem/solution presentation
- Feature highlights
- Call-to-action buttons

### DocumentUpload
- Drag & drop file upload
- Text input with character counter
- Voice input support (Speech Recognition API)
- Demo document samples
- Expertise level selection
- Form validation and error handling

### Results
- Risk assessment visualization
- Traffic light system (RED/YELLOW/GREEN)
- Confidence indicators
- Expandable clause analysis
- AI transparency metrics
- Copy/export functionality

### LoadingOverlay
- Multi-stage loading animation
- Progress bar with realistic progression
- Google Cloud AI branding
- Community impact messaging

## Styling

The app uses a modern dark theme with:
- Slate color palette for backgrounds
- Cyan/blue gradients for accents
- Custom animations and transitions
- Responsive breakpoints
- Accessibility-compliant contrast ratios

## API Integration

The frontend communicates with the Flask backend through:
- `/analyze` - Document analysis endpoint
- `/api/translate` - Translation service
- Form data submission for file uploads
- JSON responses for API calls

## Accessibility

- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast color scheme
- Focus management

## Performance

- Code splitting with Vite
- Lazy loading of components
- Optimized bundle size
- Fast development server
- Hot module replacement

## Deployment

The React app is built and served by the Flask backend in production. The build process:

1. `npm run build` creates optimized production build
2. Build output is copied to Flask `static/dist/` directory
3. Flask serves the React app for all non-API routes
4. API routes are handled by Flask backend

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Ensure accessibility compliance
4. Add proper error handling
5. Write meaningful component names
6. Use proper TypeScript types