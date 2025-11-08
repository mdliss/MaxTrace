import { useParams, useNavigate } from 'react-router-dom';
import ProcessingStatus from '../components/ProcessingStatus';

function Processing() {
  const { blueprintId } = useParams();
  const navigate = useNavigate();

  const handleComplete = (status) => {
    console.log('Processing complete:', status);
    // Navigate to results page after a short delay
    setTimeout(() => {
      navigate(`/results/${blueprintId}`);
    }, 1500);
  };

  const handleError = (error) => {
    console.error('Processing error:', error);
    // Could show an error page or allow retry
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">Innergy Room Detection AI</h1>
          <p className="text-sm text-gray-500">Processing Blueprint</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <ProcessingStatus
          blueprintId={blueprintId}
          onComplete={handleComplete}
          onError={handleError}
        />
      </main>
    </div>
  );
}

export default Processing;
