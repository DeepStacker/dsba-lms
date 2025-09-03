import React, { useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string | React.ReactNode;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  hideCloseButton?: boolean;
  className?: string;
  footer?: React.ReactNode;
  hideEscapeKey?: boolean;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  hideCloseButton = false,
  className = '',
  footer,
  hideEscapeKey = false,
}) => {
  // Handle Escape key
  useEffect(() => {
    if (hideEscapeKey) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose, hideEscapeKey]);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    '2xl': 'max-w-6xl',
    full: 'max-w-full mx-4',
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-25 transition-opacity" />

      {/* Container */}
      <div className="fixed inset-0 z-10 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <Dialog.Panel
            className={`w-full ${sizeClasses[size]} transform rounded-lg bg-white shadow-xl transition-all ${className}`}
          >
            {/* Header */}
            {(title || !hideCloseButton) && (
              <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
                {title && (
                  <Dialog.Title as="div" className="text-lg font-medium text-gray-900">
                    {title}
                  </Dialog.Title>
                )}
                {!hideCloseButton && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={onClose}
                    className="p-1"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </Button>
                )}
              </div>
            )}

            {/* Content */}
            <div className="px-6 py-4 max-h-96 overflow-y-auto">
              {children}
            </div>

            {/* Footer */}
            {footer && (
              <div className="flex items-center justify-end gap-3 border-t border-gray-200 px-6 py-4">
                {footer}
              </div>
            )}
          </Dialog.Panel>
        </div>
      </div>
    </Dialog>
  );
};

// Confirmation Dialog
interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: 'primary' | 'danger' | 'success';
  loading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
  loading = false,
}) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    title={title}
    size="sm"
    footer={
      <>
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          {cancelText}
        </Button>
        <Button
          variant={confirmVariant}
          onClick={onConfirm}
          isLoading={loading}
        >
          {confirmText}
        </Button>
      </>
    }
  >
    <p className="text-gray-700">{message}</p>
  </Modal>
);

// Form Dialog
interface FormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  title: string;
  children: React.ReactNode;
  submitText?: string;
  cancelText?: string;
  loading?: boolean;
  initialData?: Record<string, any>;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const FormDialog: React.FC<FormDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  children,
  submitText = 'Save',
  cancelText = 'Cancel',
  loading = false,
  size = 'md',
}) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    title={title}
    size={size}
    footer={
      <>
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          {cancelText}
        </Button>
        <Button
          variant="primary"
          onClick={onSubmit}
          isLoading={loading}
          type="submit"
        >
          {submitText}
        </Button>
      </>
    }
  >
    <form onSubmit={onSubmit}>
      {children}
    </form>
  </Modal>
);

// Alert Dialog
interface AlertDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  actionText?: string;
  onAction?: () => void;
}

export const AlertDialog: React.FC<AlertDialogProps> = ({
  isOpen,
  onClose,
  title,
  message,
  type = 'info',
  actionText,
  onAction,
}) => {
  const iconClasses = {
    info: 'text-blue-500',
    success: 'text-green-500',
    warning: 'text-yellow-500',
    error: 'text-red-500',
  };

  const icon = {
    info: 'ℹ️',
    success: '✓',
    warning: '⚠️',
    error: '✕',
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-3">
          <span className={`text-2xl ${iconClasses[type]}`}>
            {icon[type]}
          </span>
          {title}
        </div>
      }
      size="sm"
      footer={
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            OK
          </Button>
          {actionText && onAction && (
            <Button variant="primary" onClick={onAction}>
              {actionText}
            </Button>
          )}
        </div>
      }
    >
      <p className="text-gray-700">{message}</p>
    </Modal>
  );
};
