import React from 'react';

interface FormTextareaProps {
  id: string;
  name: string;
  label: string;
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLTextAreaElement>) => void;
  error?: string;
  helpText?: string;
  required?: boolean;
  disabled?: boolean;
  rows?: number;
  className?: string;
}

const FormTextarea: React.FC<FormTextareaProps> = ({
  id,
  name,
  label,
  placeholder,
  value,
  onChange,
  onBlur,
  error,
  helpText,
  required = false,
  disabled = false,
  rows = 3,
  className = '',
}) => {
  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <div className="mt-1">
        <textarea
          id={id}
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          required={required}
          disabled={disabled}
          rows={rows}
          className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md ${
            error ? 'border-red-300' : ''
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
        />
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      {helpText && !error && <p className="mt-1 text-xs text-gray-500">{helpText}</p>}
    </div>
  );
};

export default FormTextarea;