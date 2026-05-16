# SmartTrim 360 - AI Grooming Studio

SmartTrim 360 is a premium, AI-powered hairstyle preview and personal grooming platform. It provides an editorial-grade, highly interactive Studio interface where users can upload a photo and visualize different hairstyles using advanced AI models.

## Features

- **Premium Studio Dashboard:** A spacious, intuitive interface designed for a high-fidelity user experience.
- **AI Transformations:** Leverages state-of-the-art backend models to generate realistic hairstyle previews.
- **Interactive Comparisons:** "Before & After" interactive sliders using `react-compare-image`.
- **Session-Based Creations:** A "Recent Creations" sidebar for seamless comparison of past transformations in the current session.
- **Dynamic Animations:** Fluid UI transitions and micro-animations built with `framer-motion`.

## Tech Stack

### Frontend
- React 18 & Vite
- React Router DOM
- Framer Motion
- Tailwind CSS (with a custom premium design system)

### Backend
- Python (FastAPI / Flask - configured in `app/`)
- Generative AI models

## Getting Started

### Prerequisites
- Node.js & npm (for Frontend)
- Python 3.10+ (for Backend)

### Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### Setup Backend
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
# Run the backend server (refer to backend documentation)
```
