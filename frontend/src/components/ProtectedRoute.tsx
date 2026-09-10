/**
 * Protected route wrapper — redirects to login if not authenticated.
 */

import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const [takingLonger, setTakingLonger] = useState(false);

  useEffect(() => {
    if (!isLoading) return;
    const timer = setTimeout(() => {
      setTakingLonger(true);
    }, 3000);
    return () => clearTimeout(timer);
  }, [isLoading]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--canvas)] p-6 text-center">
        <div className="relative mb-4">
          <Loader2 size={36} className="animate-spin text-[var(--brand)]" />
        </div>
        <p className="text-sm font-semibold text-[var(--text)]">
          Connecting to COMPLIQ workspace...
        </p>
        {takingLonger && (
          <p className="mt-2 max-w-sm text-xs text-[var(--text-muted)]">
            Waking up cloud services on Render. This may take a few seconds on initial startup.
          </p>
        )}
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
