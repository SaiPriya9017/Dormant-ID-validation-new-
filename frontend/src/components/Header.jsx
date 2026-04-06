import React from 'react';
import {
  Header as CarbonHeader,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
} from '@carbon/react';
import { Information } from '@carbon/icons-react';

const Header = () => {
  return (
    <CarbonHeader aria-label="Cloudant Retrieval System">
      <HeaderName prefix="IBM">
        Cloudant Retrieval System
      </HeaderName>
      <HeaderGlobalBar>
        <HeaderGlobalAction
          aria-label="Information"
          tooltipAlignment="end"
        >
          <Information size={20} />
        </HeaderGlobalAction>
      </HeaderGlobalBar>
    </CarbonHeader>
  );
};

export default Header;

// Made with Bob
