import React, { useState, useEffect } from 'react';
import { Tab } from '@headlessui/react';
import { useLocation } from 'react-router-dom';
import { CpuChipIcon, PlayIcon, ClockIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

// Import the components
import AgentRunFormContainer from './AgentRunFormContainer';
import ActiveRuns from './ActiveRuns';
import RunHistory from './RunHistory';
import AgentSettings from './AgentSettings';
import ErrorBoundary from '../../common/ErrorBoundary';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

const AgentMonitorPage: React.FC = () => {
  const location = useLocation();
  const [selectedTab, setSelectedTab] = useState(0);
  
  // Check if we need to switch to a specific tab based on location state
  useEffect(() => {
    if (location.state && typeof location.state === 'object' && 'activeTab' in location.state) {
      const activeTab = (location.state as { activeTab: number }).activeTab;
      setSelectedTab(activeTab);
    }
  }, [location]);
  
  const tabs = [
    { name: 'New Run', icon: PlayIcon, component: <AgentRunFormContainer /> },
    { name: 'Active Runs', icon: CpuChipIcon, component: <ActiveRuns /> },
    { name: 'History', icon: ClockIcon, component: <RunHistory /> },
    { name: 'Settings', icon: Cog6ToothIcon, component: <AgentSettings /> },
  ];

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <h1 className="text-2xl font-semibold text-gray-900">Agent Monitor</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage and monitor AI agents for trade reconciliation
        </p>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 mt-6">
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
            <Tab.List className="flex border-b border-gray-200">
              {tabs.map((tab, index) => (
                <Tab
                  key={tab.name}
                  className={({ selected }) =>
                    classNames(
                      'py-4 px-6 text-sm font-medium flex items-center',
                      selected
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    )
                  }
                >
                  <tab.icon className="h-5 w-5 mr-2" aria-hidden="true" />
                  {tab.name}
                </Tab>
              ))}
            </Tab.List>
            <Tab.Panels className="p-4">
              {tabs.map((tab, index) => (
                <Tab.Panel key={tab.name}>
                  <ErrorBoundary>
                    {tab.component}
                  </ErrorBoundary>
                </Tab.Panel>
              ))}
            </Tab.Panels>
          </Tab.Group>
        </div>
      </div>
    </div>
  );
};

export default AgentMonitorPage;