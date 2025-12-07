import unittest
from unittest import mock
from llm_interface import CineQueryEngine

MOCK_DB_DATA = [
    {"title": "The Dark Knight", "year": 2008, "rating": 9.0, "genres": ["Action", "Crime"], "actors": ["Christian Bale", "Heath Ledger"]},
    {"title": "Pulp Fiction", "year": 1994, "rating": 8.9, "genres": ["Crime", "Drama"], "actors": ["John Travolta", "Uma Thurman"]},
    {"title": "Inception", "year": 2010, "rating": 8.8, "genres": ["Action", "Sci-Fi"], "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"]},
    {"title": "Forrest Gump", "year": 1994, "rating": 8.8, "genres": ["Drama"], "actors": ["Tom Hanks", "Robin Wright"]},
    {"title": "Toy Story", "year": 1995, "rating": 8.3, "genres": ["Animation", "Family"], "actors": ["Tom Hanks", "Tim Allen"]},
]

MOCK_TRANSLATION_SUCCESS = {
    "text": '{"genre": "Action", "year_min": 2000, "sort_by": "rating", "sort_order": "desc", "limit": 2}'
}


# Mock response for a successful NL to JSON translation
MOCK_SYNTHESIS_SUCCESS = {
    "text": "Based on the data, the top two action movies made after 2000 are The Dark Knight and Inception."
}

class TestCineQueryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CineQueryEngine()
        self.engine.movie_dataset = MOCK_DB_DATA

    """Test filtering by actor (fuzzy search)."""
    def test_filter_by_actor(self):
        query = {"actor": "tom hanks"}
        results = self.engine.execute_query_json(query)
        self.assertEqual(len(results), 2)
        self.assertTrue(all("Forrest Gump" in r["title"] or "Toy Story" in r["title"] for r in results))

    """Test filtering by year range and minimum rating."""
    def test_filter_by_year_and_rating(self):
        query = {"year_min": 1990, "year_max": 2000, "rating_min": 8.5}
        results = self.engine.execute_query_json(query)

        # Should return Pulp Fiction (8.9) and Forrest Gump (8.8)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Pulp Fiction")

    """Test sorting by year in ascending order."""
    def test_sort_by_year_asc(self):
        query = {"sort_by": "year", "sort_order": "asc", "limit": 3}
        results = self.engine.execute_query_json(query)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["year"], 1994) # Pulp Fiction/Forrest Gump
        self.assertEqual(results[-1]["year"], 1995) # Toy Story

    """Test the entire run_cinequery flow using mock responses."""
    @mock.patch.object(CineQueryEngine, '_call_gemini_api')
    def test_full_query_flow(self, mock_gemini):
        mock_gemini.side_effect = [
            MOCK_TRANSLATION_SUCCESS, # 1. NL to JSON
            MOCK_SYNTHESIS_SUCCESS    # 2. JSON to NL
        ]

        query = "What are the best two action movies after 2000?"
        response = self.engine.run_cinequery(query)

        # Assertions on the final output structure
        self.assertEqual(response["status"], "success")
        self.assertTrue("The Dark Knight" in response["answer"])
        self.assertTrue(isinstance(response["data"], list))

        # Assertions on mock calls
        self.assertEqual(mock_gemini.call_count, 2)

        # Assert the synthesis call received the correct data (The Dark Knight and Inception)
        synthesis_prompt = mock_gemini.call_args_list[1][0][0]
        self.assertIn("The Dark Knight", synthesis_prompt)
        self.assertIn("Inception", synthesis_prompt)

    """Test the path where the database query returns no data."""
    @mock.patch.object(CineQueryEngine, '_call_gemini_api')
    def test_empty_result_path(self, mock_gemini):
        # Mock translation to a query that has no result in MOCK_DB_DATA
        mock_translation_no_result = {
            "text": '{"actor": "Brad Pitt"}'
        }

        mock_gemini.return_value = mock_translation_no_result
        query = "Best movies with Brad Pitt."
        response = self.engine.run_cinequery(query)

        # Should skip synthesis and return a failure message
        self.assertEqual(response["status"], "success")
        self.assertIn("no movies matching your criteria", response["message"])
        self.assertEqual(mock_gemini.call_count, 1)  # Only translation was called

if __name__ == '__main__':
    unittest.main()