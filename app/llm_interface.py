import json
import os
import requests
import time
from typing import List, Dict, Any, Optional

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.5-flash-preview-09-2025" # "gemini-2.0-flash-lite"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# JSON Schema Definition
QUERY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title_keywords": {"type": "STRING", "description": "Keywords to match in the movie title."},
        "actor": {"type": "STRING", "description": "Name of the actor or actress to filter by."},
        "director": {"type": "STRING", "description": "Name of the director to filter by."},
        "genre": {"type": "STRING", "description": "Primary genre (e.g., Action, Comedy, Drama)."},
        "year_min": {"type": "INTEGER", "description": "Minimum release year (inclusive)."},
        "year_max": {"type": "INTEGER", "description": "Maximum release year (inclusive)."},
        "rating_min": {"type": "NUMBER", "description": "Minimum average rating (e.g., 7.5)."},
        "sort_by": {"type": "STRING", "enum": ["rating", "year"],
                    "description": "Field to sort results by (e.g., 'rating', 'year')."},
        "sort_order": {"type": "STRING", "enum": ["asc", "desc"],
                       "description": "Sorting direction ('asc' or 'desc')."},
        "limit": {"type": "INTEGER", "description": "Maximum number of results to return (default 5)."}
    },
    "propertyOrdering": ["title_keywords", "actor", "director", "genre", "year_min", "year_max", "rating_min",
                         "sort_by",
                         "sort_order", "limit"]
}

