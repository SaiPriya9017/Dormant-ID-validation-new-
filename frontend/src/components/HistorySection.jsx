import React from 'react';
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  TableToolbar,
  TableToolbarContent,
  TableToolbarSearch,
  Button,
  Tag,
  Tile,
} from '@carbon/react';
import { Download, View, Renew } from '@carbon/icons-react';
import { getDownloadUrl } from '../api/retrieval';
import './HistorySection.scss';

const HistorySection = ({ history, onViewData, onRefresh }) => {
  const headers = [
    { key: 'job_id', header: 'Job ID' },
    { key: 'start_date', header: 'Start Date' },
    { key: 'end_date', header: 'End Date' },
    { key: 'status', header: 'Status' },
    { key: 'records_fetched', header: 'Records' },
    { key: 'duration', header: 'Duration' },
    { key: 'actions', header: 'Actions' },
  ];

  const getStatusTag = (status) => {
    const statusMap = {
      running: { type: 'blue', text: 'Running' },
      completed: { type: 'green', text: 'Completed' },
      failed: { type: 'red', text: 'Failed' },
      stopped: { type: 'gray', text: 'Stopped' },
      initializing: { type: 'purple', text: 'Initializing' },
    };

    const statusInfo = statusMap[status] || { type: 'gray', text: status };
    return <Tag type={statusInfo.type} size="sm">{statusInfo.text}</Tag>;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A';
    
    const start = startTime;
    const end = endTime || Date.now() / 1000;
    const duration = end - start;
    
    if (duration < 60) return `${Math.round(duration)}s`;
    if (duration < 3600) return `${Math.round(duration / 60)}m`;
    const hours = Math.floor(duration / 3600);
    const minutes = Math.round((duration % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const rows = history.map((job) => ({
    id: job.job_id,
    job_id: job.job_id.substring(0, 12) + '...',
    start_date: new Date(job.start_date).toLocaleString(),
    end_date: new Date(job.end_date).toLocaleString(),
    status: getStatusTag(job.status),
    records_fetched: formatNumber(job.records_fetched || 0),
    duration: formatDuration(job.start_time, job.end_time),
    actions: job,
  }));

  return (
    <Tile className="history-section">
      <h4 className="section-title">Retrieval History</h4>
      <DataTable rows={rows} headers={headers}>
        {({
          rows,
          headers,
          getHeaderProps,
          getRowProps,
          getTableProps,
          getTableContainerProps,
        }) => (
          <TableContainer
            {...getTableContainerProps()}
            title=""
            description=""
          >
            <TableToolbar>
              <TableToolbarContent>
                <TableToolbarSearch persistent />
                <Button
                  kind="ghost"
                  renderIcon={Renew}
                  iconDescription="Refresh"
                  onClick={onRefresh}
                  hasIconOnly
                />
              </TableToolbarContent>
            </TableToolbar>
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => (
                    <TableHeader {...getHeaderProps({ header })} key={header.key}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => (
                  <TableRow {...getRowProps({ row })} key={row.id}>
                    {row.cells.map((cell) => {
                      if (cell.info.header === 'actions') {
                        const job = cell.value;
                        return (
                          <TableCell key={cell.id}>
                            <div className="action-buttons">
                              <Button
                                kind="ghost"
                                size="sm"
                                renderIcon={View}
                                iconDescription="View Data"
                                onClick={() => onViewData(job)}
                                disabled={job.status !== 'completed'}
                                hasIconOnly
                              />
                              <Button
                                kind="ghost"
                                size="sm"
                                renderIcon={Download}
                                iconDescription="Download"
                                onClick={() => window.open(getDownloadUrl(job.job_id), '_blank')}
                                disabled={job.status !== 'completed'}
                                hasIconOnly
                              />
                            </div>
                          </TableCell>
                        );
                      }
                      return <TableCell key={cell.id}>{cell.value}</TableCell>;
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DataTable>
    </Tile>
  );
};

export default HistorySection;

// Made with Bob
