/**
 * API Configuration
 *
 * This file contains the base URL and endpoint paths for the backend API.
 * Update API_BASE_URL if the backend API Gateway URL changes.
 */

// Base URL for API Gateway
export const API_BASE_URL = 'https://s4fsv92lt6.execute-api.us-east-1.amazonaws.com/dev';

// Endpoint paths
export const UPLOAD_ENDPOINT = '/upload';
export const DETECT_ENDPOINT = '/detect';
export const RESULTS_ENDPOINT = (blueprintId) => `/results/${blueprintId}`;

// Full endpoint URLs (convenience exports)
export const getUploadUrl = () => `${API_BASE_URL}${UPLOAD_ENDPOINT}`;
export const getDetectUrl = () => `${API_BASE_URL}${DETECT_ENDPOINT}`;
export const getResultsUrl = (blueprintId) => `${API_BASE_URL}${RESULTS_ENDPOINT(blueprintId)}`;

// Default config for fetch requests
export const defaultHeaders = {
  'Content-Type': 'application/json',
};

export const fetchConfig = (method = 'GET', body = null) => {
  const config = {
    method,
    headers: defaultHeaders,
  };

  if (body && method !== 'GET') {
    config.body = JSON.stringify(body);
  }

  return config;
};
