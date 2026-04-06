import axios from 'axios';

const API_BASE = '/api/retrieval';

/**
 * Start a new retrieval job
 * @param {string} startDate - ISO format start date
 * @param {string} endDate - ISO format end date
 * @param {boolean} compress - Whether to compress output
 * @returns {Promise} Job information
 */
export const startRetrieval = async (startDate, endDate, compress = false) => {
  const response = await axios.post(`${API_BASE}/start`, null, {
    params: { start_date: startDate, end_date: endDate, compress },
  });
  return response.data;
};

/**
 * Get status of a retrieval job
 * @param {string} jobId - Job identifier
 * @returns {Promise} Job status
 */
export const getStatus = async (jobId) => {
  const response = await axios.get(`${API_BASE}/status/${jobId}`);
  return response.data;
};

/**
 * Stop a running retrieval job
 * @param {string} jobId - Job identifier
 * @returns {Promise} Success message
 */
export const stopRetrieval = async (jobId) => {
  const response = await axios.post(`${API_BASE}/stop/${jobId}`);
  return response.data;
};

/**
 * Get history of all retrieval jobs
 * @returns {Promise} List of jobs
 */
export const getHistory = async () => {
  const response = await axios.get(`${API_BASE}/history`);
  return response.data;
};

/**
 * Download data file for a job
 * @param {string} jobId - Job identifier
 * @returns {string} Download URL
 */
export const getDownloadUrl = (jobId) => {
  return `${API_BASE}/download/${jobId}`;
};

/**
 * View paginated data from a job
 * @param {string} jobId - Job identifier
 * @param {number} page - Page number
 * @param {number} pageSize - Records per page
 * @returns {Promise} Paginated data
 */
export const viewData = async (jobId, page = 1, pageSize = 100) => {
  const response = await axios.get(`${API_BASE}/view/${jobId}`, {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

// Made with Bob
