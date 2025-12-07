import {Film, Loader, XCircle, Zap} from "lucide-react";

const ResultDisplay = (isLoading, error, results, MovieTable) => {
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-10 bg-white rounded-xl shadow-inner border border-indigo-100">
                <Loader className="w-8 h-8 text-indigo-500 animate-spin" />
                <p className="mt-3 text-lg font-medium text-indigo-700">Analyzing your query...</p>
                <p className="text-sm text-gray-500">Converting natural language to structured data and fetching results.</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 bg-red-50 border-l-4 border-red-500 rounded-xl shadow-lg">
                <div className="flex items-center">
                    <XCircle className="w-6 h-6 text-red-600 mr-3 flex-shrink-0" />
                    <h3 className="text-lg font-semibold text-red-800">Query Processing Error</h3>
                </div>
                <p className="mt-2 text-sm text-red-700">{error.message}</p>
                {error.llm_output && (
                    <div className="mt-3 p-3 text-xs bg-red-100 rounded">
                        <strong className="block mb-1">LLM Output Error:</strong>
                        <pre className="whitespace-pre-wrap font-mono">{error.llm_output}</pre>
                    </div>
                )}
            </div>
        );
    }

    if (results) {
        if (!results.data && !results.answer && results.message)
            results.answer = results.message;

        return (
            <div className="flex flex-col">
                {/* Conversational Answer */}
                <div className="p-6 bg-indigo-50 border border-indigo-200 rounded-xl shadow-lg">
                    <div className="flex items-start">
                        <Zap className="w-6 h-6 text-indigo-600 mr-3 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="text-lg font-bold text-indigo-800 mb-1">CineQuery Analyst Response</h3>
                            <p className="text-gray-700 whitespace-pre-wrap">{results.answer}</p>
                        </div>
                    </div>
                </div>

                {/* Structured Results Table */}
                {MovieTable}

                {/* Display if no movies matched the criteria */}
                {(!results.data || results.data?.length === 0) && (
                    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-xl shadow-sm text-center">
                        <p className="text-yellow-800 font-medium">No Movies Found...</p>
                        <p className="text-sm text-yellow-700">Try adjusting your query or filters.</p>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center p-10 bg-gray-50 rounded-xl border border-gray-200 shadow-inner text-center">
            <Film className="w-10 h-10 text-gray-400" />
            <h3 className="mt-3 text-xl font-semibold text-gray-700">Ask Me Anything About Movies</h3>
            <p className="mt-1 text-sm text-gray-500">
                Type a question like: "What are the top 3 highest rated sci-fi movies directed by women after 2000?"
            </p>
        </div>
    );
};

export default ResultDisplay;