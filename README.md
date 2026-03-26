# SignalAtlas - Owner Intelligence Suite

SignalAtlas is an AI-powered insights platform that analyzes Reddit communities to discover user archetypes, map product perception, and measure customer satisfaction. By simply entering a product name, the system automatically discovers relevant subreddits, fetches the latest discussions, and uses large language models (Google Gemini) and topic modeling to provide deep, actionable insights.

## Features

- **Automated Subreddit Discovery:** The AI automatically identifies the most relevant subreddits where your product is being discussed.
- **User Archetypes Generation:** Classifies Reddit comments into distinct user personas (archetypes) to help you understand *who* is using your product and *how*.
- **Comprehensive Product Perception:**
  - **Identity Frames:** How the community frames and perceives your product (positive, negative, mixed).
  - **Narratives:** Extracts the underlying stories and causal explanations users share.
  - **Competitor Anchoring:** Identifies who your users compare you against and why.
  - **Emotion & Trust Metrics:** Measures underlying sentiment beyond just satisfaction (e.g., trust, hype, disappointment, frustration).
- **Customer Satisfaction (ACSI) Scoring:** Calculates an estimated American Customer Satisfaction Index score based on community feedback.
- **Topic Modeling:** Uses BERTopic to group comments into distinct conversation topics and extracts key themes within each archetype.
- **Insight Coach:** An AI companion that suggests next steps and guides you through your data based on recent events and metric changes.
- **Portfolio Management:** Keep track of multiple products and their respective insights in an organized dashboard.

## Architecture & Tech Stack

The project is split into a robust Python backend and multiple frontend implementations to suit different deployment needs.

### Backend (`/backend`)
A RESTful API built with **Flask** that orchestrates the data pipeline and AI models.
- **Reddit Integration:** Uses `praw` to fetch hot posts and top comments.
- **AI/LLM:** Uses `google-generativeai` (Gemini) for classification, extraction, narrative generation, and perception analysis.
- **Topic Modeling:** Uses `bertopic` and `scikit-learn` for clustering comment topics.
- **Data Storage:** A lightweight local storage mechanism (`storage.py`) tracking products, archetypes, and history.

### Frontend Applications

1. **Main Dashboard (`/frontend-cra`)**
   - A fully-featured **React** application built with Create React App.
   - Features a rich user interface, sidebar portfolio management, detailed data visualizations (score rings, emotion tracks), timeline views, and archetype cards.
   
2. **Static App (`/frontend-static`)**
   - A lightweight, no-build pure HTML/JS implementation using Babel standalone.
   - Good for quick testing or embedding without a complex build step.

3. **Legacy/Base CRA (`/frontend`)**
   - The default Create React App boilerplate.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js & npm (for the React frontends)
- Reddit API Credentials
- Google Gemini API Key

### Backend Setup
1. Navigate to the `backend` directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend` directory with your API keys:
   ```env
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=your_user_agent
   GEMINI_API_KEY=your_gemini_api_key
   ```
4. Start the Flask server:
   ```bash
   python -m app.main
   ```
   The backend will run on `http://localhost:5000`.

### Frontend Setup (Main React App)
1. Navigate to the `frontend-cra` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```
4. Access the application at `http://localhost:3000`.

## Quick Start (Static Frontend)
If you just want to run the lightweight version:
1. Ensure the Flask backend is running on port 5000.
2. Open `frontend-static/index.html` in your browser.

## Workflow

1. **Add a Product:** Enter a product name (e.g., "iPhone", "Notion").
2. **Run Pipeline:** The backend will find subreddits, ingest posts, and use Gemini to generate archetypes and perception data.
3. **Run Topic Modeling:** Click on an archetype to run BERTopic and label emerging conversation clusters.
4. **Refresh Data:** Click "Refresh New Posts" periodically to bring in the latest comments and update satisfaction metrics over time.
