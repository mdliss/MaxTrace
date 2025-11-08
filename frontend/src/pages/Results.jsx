import { useParams, Link } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import BlueprintCanvas from '../components/BlueprintCanvas';
import { getResultsUrl } from '../config/api';

function Results() {
  const { blueprintId } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
  const canvasRef = useRef(null);

  // Fetch results from backend API
  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(getResultsUrl(blueprintId));

        if (!response.ok) {
          throw new Error(`Failed to fetch results: ${response.statusText}`);
        }

        const data = await response.json();
        setResults(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching results:', err);
        setError(err.message || 'Failed to load results. Please try again.');
        setLoading(false);
      }
    };

    if (blueprintId) {
      fetchResults();
    }
  }, [blueprintId]);

  const handleDownloadJSON = () => {
    if (!results) return;

    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `blueprint-${blueprintId}-results.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!results) return;
    navigator.clipboard.writeText(JSON.stringify(results, null, 2));
    alert('Results copied to clipboard!');
  };

  const handleDownloadImage = () => {
    if (!canvasRef.current?.exportAsImage) return;
    const filename = `blueprint-${blueprintId}-annotated.png`;
    canvasRef.current.exportAsImage(filename);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-xl mb-4">Error loading results</p>
          <p className="text-gray-600">{error}</p>
          <Link to="/" className="mt-4 inline-block text-blue-600 hover:underline">
            Return to Upload
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Innergy Room Detection AI</h1>
            <p className="text-sm text-gray-500">Blueprint ID: {blueprintId}</p>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            New Upload
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-4 mb-4">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">
                Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.3"
                max="0.9"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="w-48"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyToClipboard}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium"
              >
                Copy JSON
              </button>
              <button
                onClick={handleDownloadImage}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Download Image
              </button>
              <button
                onClick={handleDownloadJSON}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
              >
                Download JSON
              </button>
            </div>
          </div>
        </div>

        {/* Visualization */}
        <div className="bg-white rounded-lg shadow overflow-hidden" style={{ height: '600px' }}>
          <BlueprintCanvas
            ref={canvasRef}
            imageUrl={results.imageUrl}
            detections={results.detections}
            confidenceThreshold={confidenceThreshold}
          />
        </div>

        {/* Detection Summary */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Rooms</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {results.detections.filter(d => d.confidence >= confidenceThreshold).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Avg Confidence</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {(results.statistics.avgConfidence * 100).toFixed(1)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Processing Time</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {results.processingTime}s
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Results;
