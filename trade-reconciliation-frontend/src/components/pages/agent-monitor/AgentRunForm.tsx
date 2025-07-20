import React, { useState, useEffect } from 'react';
import { AgentRunConfig, SavedConfiguration } from '../../../types/agent';
import FormSelect from '../../common/FormSelect';
import FormInput from '../../common/FormInput';
import FormTextarea from '../../common/FormTextarea';
import { validateRequired, validateNumber } from '../../../utils/validation';
import SaveConfigModal from './SaveConfigModal';
import LoadConfigModal from './LoadConfigModal';
import { AgentService } from '../../../services/agent/AgentService';

interface AgentRunFormProps {
  onSubmit?: (config: AgentRunConfig) => Promise<void>;
  initialConfig?: AgentRunConfig;
  isLoading?: boolean;
}

const AgentRunForm: React.FC<AgentRunFormProps> = ({
  onSubmit,
  initialConfig,
  isLoading = false,
}) => {
  // Modal state
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [isLoadModalOpen, setIsLoadModalOpen] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  // Form state
  const [agentType, setAgentType] = useState(initialConfig?.agentType || 'trade-pdf-processing');
  const [matchingThreshold, setMatchingThreshold] = useState(
    initialConfig?.parameters?.matchingThreshold?.toString() || '0.85'
  );
  const [numericTolerance, setNumericTolerance] = useState(
    initialConfig?.parameters?.numericTolerance?.toString() || '0.001'
  );
  const [reportBucket, setReportBucket] = useState(
    initialConfig?.parameters?.reportBucket || 'reconciliation-reports'
  );
  const [tradeIds, setTradeIds] = useState(initialConfig?.inputData?.tradeIds?.join(', ') || '');
  const [documentIds, setDocumentIds] = useState(initialConfig?.inputData?.documentIds?.join(', ') || '');
  const [startDate, setStartDate] = useState(initialConfig?.inputData?.dateRange?.startDate || '');
  const [endDate, setEndDate] = useState(initialConfig?.inputData?.dateRange?.endDate || '');
  const [additionalParams, setAdditionalParams] = useState('');

  // Validation state
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Handle field touch
  const handleBlur = (field: string) => {
    setTouched({ ...touched, [field]: true });
  };

  // Validate form
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // Agent type is required
    const agentTypeValidation = validateRequired(agentType);
    if (!agentTypeValidation.isValid) {
      newErrors.agentType = agentTypeValidation.message || 'Agent type is required';
    }

    // Matching threshold must be a number between 0 and 1
    const matchingThresholdValidation = validateNumber(matchingThreshold, 0, 1);
    if (!matchingThresholdValidation.isValid) {
      newErrors.matchingThreshold = matchingThresholdValidation.message || 'Must be a number between 0 and 1';
    }

    // Numeric tolerance must be a positive number
    const numericToleranceValidation = validateNumber(numericTolerance, 0);
    if (!numericToleranceValidation.isValid) {
      newErrors.numericTolerance = numericToleranceValidation.message || 'Must be a positive number';
    }

    // Report bucket is required
    const reportBucketValidation = validateRequired(reportBucket);
    if (!reportBucketValidation.isValid) {
      newErrors.reportBucket = reportBucketValidation.message || 'Report bucket is required';
    }

    // Additional validation for date range
    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      if (start > end) {
        newErrors.endDate = 'End date must be after start date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Validate on field change if touched
  useEffect(() => {
    if (Object.keys(touched).length > 0) {
      validateForm();
    }
  }, [agentType, matchingThreshold, numericTolerance, reportBucket, startDate, endDate]);

  // Build current config object
  const buildConfig = (): AgentRunConfig => {
    // Parse additional parameters
    let additionalParamsObj = {};
    try {
      if (additionalParams.trim()) {
        additionalParamsObj = JSON.parse(additionalParams);
      }
    } catch (error) {
      // Ignore parsing errors here
    }

    return {
      agentType,
      parameters: {
        matchingThreshold: parseFloat(matchingThreshold) || 0,
        numericTolerance: parseFloat(numericTolerance) || 0,
        reportBucket,
        ...additionalParamsObj,
      },
      inputData: {
        tradeIds: tradeIds ? tradeIds.split(',').map((id) => id.trim()) : undefined,
        documentIds: documentIds ? documentIds.split(',').map((id) => id.trim()) : undefined,
        dateRange: startDate && endDate ? { startDate, endDate } : undefined,
      },
    };
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    const allTouched: Record<string, boolean> = {};
    ['agentType', 'matchingThreshold', 'numericTolerance', 'reportBucket', 'startDate', 'endDate'].forEach(
      (field) => {
        allTouched[field] = true;
      }
    );
    setTouched(allTouched);

    // Validate form
    if (!validateForm()) {
      return;
    }

    // Parse additional parameters
    let additionalParamsObj = {};
    try {
      if (additionalParams.trim()) {
        additionalParamsObj = JSON.parse(additionalParams);
      }
    } catch (error) {
      setErrors({
        ...errors,
        additionalParams: 'Invalid JSON format',
      });
      return;
    }

    // Build config object
    const config = buildConfig();

    // Submit form
    if (onSubmit) {
      onSubmit(config);
    }
  };
  
  // Handle save configuration
  const handleSaveConfig = async (name: string, description: string) => {
    setSaveError(null);
    
    try {
      const config = buildConfig();
      const agentService = AgentService.getInstance();
      
      await agentService.saveConfiguration({
        name,
        description,
        config,
      });
    } catch (error) {
      setSaveError((error as Error).message);
      throw error;
    }
  };
  
  // Handle load configuration
  const handleLoadConfig = (savedConfig: SavedConfiguration) => {
    // Update form with loaded configuration
    setAgentType(savedConfig.config.agentType);
    setMatchingThreshold(savedConfig.config.parameters.matchingThreshold?.toString() || '0.85');
    setNumericTolerance(savedConfig.config.parameters.numericTolerance?.toString() || '0.001');
    setReportBucket(savedConfig.config.parameters.reportBucket || 'reconciliation-reports');
    
    // Update input data
    setTradeIds(savedConfig.config.inputData?.tradeIds?.join(', ') || '');
    setDocumentIds(savedConfig.config.inputData?.documentIds?.join(', ') || '');
    setStartDate(savedConfig.config.inputData?.dateRange?.startDate || '');
    setEndDate(savedConfig.config.inputData?.dateRange?.endDate || '');
    
    // Update additional parameters
    const { matchingThreshold, numericTolerance, reportBucket, ...additionalParams } = savedConfig.config.parameters;
    if (Object.keys(additionalParams).length > 0) {
      setAdditionalParams(JSON.stringify(additionalParams, null, 2));
    } else {
      setAdditionalParams('');
    }
  };

  // Agent type options
  const agentTypeOptions = [
    { value: 'trade-pdf-processing', label: 'Trade PDF Processing' },
    { value: 'trade-matching', label: 'Trade Matching' },
    { value: 'reconciliation', label: 'Reconciliation' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium leading-6 text-gray-900">New Agent Run</h3>
        <p className="mt-1 text-sm text-gray-500">
          Configure and trigger a new AI agent run for trade reconciliation
        </p>
      </div>

      {saveError && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error saving configuration</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{saveError}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-gray-50 p-6 rounded-md border border-gray-200">
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
            <FormSelect
              id="agent-type"
              name="agent-type"
              label="Agent Type"
              options={agentTypeOptions}
              value={agentType}
              onChange={(e) => setAgentType(e.target.value)}
              onBlur={() => handleBlur('agentType')}
              error={touched.agentType ? errors.agentType : undefined}
              required
              className="sm:col-span-2"
            />

            <FormInput
              id="matching-threshold"
              name="matching-threshold"
              label="Matching Threshold"
              type="number"
              placeholder="0.85"
              value={matchingThreshold}
              onChange={(e) => setMatchingThreshold(e.target.value)}
              onBlur={() => handleBlur('matchingThreshold')}
              error={touched.matchingThreshold ? errors.matchingThreshold : undefined}
              helpText="Value between 0 and 1 that determines how closely items must match"
              min={0}
              max={1}
              step={0.01}
            />

            <FormInput
              id="numeric-tolerance"
              name="numeric-tolerance"
              label="Numeric Tolerance"
              type="number"
              placeholder="0.001"
              value={numericTolerance}
              onChange={(e) => setNumericTolerance(e.target.value)}
              onBlur={() => handleBlur('numericTolerance')}
              error={touched.numericTolerance ? errors.numericTolerance : undefined}
              helpText="Tolerance for numeric comparisons"
              min={0}
              step={0.001}
            />

            <FormInput
              id="report-bucket"
              name="report-bucket"
              label="Report Bucket"
              placeholder="reconciliation-reports"
              value={reportBucket}
              onChange={(e) => setReportBucket(e.target.value)}
              onBlur={() => handleBlur('reportBucket')}
              error={touched.reportBucket ? errors.reportBucket : undefined}
              helpText="Storage location for generated reports"
              required
            />

            <div className="sm:col-span-2 border-t border-gray-200 pt-5">
              <h4 className="text-sm font-medium text-gray-900">Input Data</h4>
            </div>

            <FormInput
              id="trade-ids"
              name="trade-ids"
              label="Trade IDs"
              placeholder="TR001, TR002, TR003"
              value={tradeIds}
              onChange={(e) => setTradeIds(e.target.value)}
              helpText="Comma-separated list of trade IDs to process"
            />

            <FormInput
              id="document-ids"
              name="document-ids"
              label="Document IDs"
              placeholder="DOC001, DOC002, DOC003"
              value={documentIds}
              onChange={(e) => setDocumentIds(e.target.value)}
              helpText="Comma-separated list of document IDs to process"
            />

            <FormInput
              id="start-date"
              name="start-date"
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              onBlur={() => handleBlur('startDate')}
              error={touched.startDate ? errors.startDate : undefined}
            />

            <FormInput
              id="end-date"
              name="end-date"
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              onBlur={() => handleBlur('endDate')}
              error={touched.endDate ? errors.endDate : undefined}
            />

            <FormTextarea
              id="additional-params"
              name="additional-params"
              label="Additional Parameters (JSON)"
              placeholder='{"param1": "value1", "param2": 123}'
              value={additionalParams}
              onChange={(e) => setAdditionalParams(e.target.value)}
              onBlur={() => handleBlur('additionalParams')}
              error={touched.additionalParams ? errors.additionalParams : undefined}
              helpText="Additional parameters in JSON format"
              className="sm:col-span-2"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-5">
            <button
              type="button"
              onClick={() => setIsLoadModalOpen(true)}
              className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              disabled={isLoading}
            >
              Load Configuration
            </button>
            <button
              type="button"
              onClick={() => setIsSaveModalOpen(true)}
              className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              disabled={isLoading}
            >
              Save Configuration
            </button>
            <button
              type="submit"
              className="px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              disabled={isLoading}
            >
              {isLoading ? 'Starting...' : 'Start Agent Run'}
            </button>
          </div>
        </form>
      </div>

      {/* Save Configuration Modal */}
      <SaveConfigModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        onSave={handleSaveConfig}
        config={buildConfig()}
        isLoading={isLoading}
      />

      {/* Load Configuration Modal */}
      <LoadConfigModal
        isOpen={isLoadModalOpen}
        onClose={() => setIsLoadModalOpen(false)}
        onLoad={handleLoadConfig}
      />
    </div>
  );
};

export default AgentRunForm;