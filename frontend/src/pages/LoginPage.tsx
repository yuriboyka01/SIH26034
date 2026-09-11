import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  UserRound,
  Loader2,
  ScanText,
  FileCheck2,
  Gavel,
  Scale
} from 'lucide-react';
import { Alert } from '../components/ui';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const switchMode = () => {
    setIsRegister((current) => !current);
    setError('');
    setConfirmPassword('');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (isRegister && password !== confirmPassword) {
      setError('Passwords do not match. Check both password fields and try again.');
      return;
    }

    setLoading(true);
    try {
      const response = isRegister
        ? await apiRegister({ name, email, password })
        : await apiLogin({ email, password });
      login(response);
      navigate('/dashboard');
    } catch (err: any) {
      const message =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail?.[0]?.msg ||
        'We could not complete that request. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-aside" aria-label="COMPLIQ product overview">
        <div className="auth-brand">
          <img src="/logo.jpeg" alt="COMPLIQ Logo" />
          <div>
            <h1>COMPLIQ</h1>
            <span>Compliance Workspace</span>
          </div>
        </div>

        <div className="max-w-xl z-10 relative mt-8 lg:mt-16">
          <p className="text-kicker mb-2 sm:mb-4" style={{ color: 'var(--accent-on-dark)' }}>Legal Metrology Compliance System</p>
          <h2 className="heading-display text-white text-2xl sm:text-3xl lg:text-4xl">Clear evidence.<br className="hidden sm:inline"/> Confident action.</h2>
          <p className="text-body text-[var(--sidebar-text-muted)] mt-3 sm:mt-6 text-sm sm:text-base lg:text-lg max-w-md">
            AI-powered inspection for safer markets, transparent trade, and a more compliant India.
          </p>

          <div className="mt-8 lg:mt-16 space-y-4 sm:space-y-6 hidden sm:block">
            {[
              { icon: ScanText, title: 'Evidence Capture & OCR', desc: 'Automatic extraction of package declarations.' },
              { icon: FileCheck2, title: 'AI Rule Evaluation', desc: 'Direct checking against Legal Metrology requirements.' },
              { icon: Gavel, title: 'Inspector Decision', desc: 'Traceable, evidence-backed compliance findings.' }
            ].map((item, index) => (
              <div key={index} className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-[var(--sidebar-surface)] border border-[var(--sidebar-line)] flex items-center justify-center shrink-0">
                  <item.icon size={18} style={{ color: 'var(--accent-on-dark)' }} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{item.title}</p>
                  <p className="text-xs sm:text-sm text-[var(--sidebar-text-faint)] mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Subtle watermark scale */}
        <Scale
          size={340}
          strokeWidth={0.6}
          className="absolute -right-16 -bottom-16 pointer-events-none hidden xl:block"
          style={{ color: 'rgba(255,255,255,0.05)' }}
        />
      </section>

      <section className="auth-main" aria-label={isRegister ? 'Create an account' : 'Sign in'}>
        <div className="w-full max-w-[440px] elevated-panel p-6 sm:p-8 md:p-10 z-10 relative rounded-2xl">

          <header className="mb-6 sm:mb-8">
            <h2 className="heading-page mb-1.5 sm:mb-2">{isRegister ? 'Create Account' : 'Sign in to your case file'}</h2>
            <p className="text-body text-xs sm:text-sm">
              {isRegister
                ? 'Start a new inspection workspace with your existing access model.'
                : 'Continue an open inspection or start a new one.'}
            </p>
          </header>

          {error && <div className="mb-5 sm:mb-6"><Alert tone="error">{error}</Alert></div>}

          <form className="space-y-4 sm:space-y-5" onSubmit={handleSubmit} noValidate={false}>
            {isRegister && (
              <div>
                <label className="text-xs sm:text-sm font-semibold text-[var(--text)] block mb-1.5" htmlFor="name">Full name</label>
                <div className="relative">
                  <UserRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" size={18} />
                  <input id="name" className="neo-input pl-10 text-sm" type="text" value={name} onChange={(event) => setName(event.target.value)} required placeholder="Your full name" />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs sm:text-sm font-semibold text-[var(--text)] block mb-1.5" htmlFor="email">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" size={18} />
                <input id="email" className="neo-input pl-10 text-sm" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="name@organisation.gov.in" />
              </div>
            </div>

            <div>
              <label className="text-xs sm:text-sm font-semibold text-[var(--text)] block mb-1.5" htmlFor="password">Password</label>
              <div className="relative">
                <LockKeyhole className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" size={18} />
                <input id="password" className="neo-input pl-10 pr-10 text-sm" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} required placeholder="Enter your password" />
                <button className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-faint)] hover:text-[var(--text)] transition-colors p-1" type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password">
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {isRegister && (
              <div>
                <label className="text-xs sm:text-sm font-semibold text-[var(--text)] block mb-1.5" htmlFor="confirmPassword">Confirm password</label>
                <div className="relative">
                  <LockKeyhole className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" size={18} />
                  <input id="confirmPassword" className="neo-input pl-10 text-sm" type={showPassword ? 'text' : 'password'} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required placeholder="Re-enter your password" />
                </div>
              </div>
            )}

            <button className="neo-button-primary w-full mt-3 shadow-md shadow-[var(--brand-soft)]" type="submit" disabled={loading}>
              {loading ? (
                <><Loader2 size={18} className="animate-spin" /> {isRegister ? 'Creating account…' : 'Signing in…'}</>
              ) : (
                <>{isRegister ? 'Create account' : 'Sign in'}</>
              )}
            </button>
          </form>

          <p className="mt-6 sm:mt-8 text-center text-xs sm:text-sm text-[var(--text-muted)]">
            {isRegister ? 'Already have an account?' : 'Need access to COMPLIQ?'}{' '}
            <button type="button" className="font-semibold text-[var(--brand)] hover:text-[var(--brand-hover)] transition-colors" onClick={switchMode}>
              {isRegister ? 'Sign in' : 'Create an account'}
            </button>
          </p>
        </div>
      </section>
    </main>
  );
}
