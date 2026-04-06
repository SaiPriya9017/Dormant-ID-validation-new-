import React, { useState, useEffect } from 'react';
import {
  Content,
  Theme,
  Grid,
  Column,
} from '@carbon/react';
import Header from './components/Header';
import DateTimeSelector from './components/DateTimeSelector';
import ControlPanel from './components/ControlPanel';
import StatusSection from './components/StatusSection';
import HistorySection from './components/HistorySection';
import DataViewerModal from './components/DataViewerModal';
import { startRetrieval, stopRetrieval, getStatus, getHistory } from './api/retrieval';
import './App.scss';

function App() {
  const [currentJob, setCurrentJob] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [viewerData, setViewerData] = useState(null);
  const [dateRange, setDateRange] = useState({
    startDate: '',
    startTime: '',
    endDate: '',
    endTime: '',
  });

  // Poll for status updates when job is running
  useEffect(() => {
    if (!currentJob || !isRunning) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getStatus(currentJob.job_id);
        setJobStatus(status);

        // Stop polling if job is complete
        if (['completed', 'failed', 'stopped'].includes(status.status)) {
          setIsRunning(false);
          loadHistory();
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [currentJob, isRunning]);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getHistory();
      setHistory(data.jobs || []);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const handleStart = async (compress = false) => {
    try {
      // Validate dates
      if (!dateRange.startDate || !dateRange.endDate) {
        alert('Please select start and end dates');
        return;
      }

      // Combine date and time
      const startDateTime = `${dateRange.startDate}T${dateRange.startTime || '00:00:00'}Z`;
      const endDateTime = `${dateRange.endDate}T${dateRange.endTime || '23:59:59'}Z`;

      // Start retrieval - THIS RETURNS IMMEDIATELY
      const response = await startRetrieval(startDateTime, endDateTime, compress);
      
      // Update UI instantly (before any data is fetched)
      setCurrentJob(response.job);
      setJobStatus(response.job);
      setIsRunning(true);
    } catch (error) {
      console.error('Error starting retrieval:', error);
      alert('Failed to start retrieval: ' + error.message);
    }
  };

  const handleStop = async () => {
    if (!currentJob) return;

    try {
      await stopRetrieval(currentJob.job_id);
      setIsRunning(false);
    } catch (error) {
      console.error('Error stopping retrieval:', error);
      alert('Failed to stop retrieval: ' + error.message);
    }
  };

  const handleViewData = (job) => {
    setViewerData(job);
  };

  const handleCloseViewer = () => {
    setViewerData(null);
  };

  return (
    <Theme theme="g100">
      <Header />
      <Content>
        <Grid className="app-container" fullWidth>
          <Column lg={16} md={8} sm={4}>
            {/* Date and Time Selection */}
            <DateTimeSelector
              dateRange={dateRange}
              onChange={setDateRange}
              disabled={isRunning}
            />

            {/* Control Panel */}
            <ControlPanel
              isRunning={isRunning}
              onStart={handleStart}
              onStop={handleStop}
            />

            {/* Current Status Section - BELOW date selection */}
            {(isRunning || jobStatus) && (
              <StatusSection
                status={jobStatus}
                isRunning={isRunning}
              />
            )}

            {/* History Section */}
            <HistorySection
              history={history}
              onViewData={handleViewData}
              onRefresh={loadHistory}
            />
          </Column>
        </Grid>

        {/* Data Viewer Modal */}
        {viewerData && (
          <DataViewerModal
            job={viewerData}
            onClose={handleCloseViewer}
          />
        )}
      </Content>
    </Theme>
  );
}

export default App;

// Made with Bob
