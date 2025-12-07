import pandas as pd
import json
import os
import numpy as np

# Configuration
RAW_DATA_PATH = 'data/raw'
OUTPUT_FILE = 'data/processed/movies_db.json'
TARGET_MOVIE_TYPES = ['movie', 'tvMovie']
MIN_RATING_VOTES = 10
MAX_MOVIES = 200000

"""
Loads a TSV file into a DataFrame.
"""
def load_tsv(path):
    try:
        df = pd.read_csv(path, sep='\t', low_memory=False, na_values=['\\N'])
        print(f"Loaded {path.split('/')[-1]}: {len(df)} records.")
        return df
    except FileNotFoundError:
        print(f"ERROR: Required file not found at {path}. Please check your raw data directory.")
        return pd.DataFrame()

"""
Loads, cleans, joins, and subsets the raw IMDb data files.
"""
def load_and_clean_data():
    print("Starting data processing...")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Load Core Data
    basics_df = load_tsv(os.path.join(RAW_DATA_PATH, 'title.basics.tsv'))
    ratings_df = load_tsv(os.path.join(RAW_DATA_PATH, 'title.ratings.tsv'))
    crew_df = load_tsv(os.path.join(RAW_DATA_PATH, 'title.crew.tsv'))
    principals_df = load_tsv(os.path.join(RAW_DATA_PATH, 'title.principals.tsv'))
    names_df = load_tsv(os.path.join(RAW_DATA_PATH, 'name.basics.tsv'))

    if basics_df.empty or ratings_df.empty or crew_df.empty or names_df.empty:
        print("Aborting data processing due to missing files.")
        return

    # Drop missing years/genres early
    basics_df = basics_df[basics_df['titleType'].isin(TARGET_MOVIE_TYPES)]
    basics_df = basics_df.dropna(subset=['startYear', 'genres'])
    basics_df = basics_df[basics_df['genres'] != r'\N']
    basics_df = basics_df[basics_df['startYear'] != r'\N']

    basics_df = basics_df.rename(columns={'tconst': 'tconst',
                                          'primaryTitle': 'title',
                                          'startYear': 'year',
                                          'genres': 'genres'})
    basics_df = basics_df[['tconst', 'title', 'year', 'genres']]
    print(f"Loaded {len(basics_df)} basic movie titles.")

    # Filter for movies with min rating votes
    ratings_df = ratings_df[ratings_df['numVotes'] >= MIN_RATING_VOTES]
    ratings_df = ratings_df.rename(columns={'averageRating': 'rating'})
    ratings_df = ratings_df[['tconst', 'rating']]
    print(f"Loaded {len(ratings_df)} rated titles with >= {MIN_RATING_VOTES} votes.")

    # Join Basics and Ratings
    movies_df = pd.merge(basics_df, ratings_df, on='tconst', how='inner')
    print(f"Joined titles and ratings: {len(movies_df)} records remaining.")

    # Convert year to numeric and drop invalid entries
    movies_df['year'] = pd.to_numeric(movies_df['year'], errors='coerce')
    movies_df = movies_df.dropna(subset=['year'])
    movies_df['year'] = movies_df['year'].astype(int)

    # Sort by rating and limit the dataset size for in-memory use
    movies_df = movies_df.sort_values(by='rating', ascending=False).head(MAX_MOVIES)

    # Process Directors (Crew Data)
    directors_df = crew_df.dropna(subset=['directors']).copy()
    directors_df['nconst'] = directors_df['directors'].apply(lambda x: x.split(',')[0].strip())
    directors_df = directors_df[['tconst', 'nconst']]

    # Renaming director column
    director_names_df = names_df[['nconst', 'primaryName']].rename(columns={'primaryName': 'director', 'nconst': 'director_nconst'})
    directors_df = directors_df.rename(columns={'nconst': 'director_nconst'})
    directors_df = pd.merge(directors_df, director_names_df, on='director_nconst', how='left')
    directors_df = directors_df[['tconst', 'director']].drop_duplicates(subset=['tconst'], keep='first')

    movies_df = pd.merge(movies_df, directors_df, on='tconst', how='left')
    movies_df['director'] = movies_df['director'].fillna(np.nan).replace([np.nan], [None])
    print(f"Added director data for {len(movies_df.dropna(subset=['director']))} movies.")

    # Keep only Actors/Actresses
    principals_df = principals_df[principals_df['category'].isin(['actor', 'actress'])]
    principals_df = principals_df[['tconst', 'nconst']]

    # Load Name Basics (Maps nconst to actor name)
    names_df = names_df.rename(columns={'nconst': 'nconst', 'primaryName': 'name'})
    names_df = names_df[['nconst', 'name']]

    # Join Principals with Names to get actor names per movie
    actors_df = pd.merge(principals_df, names_df, on='nconst', how='inner')

    # Group the actor names by movie ID (tconst) into a list
    actors_grouped = actors_df.groupby('tconst')['name'].apply(list).reset_index(name='actors')
    print(f"Extracted actors for {len(actors_grouped)} movies.")

    # Final Join: Add Actor Lists to the Main Movie DataFrame
    movies_df = pd.merge(movies_df, actors_grouped, on='tconst', how='left')

    # Fill NaN actor lists with empty lists
    movies_df['actors'] = movies_df['actors'].apply(lambda x: x if isinstance(x, list) else [])

    # Convert 'genres' string to a list of strings
    movies_df['genres'] = movies_df['genres'].apply(lambda x: [g.strip() for g in x.split(',')] if pd.notna(x) else [])

    # Remove the internal TCONST and convert to list of dictionaries
    final_movies_list = movies_df.drop(columns=['tconst']).to_dict('records')

    print(f"Final dataset size: {len(final_movies_list)} records.")

    # Save the JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_movies_list, f, indent=2)

    print(f"\nSuccessfully created in-memory JSON file: {OUTPUT_FILE}")
    print("This file will be loaded into memory by the LLM interface.")

if __name__ == '__main__':
    load_and_clean_data()