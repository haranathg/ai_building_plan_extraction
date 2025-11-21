# CompliCheckAI - Deployment Guide

This React application is the CompliCheckAI UI for building consent submissions.

## Render Deployment

### Option 1: Deploy via Render Dashboard (Recommended)

1. **Connect Repository to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Select this repository

2. **Configure Build Settings:**
   - **Name:** `complicheck-ai` (or your preferred name)
   - **Root Directory:** `frontend/CompliCheckAI/colabs`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `build`

3. **Advanced Settings (Optional):**
   - Enable "Auto-Deploy" to deploy on every push to main
   - Add custom domain if desired

4. **Deploy:**
   - Click "Create Static Site"
   - Render will build and deploy your app
   - You'll get a URL like: `https://complicheck-ai.onrender.com`

### Option 2: Deploy via render.yaml (Automatic)

If you have `render.yaml` in your repo root:

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect and use the `render.yaml` configuration

## Local Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Environment

- React 19.2.0
- Tailwind CSS
- Lucide React (icons)

## Project Structure

```
frontend/CompliCheckAI/colabs/
├── public/              # Static files
├── src/
│   ├── CompliCheckAI-UI.jsx  # Main UI component
│   ├── App.js           # App entry point
│   ├── index.css        # Tailwind CSS imports
│   └── index.js         # React DOM render
├── package.json
├── tailwind.config.js   # Tailwind configuration
└── render.yaml          # Render deployment config
```

## URLs

- **Local:** http://localhost:3000
- **Production:** Will be provided after Render deployment

## Support

For issues or questions, contact the development team.
