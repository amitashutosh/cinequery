import classNames from 'classnames';

const MovieTable = results => {
    if (!results || !results?.data || results?.data?.length === 0) return null;

    const data = results.data;
    const formatList = (list) => Array.isArray(list) ? list.join(', ') : 'N/A';
    const thClassName = 'px-6 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider';

    return (
        <div className="mt-6 overflow-x-auto shadow-xl rounded-xl">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-indigo-50">
                <tr>
                    <th scope="col" className={thClassName}>
                        Title
                    </th>
                    <th scope="col" className={classNames(thClassName, "hidden sm:table-cell")}>
                        Year
                    </th>
                    <th scope="col" className={thClassName}>
                        Rating
                    </th>
                    <th scope="col" className={classNames(thClassName, "hidden md:table-cell")}>
                        Director
                    </th>
                    <th scope="col" className={classNames(thClassName, "hidden lg:table-cell")}>
                        Genres
                    </th>
                    <th scope="col" className={classNames(thClassName, "hidden xl:table-cell")}>
                        Actors
                    </th>
                </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                {data.map((movie, index) => (
                    <tr key={index} className="hover:bg-gray-50 transition duration-150">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-800">
                            {movie.title}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 hidden sm:table-cell">
                            {movie.year}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                            {movie.rating ? movie.rating.toFixed(1) : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 hidden md:table-cell">
                            {movie.director || 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 hidden lg:table-cell max-w-xs truncate">
                            {formatList(movie.genres)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 hidden xl:table-cell max-w-sm truncate">
                            {formatList(movie.actors)}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}

export default MovieTable;