"""
Core engine for handling natural language queries, database execution,
and LLM synthesis. Designed for testability by encapsulating state.
"""
class CineQueryEngine:
    """
    Load the in-memory database.
    """
    def __init__(self, db_filepath: str = "data/processed/movies_db.json"):
        self.movie_dataset: List[Dict[str, Any]] = self._initialize_database(db_filepath)
        if not self.movie_dataset:
            print("Warning: Database is empty or not found. Please check the database filepath.")

        self.api_key = API_KEY
        if not self.api_key:
            print("Warning: Gemini API key not found. Please check the API_KEY environment variable.")

        self.model_name = MODEL_NAME
        self.api_base_url = API_BASE_URL

    """
    Loads the pre-processed JSON file into memory.
    """
    def _initialize_database(self, filepath: str) -> List[Dict[str, Any]]:
        print(f"Loading in-memory database from {filepath}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Database loaded successfully: {len(data)} records.")
            return data
        except FileNotFoundError:
            print(f"Error: Database file not found at {filepath}.")
            return []
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from {filepath}.")
            return []

    """
    Generic function to call the Gemini API with exponential backoff.
    Includes Google Search grounding only for the synthesis step (is_translation=False)
    to improve stability of the structured output translation step.
    """
    def _call_gemini_api(self, prompt: str, system_instruction: str, is_translation: bool = False) -> Optional[
        Dict[str, Any]]:
        if not self.api_key:
            return {"status": "error", "message": "Gemini API key not found. Please check the API_KEY environment variable."}

        url = f"{self.api_base_url}/{self.model_name}:generateContent?key={self.api_key}"

        generation_config = {"temperature": 0.1}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": generation_config,
        }

        if not is_translation:
            payload["tools"] = [{"google_search": {}}]

        if is_translation:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = QUERY_SCHEMA

        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)
                    print(f"Retrying API request in {delay}s...")
                    time.sleep(delay)

                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
                response.raise_for_status()

                result = response.json()
                if result.get("candidates") and result["candidates"][0].get("content"):
                    return result["candidates"][0]["content"]["parts"][0]
                return None

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    print(f"API rate limit exceeded. Waiting for {response.headers.get('Retry-After')} seconds...")
                    # time.sleep(int(response.headers.get('Retry-After')))
                    continue


            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    # print(f"API request failed ({e}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Final API request failed after {max_retries} attempts: {e}")
                    return None
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from API response: {e}")
                return None

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return {"status": "error", "message": "An unexpected error occurred during API call.", "details": str(e)}
        return None

    """
    Executes the JSON filter/sort query against the in-memory movie dataset.
    """
    def execute_query_json(self, query_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = self.movie_dataset

        def get_lower_string_value(key):
            value = query_json.get(key)

            if isinstance(value, (int, float)):
                value = str(value)

            if isinstance(value, str):
                cleaned_value = value.strip()
                if cleaned_value not in ("", r'\N'):
                    return cleaned_value.lower()

            return None

        # Filter by director
        director = query_json.get("director")
        director_lower = get_lower_string_value("director")
        if director:
            results = [m for m in results if m.get("director") and director_lower in m["director"].lower()]

        # Filter by actor
        actor = query_json.get("actor")
        actor_lower = get_lower_string_value("actor")
        if actor_lower:
            results = [
                m for m in results
                if any(actor_lower in a.lower() for a in m.get("actors", []))
            ]

        # Filter by genre
        genre = query_json.get("genre")
        genre_lower = get_lower_string_value("genre")
        if genre:
            results = [
                m for m in results
                if any(genre_lower in g.lower() for g in m.get("genres", []))
            ]

        # Filter by title keywords
        title_keywords = query_json.get("title_keywords")
        title_keywords_lower = get_lower_string_value("title_keywords")
        if title_keywords:
            results = [m for m in results if title_keywords_lower in str(m.get("title", "")).lower()]

        # Filter by year_min
        year_min = query_json.get("year_min")
        if year_min is not None:
            results = [m for m in results if m.get("year", 0) >= year_min]

        # Filter by year_max
        year_max = query_json.get("year_max")
        if year_max is not None:
            results = [m for m in results if m.get("year", 9999) <= year_max]

        # Filter by rating_min
        rating_min = query_json.get("rating_min")
        if rating_min is not None:
            results = [m for m in results if m.get("rating", 0.0) >= rating_min]

        # Sorting
        sort_by = query_json.get("sort_by")
        sort_order = query_json.get("sort_order", "desc")

        if sort_by in ["rating", "year"]:
            reverse = sort_order == "desc"
            default_key = 0.0 if sort_by == 'rating' else 0
            results.sort(key=lambda x: x.get(sort_by, default_key), reverse=reverse)

        # Limit Results
        limit = query_json.get("limit", 5)
        if isinstance(limit, int) and limit > 0:
            results = results[:limit]

        return results

    """
    Main orchestrator for the NL-to-DB-to-NL pipeline.
    """
    def run_cinequery(self, user_query: str) -> Dict[str, Any]:

        if not self.movie_dataset:
            return {"status": "error", "message": "Database not initialized or empty."}

        # Translation
        translation_system_prompt = (
            "You are a strict data retrieval engine. Your ONLY function is to convert the user's "
            "natural language query into a valid JSON object matching the provided schema. "
            "Do not include any text or conversation outside of the JSON object. "
            "If a field is not mentioned by the user, omit it from the JSON. "
            "Be aggressive in mapping concepts (e.g., 'best' or 'top' implies sort_by: 'rating', sort_order: 'desc', limit: 5)."
        )

        translation_result = self._call_gemini_api(user_query, translation_system_prompt, is_translation=True)

        if not translation_result:
            return {"status": "error", "message": "Failed to translate query into structured JSON format."}

        try:
            query_json_text = translation_result.get("text", "")

            if query_json_text.startswith("```json"):
                query_json_text = query_json_text.replace("```json", "", 1).rstrip('`\n')
            elif query_json_text.startswith("```"):
                query_json_text = query_json_text.replace("```", "", 1).rstrip('`\n')

            query_json = json.loads(query_json_text)
        except json.JSONDecodeError:
            return {"status": "error", "message": "LLM returned improperly formatted JSON.",
                    "llm_output": query_json_text}

        # Execution
        movie_results = self.execute_query_json(query_json)

        if not movie_results:
            return {"status": "success", "message": "I found no movies matching your criteria in the database."}

        # Synthesis
        results_data_json = json.dumps(movie_results, indent=2)

        synthesis_prompt = (
            f"The user asked: '{user_query}'. "
            f"The following data was retrieved from the database:\n\n{results_data_json}\n\n"
            "Please use ONLY this data to generate a concise, conversational, and helpful summary. "
            "Do not hallucinate any information not present in the provided JSON data."
        )
        synthesis_system_prompt = (
            "You are a helpful film analyst. Your task is to summarize the provided structured movie data "
            "into natural, conversational language based on the original user query."
        )

        synthesis_result = self._call_gemini_api(synthesis_prompt, synthesis_system_prompt, is_translation=False)

        if not synthesis_result:
            return {"status": "error", "message": "Failed to synthesize a final answer."}

        final_answer = synthesis_result.get("text", "Could not generate final answer text.")

        return {"status": "success", "query": user_query, "data": movie_results, "answer": final_answer}

# cqe = CineQueryEngine()
# print(cqe.run_cinequery("What are the top 5 highest-rated family movies?"))