import React from 'react';
import { Radio, RadioGroup, Checkbox, Textarea, Input } from '@headlessui/react';
import clsx from 'clsx';

interface QuestionRendererProps {
  question: any;
  response: any;
  onResponseChange: (response: any) => void;
  disabled?: boolean;
}

export const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  response,
  onResponseChange,
  disabled = false
}) => {
  if (!question) return null;

  const renderMCQ = () => (
    <div className="space-y-3">
      <RadioGroup value={response?.selectedOption || ''} onChange={(value) => onResponseChange({ selectedOption: value })}>
        <div className="space-y-2">
          {question.options?.map((option: any, index: number) => (
            <Radio
              key={option.id}
              value={option.id}
              disabled={disabled}
              className={({ checked }) =>
                clsx(
                  'relative flex cursor-pointer rounded-lg px-5 py-4 shadow-sm focus:outline-none border',
                  checked
                    ? 'bg-blue-50 border-blue-200 text-blue-900'
                    : 'bg-white border-gray-200 hover:bg-gray-50',
                  disabled && 'opacity-50 cursor-not-allowed'
                )
              }
            >
              {({ checked }) => (
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center">
                    <div className="text-sm">
                      <div className="flex items-center">
                        <div
                          className={clsx(
                            'h-4 w-4 rounded-full border-2 mr-3',
                            checked
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-300'
                          )}
                        >
                          {checked && (
                            <div className="h-full w-full rounded-full bg-white scale-50"></div>
                          )}
                        </div>
                        <span className="font-medium">
                          {String.fromCharCode(65 + index)}.
                        </span>
                        <span className="ml-2">{option.text}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </Radio>
          ))}
        </div>
      </RadioGroup>
    </div>
  );

  const renderMSQ = () => (
    <div className="space-y-3">
      {question.options?.map((option: any, index: number) => (
        <div
          key={option.id}
          className={clsx(
            'relative flex cursor-pointer rounded-lg px-5 py-4 shadow-sm focus:outline-none border',
            response?.selectedOptions?.includes(option.id)
              ? 'bg-blue-50 border-blue-200 text-blue-900'
              : 'bg-white border-gray-200 hover:bg-gray-50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <Checkbox
            checked={response?.selectedOptions?.includes(option.id) || false}
            onChange={(checked) => {
              const currentOptions = response?.selectedOptions || [];
              const newOptions = checked
                ? [...currentOptions, option.id]
                : currentOptions.filter((id: number) => id !== option.id);
              onResponseChange({ selectedOptions: newOptions });
            }}
            disabled={disabled}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded mr-3 mt-0.5"
          />
          <div className="text-sm">
            <span className="font-medium">
              {String.fromCharCode(65 + index)}.
            </span>
            <span className="ml-2">{option.text}</span>
          </div>
        </div>
      ))}
    </div>
  );

  const renderTrueFalse = () => (
    <div className="space-y-3">
      <RadioGroup value={response?.answer || ''} onChange={(value) => onResponseChange({ answer: value })}>
        <div className="space-y-2">
          <Radio
            value="true"
            disabled={disabled}
            className={({ checked }) =>
              clsx(
                'relative flex cursor-pointer rounded-lg px-5 py-4 shadow-sm focus:outline-none border',
                checked
                  ? 'bg-green-50 border-green-200 text-green-900'
                  : 'bg-white border-gray-200 hover:bg-gray-50',
                disabled && 'opacity-50 cursor-not-allowed'
              )
            }
          >
            {({ checked }) => (
              <div className="flex items-center">
                <div
                  className={clsx(
                    'h-4 w-4 rounded-full border-2 mr-3',
                    checked
                      ? 'bg-green-600 border-green-600'
                      : 'border-gray-300'
                  )}
                >
                  {checked && (
                    <div className="h-full w-full rounded-full bg-white scale-50"></div>
                  )}
                </div>
                <span className="font-medium">True</span>
              </div>
            )}
          </Radio>
          
          <Radio
            value="false"
            disabled={disabled}
            className={({ checked }) =>
              clsx(
                'relative flex cursor-pointer rounded-lg px-5 py-4 shadow-sm focus:outline-none border',
                checked
                  ? 'bg-red-50 border-red-200 text-red-900'
                  : 'bg-white border-gray-200 hover:bg-gray-50',
                disabled && 'opacity-50 cursor-not-allowed'
              )
            }
          >
            {({ checked }) => (
              <div className="flex items-center">
                <div
                  className={clsx(
                    'h-4 w-4 rounded-full border-2 mr-3',
                    checked
                      ? 'bg-red-600 border-red-600'
                      : 'border-gray-300'
                  )}
                >
                  {checked && (
                    <div className="h-full w-full rounded-full bg-white scale-50"></div>
                  )}
                </div>
                <span className="font-medium">False</span>
              </div>
            )}
          </Radio>
        </div>
      </RadioGroup>
    </div>
  );

  const renderNumeric = () => (
    <div className="space-y-3">
      <Input
        type="number"
        placeholder="Enter your answer"
        value={response?.answer || ''}
        onChange={(value) => onResponseChange({ answer: value })}
        disabled={disabled}
        className="max-w-xs"
      />
      {question.unit && (
        <p className="text-sm text-gray-600">Unit: {question.unit}</p>
      )}
    </div>
  );

  const renderDescriptive = () => (
    <div className="space-y-3">
      <Textarea
        placeholder="Type your answer here..."
        value={response?.answer || ''}
        onChange={(e) => onResponseChange({ answer: e.target.value })}
        disabled={disabled}
        rows={8}
        className="w-full resize-none"
      />
      <div className="flex justify-between text-sm text-gray-500">
        <span>
          {question.maxWords && `Maximum ${question.maxWords} words`}
        </span>
        <span>
          {response?.answer ? response.answer.split(' ').length : 0} words
        </span>
      </div>
    </div>
  );

  const renderCoding = () => (
    <div className="space-y-3">
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Problem Statement:</h4>
        <div className="text-sm text-gray-700 whitespace-pre-wrap">
          {question.problemStatement}
        </div>
      </div>
      
      {question.sampleInput && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Sample Input:</h4>
          <pre className="text-sm text-blue-800 font-mono">
            {question.sampleInput}
          </pre>
        </div>
      )}
      
      {question.sampleOutput && (
        <div className="bg-green-50 rounded-lg p-4">
          <h4 className="font-medium text-green-900 mb-2">Sample Output:</h4>
          <pre className="text-sm text-green-800 font-mono">
            {question.sampleOutput}
          </pre>
        </div>
      )}
      
      <Textarea
        placeholder="Write your code here..."
        value={response?.code || ''}
        onChange={(e) => onResponseChange({ code: e.target.value })}
        disabled={disabled}
        rows={15}
        className="w-full font-mono text-sm resize-none"
      />
      
      {question.language && (
        <p className="text-sm text-gray-600">Language: {question.language}</p>
      )}
    </div>
  );

  const renderFileUpload = () => (
    <div className="space-y-3">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <input
          type="file"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              onResponseChange({ file: file, fileName: file.name });
            }
          }}
          disabled={disabled}
          accept={question.acceptedFileTypes || '*'}
          className="hidden"
          id={`file-upload-${question.id}`}
        />
        <label
          htmlFor={`file-upload-${question.id}`}
          className={clsx(
            'cursor-pointer text-blue-600 hover:text-blue-500',
            disabled && 'cursor-not-allowed opacity-50'
          )}
        >
          {response?.fileName ? (
            <div>
              <p className="font-medium">{response.fileName}</p>
              <p className="text-sm text-gray-500">Click to change file</p>
            </div>
          ) : (
            <div>
              <p className="font-medium">Click to upload file</p>
              <p className="text-sm text-gray-500">
                {question.acceptedFileTypes || 'Any file type accepted'}
              </p>
            </div>
          )}
        </label>
      </div>
      
      {question.maxFileSize && (
        <p className="text-sm text-gray-600">
          Maximum file size: {question.maxFileSize}
        </p>
      )}
    </div>
  );

  const renderQuestionContent = () => {
    switch (question.type) {
      case 'mcq':
        return renderMCQ();
      case 'msq':
        return renderMSQ();
      case 'tf':
        return renderTrueFalse();
      case 'numeric':
        return renderNumeric();
      case 'descriptive':
        return renderDescriptive();
      case 'coding':
        return renderCoding();
      case 'file_upload':
        return renderFileUpload();
      default:
        return <p className="text-red-600">Unsupported question type: {question.type}</p>;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Question Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Question {question.order || 1}
          </h2>
          <div className="text-sm text-gray-600">
            <span className="font-medium">{question.max_marks || question.maxMarks} marks</span>
          </div>
        </div>
        
        {/* Question Text */}
        <div className="prose max-w-none">
          <div 
            className="text-gray-800 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: question.text }}
          />
        </div>
        
        {/* Question Image/Media */}
        {question.imageUrl && (
          <div className="mt-4">
            <img
              src={question.imageUrl}
              alt="Question illustration"
              className="max-w-full h-auto rounded-lg border border-gray-200"
            />
          </div>
        )}
      </div>

      {/* Question Content */}
      <div className="space-y-4">
        {renderQuestionContent()}
      </div>

      {/* Question Footer */}
      {question.co && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Course Outcome: {question.co.code} - {question.co.title}
          </p>
        </div>
      )}
    </div>
  );
};