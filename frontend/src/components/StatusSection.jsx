import React from 'react';
import {
  Tile,
  ProgressBar,
  Tag,
  Grid,
  Column,
} from '@carbon/react';
import './StatusSection.scss';

const StatusSection = ({ status, isRunning }) => {
  if (!status) return null;

  const getStatusTag = () => {
    const statusMap = {
      running: { type: 'blue', text: 'Running' },
      completed: { type: 'green', text: 'Completed' },
      failed: { type: 'red', text: 'Failed' },
      stopped: { type: 'gray', text: 'Stopped' },
      initializing: { type: 'purple', text: 'Initializing' },
    };

    const statusInfo = statusMap[status.status] || { type: 'gray', text: status.status };
    return <Tag type={statusInfo.type}>{statusInfo.text}</Tag>;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  return (
    <Tile className="status-section">
      <div className="status-header">
        <h4 className="section-title">Current Status</h4>
        {getStatusTag()}
      </div>

      <Grid narrow className="status-grid">
        <Column lg={4} md={2} sm={2}>
          <div className="stat-item">
            <div className="stat-label">Records Fetched</div>
            <div className="stat-value">{formatNumber(status.records_fetched || 0)}</div>
          </div>
        </Column>
        <Column lg={4} md={2} sm={2}>
          <div className="stat-item">
            <div className="stat-label">Records/sec</div>
            <div className="stat-value">{status.records_per_sec?.toFixed(2) || '0.00'}</div>
          </div>
        </Column>
        <Column lg={4} md={2} sm={2}>
          <div className="stat-item">
            <div className="stat-label">Progress</div>
            <div className="stat-value">{status.progress_percent?.toFixed(1) || '0.0'}%</div>
          </div>
        </Column>
        <Column lg={4} md={2} sm={2}>
          <div className="stat-item">
            <div className="stat-label">Est. Time Remaining</div>
            <div className="stat-value">
              {status.estimated_time_remaining 
                ? formatTime(status.estimated_time_remaining)
                : 'Calculating...'}
            </div>
          </div>
        </Column>
      </Grid>

      {isRunning && (
        <div className="progress-bar-container">
          <ProgressBar
            label="Retrieval Progress"
            value={status.progress_percent || 0}
            max={100}
            size="big"
          />
        </div>
      )}

      {status.error && (
        <div className="error-message">
          <Tag type="red">Error</Tag>
          <span>{status.error}</span>
        </div>
      )}
    </Tile>
  );
};

export default StatusSection;

// Made with Bob
