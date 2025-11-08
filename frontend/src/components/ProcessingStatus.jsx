import { useEffect } from 'react';
import { useProcessingStatus } from '../hooks/useProcessingStatus';

const STAGE_INFO = {
  'upload': { label: 'Uploading', icon: '📤', order: 1 },
  'preprocessing': { label: 'Preprocessing', icon: '🔄', order: 2 },
  'inference': { label: 'Running Inference', icon: '🤖', order: 3 },
  'postprocess': { label: 'Post-processing', icon: '✨', order: 4 },
  'complete': { label: 'Complete', icon: '✅', order: 5 },
  'failed': { label: 'Failed', icon: '❌', order: 5 },
};

/**
 * Component to display real-time processing status with progress stages
 */
function ProcessingStatus({ blueprintId, onComplete, onError }) {
  const { status, isPolling, error, retry } = useProcessingStatus(blueprintId, true);

  // Call callbacks when status changes
  useEffect(() => {
    if (status?.status === 'completed' && onComplete) {
      onComplete(status);
    }
    if ((status?.status === 'failed' || error) && onError) {
      onError(error || status?.message);
    }
  }, [status, error, onComplete, onError]);

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-red-600 mb-2">Processing Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={retry}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing...</p>
        </div>
      </div>
    );
  }

  const currentStageInfo = STAGE_INFO[status.stage] || STAGE_INFO['preprocessing'];
  const progress = status.progress || 0;
  const estimatedTime = status.estimatedTimeRemaining || 0;

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="text-6xl mb-4">{currentStageInfo.icon}</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {currentStageInfo.label}
        </h2>
        <p className="text-gray-600">
          Blueprint ID: {blueprintId}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span className="font-semibold">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          >
            <div className="h-full w-full bg-white/20 animate-pulse"></div>
          </div>
        </div>
      </div>

      {/* Time Remaining */}
      {estimatedTime > 0 && (
        <div className="text-center mb-6">
          <p className="text-sm text-gray-500 mb-1">Estimated time remaining</p>
          <p className="text-3xl font-bold text-gray-900">
            {formatTime(estimatedTime)}
          </p>
        </div>
      )}

      {/* Stage Indicators */}
      <div className="grid grid-cols-4 gap-2 mb-6">
        {Object.entries(STAGE_INFO)
          .filter(([key]) => !['complete', 'failed'].includes(key))
          .sort(([, a], [, b]) => a.order - b.order)
          .map(([key, info]) => {
            const isComplete = info.order < currentStageInfo.order;
            const isCurrent = key === status.stage;
            const isPending = info.order > currentStageInfo.order;

            return (
              <div
                key={key}
                className={`p-3 rounded-lg text-center transition-all ${
                  isComplete
                    ? 'bg-green-100 border-2 border-green-500'
                    : isCurrent
                    ? 'bg-blue-100 border-2 border-blue-500 animate-pulse'
                    : 'bg-gray-100 border-2 border-gray-300'
                }`}
              >
                <div className="text-2xl mb-1">{info.icon}</div>
                <p className={`text-xs font-medium ${
                  isComplete
                    ? 'text-green-700'
                    : isCurrent
                    ? 'text-blue-700'
                    : 'text-gray-500'
                }`}>
                  {info.label}
                </p>
              </div>
            );
          })}
      </div>

      {/* Status Message */}
      {status.message && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <p className="text-sm text-blue-800">{status.message}</p>
        </div>
      )}

      {/* Polling Indicator */}
      {isPolling && (
        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500">
          <div className="animate-pulse flex gap-1">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animation-delay-200"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animation-delay-400"></div>
          </div>
          <span>Checking status...</span>
        </div>
      )}
    </div>
  );
}

/**
 * Format seconds into readable time string
 */
function formatTime(seconds) {
  if (seconds < 60) {
    return `${Math.ceil(seconds)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.ceil(seconds % 60);

  if (remainingSeconds === 0) {
    return `${minutes}m`;
  }

  return `${minutes}m ${remainingSeconds}s`;
}

export default ProcessingStatus;
