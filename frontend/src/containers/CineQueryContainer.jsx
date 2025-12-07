import React, {useState, useCallback, useMemo} from 'react';
import { Search, Loader, Film, XCircle, Zap } from 'lucide-react';
import {runCineQuery, runCineQueryPlaceholder} from '../helpers/runCineQuery';

// Components
import Header from '../components/Header.jsx';
import ResultDisplay from '../components/ResultDisplay';
import MovieTable from '../components/MovieTable';

const CineQueryContainer = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = useCallback(async () => {
        if (!query.trim()) return;

        setIsLoading(true);
        setError(null);
        setResults(null);

        try {
            // const response = await runCineQueryPlaceholder(query.trim());
            const response = await runCineQuery(query.trim());

            if (response.status === 'success') setResults(response);
            else if (response.status === 'error') setError(response);
        }
        catch (err) {
            setError({ message: 'An unexpected network error occurred.', details: err.message });
        }
        finally {
            setIsLoading(false);
        }
    }, [query]);

    const handleKeyPress = useCallback((e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    }, [handleSearch]);

    const MemoMovieTable = useMemo(() => MovieTable(results), [results]);
    const MemoResultDisplay = useMemo(() => ResultDisplay(isLoading, error, results, MemoMovieTable), [isLoading, error, results, MemoMovieTable])

    return (
        <div className="min-h-screen bg-gray-100 font-[Inter] p-4 sm:p-8">
            <div className="mx-auto">
                <Header />

                <div className="bg-white p-6 rounded-2xl shadow-2xl mb-8">
                    {/* Input Field */}
                    <div className="flex rounded-xl shadow-lg ring-2 ring-indigo-500/50 focus-within:ring-indigo-600 transition duration-300">
                        <input
                            type="text"
                            className="flex-grow p-4 text-gray-700 focus:outline-none rounded-l-xl text-base sm:text-lg"
                            placeholder="e.g., Best action movies starring Tom Cruise in the 1990s"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSearch}
                            disabled={isLoading || !query.trim()}
                            className={`p-4 rounded-r-xl transition duration-200 flex items-center justify-center
                                ${isLoading || !query.trim()
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg'
                            }`}
                        >
                            {isLoading ? (
                                <Loader className="w-5 h-5 animate-spin" />
                            ) : (
                                <Search className="w-5 h-5" />
                            )}
                            <span className="ml-2 font-semibold hidden sm:inline">Search</span>
                        </button>
                    </div>
                </div>

                <div className="min-h-[300px]">
                    {MemoResultDisplay}
                </div>
            </div>
        </div>
    );
}

export default CineQueryContainer;