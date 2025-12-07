/**
 * Mock API Call Function
 */

export const runCineQueryPlaceholder = async (query) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Stub 1: Successful Query (The Dark Knight Query)
    if (query.toLowerCase().includes('dark knight')) {
        return {
            status: 'success',
            query: query,
            data: [
                {
                    "title": "The Dark Knight",
                    "year": 2008,
                    "rating": 9.0,
                    "director": "Christopher Nolan",
                    "genres": ["Action", "Crime", "Drama"],
                    "actors": ["Christian Bale", "Heath Ledger", "Aaron Eckhart"]
                },
                {
                    "title": "The Dark Knight Rises",
                    "year": 2012,
                    "rating": 8.4,
                    "director": "Christopher Nolan",
                    "genres": ["Action", "Crime", "Drama"],
                    "actors": ["Christian Bale", "Tom Hardy", "Anne Hathaway"]
                }
            ],
            answer: "Based on your query, here are two highly-rated films from the Dark Knight trilogy, both directed by Christopher Nolan."
        };
    }

    // Stub 2: No Results
    if (query.toLowerCase().includes('unicorn')) {
        return {
            status: 'success',
            query: query,
            data: [],
            answer: "I found no movies matching your criteria in the database."
        };
    }

    // Stub 3: Simulated LLM/Backend Error
    if (query.toLowerCase().includes('error')) {
        return {
            status: 'error',
            message: 'Failed to translate query into structured JSON format.',
            llm_output: '{"title_keywords": "error", "year_min": 2025' // Example bad JSON
        };
    }

    // Stub 4: Simulated Future Year
    if (query.toLowerCase().includes('2026')) {
        return{
            status: 'success',
            message: 'I found no movies matching your criteria in the database.'
        }
    }

    // Default successful response
    return {
        status: 'success',
        query: query,
        data: [
            {
                "title": "Inception",
                "year": 2010,
                "rating": 8.8,
                "director": "Christopher Nolan",
                "genres": ["Action", "Sci-Fi", "Adventure"],
                "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"]
            }
        ],
        answer: "I found one movie based on your generic search: Inception. It's a highly-rated sci-fi masterpiece from 2010."
    };
};

/**
 * Actual API Call
 * @param {string} query The natural language query string.
 * @returns {Promise<Object>} The structured response object from the CineQueryEngine.
 */
export const runCineQuery = async (query) => {
    // The endpoint where your Python Flask/API is listening to
    const API_URL = 'http://localhost:5001/query';

    const payload = { query: query };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        // 1. Check for non-2xx HTTP status codes (e.g., 404, 500)
        if (!response.ok) {
            // Attempt to parse the response body for a detailed error message
            try {
                // Return the error structure assumed by the main component
                return await response.json();
            } catch (e) {
                // If parsing fails, return a generic HTTP error
                return {
                    status: 'error',
                    message: `HTTP Error: ${response.status} ${response.statusText}`,
                    llm_output: `Attempted to query backend at ${API_URL} but received status ${response.status}.`
                };
            }
        }

        // 2. Response is 2xx, parse the JSON payload
        return await response.json();
    } catch (error) {
        // 3. Handle network errors (e.g., server not running, CORS issues)
        console.error("Network Error:", error);
        return {
            status: 'error',
            message: 'Network connection failed. Ensure the Python backend is running on http://localhost:5001 and accessible.',
            details: error.message
        };
    }
};

