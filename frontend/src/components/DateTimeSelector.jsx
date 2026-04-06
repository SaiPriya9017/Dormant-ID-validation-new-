import React from 'react';
import {
  DatePicker,
  DatePickerInput,
  TimePicker,
  TimePickerSelect,
  SelectItem,
  Grid,
  Column,
  Tile,
} from '@carbon/react';
import './DateTimeSelector.scss';

const DateTimeSelector = ({ dateRange, onChange, disabled }) => {
  const handleDateChange = (dates) => {
    if (dates && dates.length >= 2) {
      onChange({
        ...dateRange,
        startDate: dates[0]?.toISOString().split('T')[0] || '',
        endDate: dates[1]?.toISOString().split('T')[0] || '',
      });
    }
  };

  const handleStartTimeChange = (e) => {
    onChange({
      ...dateRange,
      startTime: e.target.value,
    });
  };

  const handleEndTimeChange = (e) => {
    onChange({
      ...dateRange,
      endTime: e.target.value,
    });
  };

  return (
    <Tile className="date-time-selector">
      <h4 className="section-title">Select Date and Time Range</h4>
      <Grid narrow>
        <Column lg={8} md={4} sm={4}>
          <DatePicker
            datePickerType="range"
            onChange={handleDateChange}
            disabled={disabled}
          >
            <DatePickerInput
              id="start-date"
              placeholder="mm/dd/yyyy"
              labelText="Start Date"
              size="md"
              disabled={disabled}
            />
            <DatePickerInput
              id="end-date"
              placeholder="mm/dd/yyyy"
              labelText="End Date"
              size="md"
              disabled={disabled}
            />
          </DatePicker>
        </Column>
        <Column lg={4} md={2} sm={2}>
          <TimePicker
            id="start-time"
            labelText="Start Time"
            value={dateRange.startTime}
            onChange={handleStartTimeChange}
            disabled={disabled}
          >
            <TimePickerSelect
              id="start-time-select"
              labelText="Timezone"
              disabled={disabled}
            >
              <SelectItem value="UTC" text="UTC" />
            </TimePickerSelect>
          </TimePicker>
        </Column>
        <Column lg={4} md={2} sm={2}>
          <TimePicker
            id="end-time"
            labelText="End Time"
            value={dateRange.endTime}
            onChange={handleEndTimeChange}
            disabled={disabled}
          >
            <TimePickerSelect
              id="end-time-select"
              labelText="Timezone"
              disabled={disabled}
            >
              <SelectItem value="UTC" text="UTC" />
            </TimePickerSelect>
          </TimePicker>
        </Column>
      </Grid>
    </Tile>
  );
};

export default DateTimeSelector;

// Made with Bob
