import { useState, useEffect, useRef, useCallback } from 'react';

const POLL_INTERVAL = 2000; // 2 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * Custom hook to poll for blueprint processing status
 * @param {string} blueprintId - The blueprint ID to check status for
 * @param {boolean} enabled - Whether polling is enabled
 * @returns {object} Status data and control functions
 */
export function useProcessingStatus(blueprintId, enabled = true) {
  const [status, setStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const pollIntervalRef = useRef(null);
  const retryTimeoutRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    if (!blueprintId) return;

    try {
      // TODO: Replace with actual API endpoint
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';
      const response = await fetch(`${apiUrl}/status/${blueprintId}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Blueprint not found');
        }
        throw new Error(`Failed to fetch status: ${response.statusText}`);
      }

      const data = await response.json();
      setStatus(data);
      setError(null);
      setRetryCount(0);

      // Stop polling if processing is complete or failed
      if (data.status === 'completed' || data.status === 'failed') {
        stopPolling();
      }

      return data;
    } catch (err) {
      console.error('Error fetching status:', err);

      // Increment retry count
      const newRetryCount = retryCount + 1;
      setRetryCount(newRetryCount);

      // If max retries exceeded, stop polling and set error
      if (newRetryCount >= MAX_RETRIES) {
        setError(err.message || 'Failed to fetch processing status');
        stopPolling();
      } else {
        // Retry after delay with exponential backoff
        const delay = RETRY_DELAY * Math.pow(2, newRetryCount - 1);
        retryTimeoutRef.current = setTimeout(() => {
          fetchStatus();
        }, delay);
      }
    }
  }, [blueprintId, retryCount]);

  const startPolling = useCallback(() => {
    if (!blueprintId || isPolling) return;

    setIsPolling(true);
    setError(null);
    setRetryCount(0);

    // Fetch immediately
    fetchStatus();

    // Set up polling interval
    pollIntervalRef.current = setInterval(() => {
      fetchStatus();
    }, POLL_INTERVAL);
  }, [blueprintId, isPolling, fetchStatus]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  const retry = useCallback(() => {
    setError(null);
    setRetryCount(0);
    startPolling();
  }, [startPolling]);

  // Auto-start polling when enabled
  useEffect(() => {
    if (enabled && blueprintId && !isPolling) {
      startPolling();
    }

    return () => {
      stopPolling();
    };
  }, [enabled, blueprintId, startPolling, stopPolling, isPolling]);

  return {
    status,
    isPolling,
    error,
    retryCount,
    startPolling,
    stopPolling,
    retry,
  };
}
