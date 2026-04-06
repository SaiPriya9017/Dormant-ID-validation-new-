import React, { useState, useEffect } from 'react';
import {
  Modal,
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  Pagination,
  Loading,
} from '@carbon/react';
import { viewData } from '../api/retrieval';
import './DataViewerModal.scss';

const DataViewerModal = ({ job, onClose }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData(page, pageSize);
  }, [page, pageSize]);

  const loadData = async (currentPage, currentPageSize) => {
    setLoading(true);
    setError(null);
    try {
      const result = await viewData(job.job_id, currentPage, currentPageSize);
      setData(result);
    } catch (err) {
      setError(err.message);
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = ({ page: newPage, pageSize: newPageSize }) => {
    if (newPage !== page) {
      setPage(newPage);
    }
    if (newPageSize !== pageSize) {
      setPageSize(newPageSize);
      setPage(1); // Reset to first page when page size changes
    }
  };

  // Generate headers from first row
  const headers = data?.rows?.[0]
    ? Object.keys(data.rows[0]).map((key) => ({
        key,
        header: key.charAt(0).toUpperCase() + key.slice(1),
      }))
    : [];

  // Generate rows
  const rows = data?.rows?.map((row, index) => ({
    id: `row-${index}`,
    ...row,
  })) || [];

  return (
    <Modal
      open
      modalHeading={`Data Viewer - ${job.job_id}`}
      primaryButtonText="Close"
      onRequestClose={onClose}
      onRequestSubmit={onClose}
      size="lg"
      className="data-viewer-modal"
    >
      {loading ? (
        <Loading description="Loading data..." withOverlay={false} />
      ) : error ? (
        <div className="error-state">
          <p>Error loading data: {error}</p>
        </div>
      ) : (
        <>
          <DataTable rows={rows} headers={headers}>
            {({
              rows,
              headers,
              getHeaderProps,
              getRowProps,
              getTableProps,
              getTableContainerProps,
            }) => (
              <TableContainer {...getTableContainerProps()}>
                <Table {...getTableProps()} size="sm">
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
                        {row.cells.map((cell) => (
                          <TableCell key={cell.id}>
                            {typeof cell.value === 'object'
                              ? JSON.stringify(cell.value)
                              : String(cell.value)}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </DataTable>

          <Pagination
            backwardText="Previous page"
            forwardText="Next page"
            itemsPerPageText="Items per page:"
            page={page}
            pageSize={pageSize}
            pageSizes={[100, 500, 1000]}
            totalItems={data?.total_lines || 0}
            onChange={handlePageChange}
          />
        </>
      )}
    </Modal>
  );
};

export default DataViewerModal;

// Made with Bob
