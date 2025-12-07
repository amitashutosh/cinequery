# CineQuery Engine (Backend API)

The CineQuery Engine is a Python-based, _two-stage_ **Retrieval-Augmented Generation (RAG)** system designed to
translate natural language movie queries into structured JSON queries, execute them against an in-memory database, and
synthesize the results into a conversational response.

## Architecture Overview

The system operates in **_three_** main steps:

1. **Semantic Parsing (Translation)**: A Large Language Model (LLM) is used to translate the user's Natural Language
   query into a structured JSON query object, constrained by a predefined schema.
2. **Deterministic Execution**: The JSON query is executed efficiently against an in-memory, pre-processed movie
   database (using pure Python/Pandas logic).
3. **Grounded Synthesis**: A second LLM call uses only the filtered, retrieved movie data to generate a concise,
   conversational answer, ensuring 100% data fidelity.

## Setup and Installation

### Prerequisites

- Python 3.9+
- The required Python libraries (listed in requirements.txt).
- The IMDb datasets (must be downloaded separately).

### Project Structure

```
├── data/
│   ├── raw/
│   │   ├── title.basics.tsv        # Raw IMDb data files
│   │   ├── title.ratings.tsv
│   │   └── ...
│   └── processed/
│       └── movies_db.json          # Processed, in-memory database (Generated)
├── app/
│   ├── llm_interface.py            # Core engine logic and LLM orchestration
│   │── data_processor.py           # Script to load/clean/join raw data
│   ├── test_cinequery_engine.py    # Unit tests for the core logic
│
└── README.md
```

### Setup Steps

#### Clone the Repository:

```
git clone https://github.com/amitashutosh/cinequery
cd cinequery
```

#### Install Dependencies:

```
pip install -r requirements.txt
```

#### Set API Key:

- The system uses the Gemini API. Set your key as an environment variable.

```
export GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

## Data Processing

The database used is an in-memory JSON file (movies_db.json) generated from the raw IMDb data.

**Download Raw Data**: Download the necessary IMDb files (title.basics.tsv, title.ratings.tsv, etc.) and place them into
the data/raw/ directory.

**Process Data**: Run the processor script to clean, join, filter, and subset the data. This step can take a few minutes
depending on hardware.

```
python scripts/data_processor.py  # Output file: data/processed/movies_db.json
```

## Usage

### Running the Engine

The core logic is contained within the CineQueryEngine class in llm_interface.py. You can import and use it as a
service:

```
from app.llm_interface import CineQueryEngine

# Initialize the engine (loads the movies_db.json into memory)
engine = CineQueryEngine()

# Run a query
user_query = "What are the top 5 highest-rated action movies from the 90s starring Tom Hanks?"
response = engine.run_cinequery(user_query)

# Response structure:
# {
#   "status": "success",
#   "query": "...",
#   "data": [...],        # The raw filtered JSON data
#   "answer": "..."       # The final conversational text answer
# }
print(response["answer"])

```

### Running Tests

Execute the unit tests to ensure the deterministic query execution logic is sound.

```
python app/test_cinequery_engine.py
```

## API Endpoints

The CineQueryEngine is designed to be wrapped in a microservice (e.g., using Flask or FastAPI). The conceptual primary
endpoint is:

| Method | Endpoint      | Description                                               |
|--------|---------------|-----------------------------------------------------------|
| POST   | /api/v1/query | Submits a natural language query and returns the results. |

### Request Body (JSON):

```json
{
  "query": "Show me the best Sci-Fi movies from 2010."
}
```

### Successful Response (JSON):

```json
{
  "answer": "Certainly, the top Sci-Fi movies from 2010 found in the database are...",
  "movies": [
    {
      "title": "Inception",
      "year": 2010,
      "rating": 8.8,
      ...
    }
    // ... up to the limit requested
  ]
}
```

---

# CineQuery Web Interface (Frontend)

This repository contains the single-page application (SPA) designed to provide a user-friendly interface for the
CineQuery Engine API. The application allows users to submit natural language queries and view the conversational,
data-grounded results in real-time.

## Key Technologies

* **_Framework_**: React
* **_Styling_**: Tailwind CSS (for responsive, utility-first design)
* **_Data Fetching_**: Standard Fetch API or Axios
* **_Core Feature_**: Real-time communication with the CineQuery Engine API.

## Setup and Installation

### Prerequisites

* Node.js and npm (or yarn) installed.
* The CineQuery Engine API must be running and accessible (e.g., on http://localhost:5001).

### Setup Steps

1. Clone the Repository: (You should already have repo cloned from the CineQuery repo)

```
git clone https://github.com/amitashutosh/cinequery  
cd cinequery/frontend
```

2. Install Dependencies:

```
npm install
# or yarn install
```

3. Configure API URL (if needed):

- Ensure the environment variable `REACT_APP_API_URL` (or equivalent) points to your running backend.

- In the project root, create a file named `.env`:

```
REACT_APP_API_URL=http://localhost:5001/api/v1/query
```

4. Start the Application:

```
npm run dev
# The application should open in your browser (typically http://localhost:5173)
```

3. Usage and Components

- The main interface is a single component: `CineQueryContainer` Component.
- This component handles user input and displays the conversation history.

### API Interaction

The application uses an asynchronous function to POST the user's query to the backend and handle the response:

```
// Example API call structure
async function handleSubmit(query) {
  const response = await fetch(API_URL, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: query })
});

    if (response.ok) {
        const data = await response.json();
        // Update state with data.answer and data.movies (for display)
    } else {
        // Handle API error
    }

}
```