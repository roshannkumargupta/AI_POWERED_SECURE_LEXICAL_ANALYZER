import React from 'react';
import { CheckCircle2, AlertOctagon, AlertTriangle, Info, X } from 'lucide-react';
import { ToastItem } from '../state/store';

interface ToastProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div style={containerStyle}>
      {toasts.map((toast) => {
        let icon = <Info size={16} color="var(--accent)" />;
        let borderColor = 'var(--border)';

        if (toast.type === 'success') {
          icon = <CheckCircle2 size={16} color="var(--success)" />;
          borderColor = 'rgba(61, 220, 151, 0.4)';
        } else if (toast.type === 'error') {
          icon = <AlertOctagon size={16} color="var(--critical)" />;
          borderColor = 'rgba(255, 77, 109, 0.4)';
        } else if (toast.type === 'warning') {
          icon = <AlertTriangle size={16} color="var(--medium)" />;
          borderColor = 'rgba(245, 197, 66, 0.4)';
        }

        return (
          <div key={toast.id} style={{ ...toastItemStyle, borderColor }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
              {icon}
              <span style={messageStyle}>{toast.message}</span>
            </div>

            {toast.actionLabel && toast.onAction && (
              <button
                style={actionButtonStyle}
                onClick={() => {
                  toast.onAction!();
                  onDismiss(toast.id);
                }}
              >
                {toast.actionLabel}
              </button>
            )}

            <button
              style={closeButtonStyle}
              onClick={() => onDismiss(toast.id)}
              aria-label="Dismiss notification"
            >
              <X size={14} color="var(--muted)" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  position: 'fixed',
  bottom: '36px',
  right: '24px',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  zIndex: 2000,
  maxWidth: '420px',
  pointerEvents: 'none',
};

const toastItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '12px',
  padding: '10px 14px',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
  pointerEvents: 'auto',
  animation: 'slideIn 150ms ease-out',
};

const messageStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text)',
  lineHeight: 1.4,
};

const actionButtonStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--accent)',
  backgroundColor: 'rgba(79, 140, 255, 0.15)',
  padding: '4px 8px',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
};

const closeButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '2px',
  cursor: 'pointer',
};
