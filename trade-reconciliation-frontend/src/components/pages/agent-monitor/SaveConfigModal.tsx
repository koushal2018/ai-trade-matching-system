import React, { useState } from 'react';
import Modal from '../../common/Modal';
import FormInput from '../../common/FormInput';
import FormTextarea from '../../common/FormTextarea';
import { validateRequired } from '../../../utils/validation';
import { AgentRunConfig } from '../../../types/agent';

interface SaveConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, description: string) => Promise<void>;
  config: AgentRunConfig;
  isLoading?: boolean;
}

const SaveConfigModal: React.FC<SaveConfigModalProps> = ({
  isOpen,
  onClose,
  onSave,
  config,
  isLoading = false,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSave = async () => {
    // Validate form
    const nameValidation = validateRequired(name);
    if (!nameValidation.isValid) {
      setErrors({ ...errors, name: nameValidation.message || 'Name is required' });
      return;
    }

    // Clear errors
    setErrors({});

    // Save configuration
    try {
      await onSave(name, description);
      // Reset form
      setName('');
      setDescription('');
      // Close modal
      onClose();
    } catch (error) {
      setErrors({ ...errors, form: (error as Error).message });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Save Configuration" size="md">
      <div className="mt-4 space-y-4">
        <FormInput
          id="config-name"
          name="config-name"
          label="Configuration Name"
          placeholder="My Configuration"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
          required
        />

        <FormTextarea
          id="config-description"
          name="config-description"
          label="Description"
          placeholder="Description of this configuration"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          error={errors.description}
          rows={3}
        />

        <div className="mt-2 rounded-md bg-gray-50 p-4">
          <h4 className="text-sm font-medium text-gray-900">Configuration Preview</h4>
          <pre className="mt-2 text-xs text-gray-600 overflow-auto max-h-40">
            {JSON.stringify(config, null, 2)}
          </pre>
        </div>

        {errors.form && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{errors.form}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
          <button
            type="button"
            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm"
            onClick={handleSave}
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default SaveConfigModal;