import React from 'react';
import { Button, ButtonSet, Tile } from '@carbon/react';
import { Play, Stop } from '@carbon/icons-react';
import './ControlPanel.scss';

const ControlPanel = ({ isRunning, onStart, onStop }) => {
  return (
    <Tile className="control-panel">
      <h4 className="section-title">Retrieval Controls</h4>
      <ButtonSet>
        <Button
          kind="primary"
          renderIcon={Play}
          onClick={() => onStart(false)}
          disabled={isRunning}
          size="lg"
        >
          Start Retrieval
        </Button>
        <Button
          kind="secondary"
          renderIcon={Play}
          onClick={() => onStart(true)}
          disabled={isRunning}
          size="lg"
        >
          Start with Compression
        </Button>
        <Button
          kind="danger"
          renderIcon={Stop}
          onClick={onStop}
          disabled={!isRunning}
          size="lg"
        >
          Stop Retrieval
        </Button>
      </ButtonSet>
    </Tile>
  );
};

export default ControlPanel;

// Made with Bob
