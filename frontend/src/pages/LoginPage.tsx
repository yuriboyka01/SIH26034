import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  FileCheck2,
  Loader2,
  LockKeyhole,
  Mail,
  ScanLine,
  ShieldCheck,
  UserRound,
} from 'lucide-react';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
      <section className="auth-aside" aria-label="SIH26034 product overview">
        <div className="auth-brand">
          <span className="auth-brand-mark" aria-hidden="true"><ShieldCheck size={20} /></span>
          SIH26034
        </div>

        <div className="auth-positioning">
          <p className="app-kicker">Legal Metrology Compliance System</p>
          <h1>Clear evidence. Confident action.</h1>
          <p>
            A focused workspace for package inspection, declaration review, and evidence-led
            compliance analysis under the Legal Metrology framework.
          </p>
          <div className="auth-workflow" aria-label="Compliance workflow">
            {['Evidence', 'OCR extraction', 'Rule evaluation', 'Inspector decision'].map((stage, index) => <div className="auth-workflow-item" key={stage}><span>{String(index + 1).padStart(2, '0')}</span>{stage}</div>)}
          </div>
        </div>

        <div className="auth-trust" aria-label="Product capabilities">
          <span><ScanLine size={15} aria-hidden="true" /> OCR-assisted review</span>
          <span><FileCheck2 size={15} aria-hidden="true" /> Traceable inspection records</span>
          <span><ShieldCheck size={15} aria-hidden="true" /> Role-based access</span>
        </div>
      </section>

      <section className="auth-main" aria-label={isRegister ? 'Create an account' : 'Sign in'}>
        <div className="auth-form-wrap">
          <header className="auth-form-header">
            <p className="app-kicker">Secure access</p>
            <h2>{isRegister ? 'Create your inspector account' : 'Sign in to your workspace'}</h2>
            <p>
              {isRegister
                ? 'Start a new inspection workspace with your existing access model.'
                : 'Use your authorised SIH26034 account to continue.'}
            </p>
          </header>

          {error && (
            <div className="ui-alert ui-alert-error mb-5" role="alert">
              <AlertCircle size={17} aria-hidden="true" className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate={false}>
            {isRegister && (
              <div>
                <label className="ui-label" htmlFor="name">Full name</label>
                <div className="auth-input-icon">
                  <UserRound aria-hidden="true" />
                  <input id="name" className="ui-input" type="text" value={name} onChange={(event) => setName(event.target.value)} required minLength={1} maxLength={255} autoComplete="name" placeholder="Your full name" />
                </div>
              </div>
            )}

            <div>
              <label className="ui-label" htmlFor="email">Email address</label>
              <div className="auth-input-icon">
                <Mail aria-hidden="true" />
                <input id="email" className="ui-input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" placeholder="name@organisation.gov.in" />
              </div>
            </div>

            <div>
              <label className="ui-label" htmlFor="password">Password</label>
              <div className="auth-input-icon">
                <LockKeyhole aria-hidden="true" />
                <input id="password" className="ui-input" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} required minLength={6} maxLength={128} autoComplete={isRegister ? 'new-password' : 'current-password'} placeholder="Enter your password" />
                <button className="auth-password-toggle" type="button" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                  {showPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </div>
              {isRegister && <p className="ui-field-hint">Use at least 6 characters. Your password is never displayed in the workspace.</p>}
            </div>

            {isRegister && (
              <div>
                <label className="ui-label" htmlFor="confirmPassword">Confirm password</label>
                <div className="auth-input-icon">
                  <LockKeyhole aria-hidden="true" />
                  <input id="confirmPassword" className="ui-input" type={showConfirmPassword ? 'text' : 'password'} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required minLength={6} autoComplete="new-password" placeholder="Re-enter your password" />
                  <button className="auth-password-toggle" type="button" onClick={() => setShowConfirmPassword((current) => !current)} aria-label={showConfirmPassword ? 'Hide confirmation password' : 'Show confirmation password'}>
                    {showConfirmPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                  </button>
                </div>
              </div>
            )}

            <button className="ui-button-primary w-full" type="submit" disabled={loading}>
              {loading ? <><Loader2 size={17} className="animate-spin" aria-hidden="true" /> {isRegister ? 'Creating account…' : 'Signing in…'}</> : <>{isRegister ? 'Create account' : 'Sign in securely'} <CheckCircle2 size={17} aria-hidden="true" /></>}
            </button>
          </form>

          <p className="auth-switch">
            {isRegister ? 'Already have an account?' : 'Need access to SIH26034?'}{' '}
            <button type="button" onClick={switchMode}>{isRegister ? 'Sign in' : 'Create an account'}</button>
          </p>
        </div>
      </section>
    </main>
  );
}
