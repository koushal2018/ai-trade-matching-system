import React, { useState, useEffect } from 'react';
export {};

interface RunStatusIndicatorProps {
  isConnected: boolean;
  lastUpdated: Date | null;
}

const RunStatusIndicator: React.FC<RunStatusIndicatorProps> = ({ isConnected, lastUpdated }) => {
  const [timeAgo, setTimeAgo] = useState<string>('');
  
  // Update time ago every second
  useEffect(() => {
    if (!lastUpdated) {
      return;
    }
    
    const updateTimeAgo = () => {
      const now = new Date();
      const diff = now.getTime() - lastUpdated.getTime();
      
      if (diff < 1000) {
        setTimeAgo('just now');
      } else if (diff < 60000) {
        setTimeAgo(`${Math.floor(diff / 1000)} seconds ago`);
      } else if (diff < 3600000) {
        setTimeAgo(`${Math.floor(diff / 60000)} minutes ago`);
      } else {
        setTimeAgo(`${Math.floor(diff / 3600000)} hours ago`);
      }
    };
    
    updateTimeAgo();
    
    const intervalId = setInterval(updateTimeAgo, 1000);
    
    return () => {
      clearInterval(intervalId);
    };
  }, [lastUpdated]);
  
  return (
    <div className="flex items-center justify-between bg-white shadow overflow-hidden sm:rounded-lg p-4 mb-4">
      <div className="flex items-center">
        <div className={`h-3 w-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-gray-300'}`}></div>
        <span className="text-sm text-gray-600">
          {isConnected ? 'Connected - Receiving real-time updates' : 'Connecting...'}
        </span>
      </div>
      {lastUpdated && (
        <div className="text-sm text-gray-500">
          Last updated: {timeAgo}
        </div>
      )}
    </div>
  );
};

export default RunStatusIndicator;