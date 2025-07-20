import React, { useEffect, useState } from 'react';
import { AgentService } from '../../../services/agent/AgentService';
import { AgentSettings as AgentSettingsType } from '../../../types/agent';
import FormInput from '../../common/FormInput';
import { validateRequired, validateNumber } from '../../../utils/validation';
import { useCustomToast } from '../../../hooks/useCustomToast';
import SystemHealthMonitor from './SystemHealthMonitor';

interface AgentSettingsProps {
  // No props needed for now
}

const AgentSettings: React.FC<AgentSettingsProps> = () => {
  const [settings, setSettings] = useState<AgentSettingsType>({
    globalSettings: {
      maxConcurrentRuns: 3,
      defaultMatchingThreshold: 0.85,
      defaultNumericTolerance: 0.001,
      defaultReportBucket: 'reconciliation-reports',
    },
    agentSpecificSettings: {},
  });
  
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [agentTypes, setAgentTypes] = useState<string[]>(['trade-pdf-processing', 'trade-matching', 'reconciliation']);
  const [showAgentSettings, setShowAgentSettings] = useState<Record<string, boolean>>({});
  
  // Use our custom toast hook
  const { showToast } = useCustomToast();
  
  // Fetch settings on component mount
  useEffect(() => {
    fetchSettings();
  }, []);
  
  const fetchSettings = async () => {
    setLoading(true);
    try {
      const agentService = AgentService.getInstance();
      const fetchedSettings = await agentService.getSettings();
      setSettings(fetchedSettings);
      
      // Initialize showAgentSettings based on fetched agent types
      const agentTypesFromSettings = Object.keys(fetchedSettings.agentSpecificSettings);
      if (agentTypesFromSettings.length > 0) {
        setAgentTypes(agentTypesFromSettings);
        
        const initialShowState: Record<string, boolean> = {};
        agentTypesFromSettings.forEach(type => {
          initialShowState[type] = false;
        });
        setShowAgentSettings(initialShowState);
      }
    } catch (error) {
      showToast('error', 'Error: Failed to fetch settings. Please try again.');
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleGlobalSettingChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    // Convert to number if the field is numeric
    const numericFields = ['maxConcurrentRuns', 'defaultMatchingThreshold', 'defaultNumericTolerance'];
    const processedValue = numericFields.includes(name) ? Number(value) : value;
    
    setSettings(prev => ({
      ...prev,
      globalSettings: {
        ...prev.globalSettings,
        [name]: processedValue,
      },
    }));
    
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };
  
  const handleAgentSettingChange = (agentType: string, settingName: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      agentSpecificSettings: {
        ...prev.agentSpecificSettings,
        [agentType]: {
          ...prev.agentSpecificSettings[agentType],
          [settingName]: value,
        },
      },
    }));
    
    // Clear error when user types
    const errorKey = `${agentType}.${settingName}`;
    if (errors[errorKey]) {
      setErrors(prev => ({
        ...prev,
        [errorKey]: '',
      }));
    }
  };
  
  const toggleAgentSettings = (agentType: string) => {
    setShowAgentSettings(prev => ({
      ...prev,
      [agentType]: !prev[agentType],
    }));
  };
  
  const validateSettings = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Validate global settings
    const maxConcurrentRunsValidation = validateRequired(settings.globalSettings.maxConcurrentRuns);
    if (!maxConcurrentRunsValidation.isValid) {
      newErrors.maxConcurrentRuns = maxConcurrentRunsValidation.message || 'Required';
    } else {
      const numValidation = validateNumber(settings.globalSettings.maxConcurrentRuns, 1, 10);
      if (!numValidation.isValid) {
        newErrors.maxConcurrentRuns = numValidation.message || 'Invalid value';
      }
    }
    
    const thresholdValidation = validateRequired(settings.globalSettings.defaultMatchingThreshold);
    if (!thresholdValidation.isValid) {
      newErrors.defaultMatchingThreshold = thresholdValidation.message || 'Required';
    } else {
      const numValidation = validateNumber(settings.globalSettings.defaultMatchingThreshold, 0, 1);
      if (!numValidation.isValid) {
        newErrors.defaultMatchingThreshold = numValidation.message || 'Invalid value';
      }
    }
    
    const toleranceValidation = validateRequired(settings.globalSettings.defaultNumericTolerance);
    if (!toleranceValidation.isValid) {
      newErrors.defaultNumericTolerance = toleranceValidation.message || 'Required';
    } else {
      const numValidation = validateNumber(settings.globalSettings.defaultNumericTolerance, 0);
      if (!numValidation.isValid) {
        newErrors.defaultNumericTolerance = numValidation.message || 'Invalid value';
      }
    }
    
    const bucketValidation = validateRequired(settings.globalSettings.defaultReportBucket);
    if (!bucketValidation.isValid) {
      newErrors.defaultReportBucket = bucketValidation.message || 'Required';
    }
    
    // Validate agent-specific settings
    // This would depend on the specific settings for each agent type
    // For now, we'll just check if required fields are present
    
    Object.entries(settings.agentSpecificSettings).forEach(([agentType, agentSettings]) => {
      Object.entries(agentSettings).forEach(([settingName, value]) => {
        if (settingName.includes('required') && !value) {
          newErrors[`${agentType}.${settingName}`] = 'Required';
        }
      });
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSaveSettings = async () => {
    if (!validateSettings()) {
      showToast('error', 'Validation Error: Please fix the errors in the form before saving.');
      return;
    }
    
    setSaving(true);
    try {
      const agentService = AgentService.getInstance();
      const success = await agentService.updateSettings(settings);
      
      if (success) {
        showToast('success', 'Settings Saved: Agent settings have been updated successfully.');
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      showToast('error', 'Error: Failed to save settings. Please try again.');
      console.error('Error saving settings:', error);
    } finally {
      setSaving(false);
    }
  };
  
  // Define types for agent settings
  type NumberSettingType = {
    name: string;
    label: string;
    type: 'number';
    min: number;
    max: number;
    step: number;
  };
  
  type SelectSettingType = {
    name: string;
    label: string;
    type: 'select';
    options: string[];
  };
  
  type CheckboxSettingType = {
    name: string;
    label: string;
    type: 'checkbox';
  };
  
  type SettingType = NumberSettingType | SelectSettingType | CheckboxSettingType;
  
  // Render agent-specific settings form for a given agent type
  const renderAgentSpecificSettings = (agentType: string) => {
    const agentSettings = settings.agentSpecificSettings[agentType] || {};
    
    // This is a placeholder - in a real app, you would have a schema or configuration
    // that defines what settings each agent type has
    const agentSettingsConfig: Record<string, SettingType[]> = {
      'trade-pdf-processing': [
        { name: 'pdfParsingMode', label: 'PDF Parsing Mode', type: 'select', options: ['strict', 'lenient', 'auto'] },
        { name: 'extractionConfidenceThreshold', label: 'Extraction Confidence Threshold', type: 'number', min: 0, max: 1, step: 0.01 },
      ],
      'trade-matching': [
        { name: 'fuzzyMatchingEnabled', label: 'Enable Fuzzy Matching', type: 'checkbox' },
        { name: 'matchingAlgorithm', label: 'Matching Algorithm', type: 'select', options: ['exact', 'levenshtein', 'jaccard'] },
      ],
      'reconciliation': [
        { name: 'autoResolveThreshold', label: 'Auto-Resolve Threshold', type: 'number', min: 0, max: 1, step: 0.01 },
        { name: 'conflictResolutionStrategy', label: 'Conflict Resolution Strategy', type: 'select', options: ['manual', 'newest', 'source-priority'] },
      ],
    };
    
    const config = agentSettingsConfig[agentType] || [];
    
    return (
      <div className="mt-4 pl-4 border-l-2 border-gray-200">
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
          {config.map(setting => {
            // Handle different setting types
            if (setting.type === 'number') {
              return (
                <FormInput
                  key={`${agentType}-${setting.name}`}
                  id={`${agentType}-${setting.name}`}
                  name={`${agentType}-${setting.name}`}
                  label={setting.label}
                  type="number"
                  value={String(agentSettings[setting.name] || '')}
                  onChange={(e) => handleAgentSettingChange(agentType, setting.name, Number(e.target.value))}
                  error={errors[`${agentType}.${setting.name}`]}
                  min={setting.min}
                  max={setting.max}
                  step={setting.step}
                  required={setting.name.includes('required')}
                />
              );
            } else {
              return (
                <FormInput
                  key={`${agentType}-${setting.name}`}
                  id={`${agentType}-${setting.name}`}
                  name={`${agentType}-${setting.name}`}
                  label={setting.label}
                  type="text"
                  value={String(agentSettings[setting.name] || '')}
                  onChange={(e) => handleAgentSettingChange(agentType, setting.name, e.target.value)}
                  error={errors[`${agentType}.${setting.name}`]}
                  required={setting.name.includes('required')}
                />
              );
            }
          })}
        </div>
      </div>
    );
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium leading-6 text-gray-900">Agent Settings</h3>
        <p className="mt-1 text-sm text-gray-500">
          Configure agent parameters and monitor system health
        </p>
      </div>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Global Settings</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Settings that apply to all agent types
          </p>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
          <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
            <FormInput
              id="maxConcurrentRuns"
              name="maxConcurrentRuns"
              label="Max Concurrent Runs"
              type="number"
              value={String(settings.globalSettings.maxConcurrentRuns)}
              onChange={handleGlobalSettingChange}
              error={errors.maxConcurrentRuns}
              helpText="Maximum number of agent runs that can be active simultaneously"
              min={1}
              max={10}
              required
            />
            
            <FormInput
              id="defaultMatchingThreshold"
              name="defaultMatchingThreshold"
              label="Default Matching Threshold"
              type="number"
              value={String(settings.globalSettings.defaultMatchingThreshold)}
              onChange={handleGlobalSettingChange}
              error={errors.defaultMatchingThreshold}
              helpText="Default threshold for matching trades (0-1)"
              min={0}
              max={1}
              step={0.01}
              required
            />
            
            <FormInput
              id="defaultNumericTolerance"
              name="defaultNumericTolerance"
              label="Default Numeric Tolerance"
              type="number"
              value={String(settings.globalSettings.defaultNumericTolerance)}
              onChange={handleGlobalSettingChange}
              error={errors.defaultNumericTolerance}
              helpText="Default tolerance for numeric comparisons"
              min={0}
              step={0.001}
              required
            />
            
            <FormInput
              id="defaultReportBucket"
              name="defaultReportBucket"
              label="Default Report Bucket"
              type="text"
              value={settings.globalSettings.defaultReportBucket}
              onChange={handleGlobalSettingChange}
              error={errors.defaultReportBucket}
              helpText="Default storage location for generated reports"
              required
            />
          </div>
        </div>
      </div>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Agent-Specific Settings</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Configure settings for individual agent types
          </p>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
          {agentTypes.map(agentType => (
            <div key={agentType} className="mb-4 last:mb-0">
              <div 
                className="flex items-center justify-between cursor-pointer"
                onClick={() => toggleAgentSettings(agentType)}
              >
                <h4 className="text-sm font-medium text-gray-900">{agentType}</h4>
                <button
                  type="button"
                  className="inline-flex items-center p-1 border border-transparent rounded-full shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg 
                    className={`h-4 w-4 transition-transform ${showAgentSettings[agentType] ? 'transform rotate-180' : ''}`} 
                    xmlns="http://www.w3.org/2000/svg" 
                    viewBox="0 0 20 20" 
                    fill="currentColor"
                  >
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              
              {showAgentSettings[agentType] && renderAgentSpecificSettings(agentType)}
            </div>
          ))}
        </div>
      </div>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">System Health</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Current system resource usage and health metrics
          </p>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
          <SystemHealthMonitor refreshInterval={60000} />
        </div>
      </div>
      
      <div className="flex justify-end">
        <button
          type="button"
          className={`px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
            saving ? 'opacity-75 cursor-not-allowed' : ''
          }`}
          onClick={handleSaveSettings}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default AgentSettings;