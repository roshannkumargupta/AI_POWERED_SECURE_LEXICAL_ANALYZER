import React from 'react';

export interface Toast {
  id: string;
  msg: string;
  type?: 'info' | 'success' | 'warning' | 'error';
}

interface ToastBoxProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

export const ToastBox: React.FC<ToastBoxProps> = ({ toasts }) => {
  return (
    <div className="fixed bottom-10 right-4 z-50 flex flex-col gap-2 pointer-events-none" id="toastBox">
      {toasts.map((t) => {
        let icon = 'info';
        let colorClasses = 'border-border-primary text-text-primary';

        if (t.type === 'success') {
          icon = 'check_circle';
          colorClasses = 'text-status-success border-status-success/40';
        } else if (t.type === 'warning') {
          icon = 'warning';
          colorClasses = 'text-status-warning border-status-warning/40';
        } else if (t.type === 'error') {
          icon = 'error';
          colorClasses = 'text-status-error border-status-error/40';
        }

        return (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-elevated border ${colorClasses} text-[11px] shadow-2xl transition-all duration-200 animate-in fade-in slide-in-from-bottom-2`}
          >
            <span className="material-symbols-outlined text-[16px]">{icon}</span>
            <span className="font-medium">{t.msg}</span>
          </div>
        );
      })}
    </div>
  );
};

