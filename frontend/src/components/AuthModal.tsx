import { useEffect, useState } from 'react';
import { requestLoginOtp, verifyLoginOtp } from '../api';
import type { AppLanguage } from '../App';
import type { AuthRole, AuthSession } from '../types';

const authCopy = {
  en: {
    eyebrow: 'Role login',
    title: 'Login to BolBazaar',
    otpTitle: 'Enter the OTP',
    close: 'Close',
    buyer: 'Buyer',
    buyerBody: 'Marketplace view with live listings, filters, and order booking.',
    seller: 'Seller',
    sellerBody: 'Seller cockpit with khata, pending orders, listings, and WhatsApp-linked stats.',
    phone: 'Phone number',
    phonePlaceholder: 'Enter the number you use for BolBazaar',
    otp: 'OTP',
    otpPlaceholder: 'Enter the 6-digit code',
    demoOtp: 'Demo OTP',
    changeNumber: 'Change number',
    chooseRole: 'Choose buyer or seller first.',
    sendOtp: 'Send OTP',
    sending: 'Sending...',
    verify: 'Verify and continue',
    verifying: 'Verifying...',
    sendError: 'Failed to send OTP',
    verifyError: 'Failed to verify OTP',
  },
  hi: {
    eyebrow: 'रोल लॉगिन',
    title: 'BolBazaar में लॉगिन करें',
    otpTitle: 'OTP दर्ज करें',
    close: 'बंद करें',
    buyer: 'खरीदार',
    buyerBody: 'लाइव लिस्टिंग, फिल्टर और ऑर्डर बुकिंग वाला मार्केटप्लेस व्यू।',
    seller: 'विक्रेता',
    sellerBody: 'खाता, पेंडिंग ऑर्डर, लिस्टिंग और WhatsApp-linked stats वाला seller cockpit.',
    phone: 'फोन नंबर',
    phonePlaceholder: 'BolBazaar के लिए इस्तेमाल किया गया नंबर दर्ज करें',
    otp: 'OTP',
    otpPlaceholder: '6 अंकों का कोड दर्ज करें',
    demoOtp: 'Demo OTP',
    changeNumber: 'नंबर बदलें',
    chooseRole: 'पहले buyer या seller चुनें।',
    sendOtp: 'OTP भेजें',
    sending: 'भेजा जा रहा है...',
    verify: 'Verify करके आगे बढ़ें',
    verifying: 'Verify हो रहा है...',
    sendError: 'OTP भेजने में समस्या हुई',
    verifyError: 'OTP verify करने में समस्या हुई',
  },
};

export default function AuthModal({
  language,
  onLanguageChange,
  isOpen,
  initialRole,
  onClose,
  onSuccess,
}: {
  language: AppLanguage;
  onLanguageChange: (language: AppLanguage) => void;
  isOpen: boolean;
  initialRole: AuthRole | null;
  onClose: () => void;
  onSuccess: (session: AuthSession) => void;
}) {
  const [role, setRole] = useState<AuthRole | null>(initialRole);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [requestId, setRequestId] = useState<string | null>(null);
  const [otpCode, setOtpCode] = useState('');
  const [requestNote, setRequestNote] = useState<string | null>(null);
  const [demoOtp, setDemoOtp] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setRole(initialRole);
    setPhoneNumber('');
    setRequestId(null);
    setOtpCode('');
    setRequestNote(null);
    setDemoOtp(null);
    setSending(false);
    setVerifying(false);
    setError(null);
  }, [initialRole, isOpen]);

  if (!isOpen) {
    return null;
  }

  const otpStep = requestId !== null;
  const copy = authCopy[language];

  return (
    <div className="modal-backdrop auth-backdrop">
      <div className="modal card auth-modal">
        <div className="modal-language-row">
          <span className="label">Language</span>
          <div className="language-switcher" aria-label="Language switcher">
            <button
              type="button"
              className={language === 'en' ? 'language-switch-active' : ''}
              onClick={() => onLanguageChange('en')}
            >
              English
            </button>
            <button
              type="button"
              className={language === 'hi' ? 'language-switch-active' : ''}
              onClick={() => onLanguageChange('hi')}
            >
              हिंदी
            </button>
          </div>
        </div>
        <div className="modal-header">
          <div>
            <span className="eyebrow">{copy.eyebrow}</span>
            <h3>{otpStep ? copy.otpTitle : copy.title}</h3>
          </div>
          <button className="ghost-button" onClick={onClose}>{copy.close}</button>
        </div>

        {!otpStep && (
          <div className="role-grid">
            <button
              className={`role-card ${role === 'buyer' ? 'role-card-active' : ''}`}
              onClick={() => setRole('buyer')}
            >
              <strong>{copy.buyer}</strong>
              <span>{copy.buyerBody}</span>
            </button>
            <button
              className={`role-card ${role === 'seller' ? 'role-card-active' : ''}`}
              onClick={() => setRole('seller')}
            >
              <strong>{copy.seller}</strong>
              <span>{copy.sellerBody}</span>
            </button>
          </div>
        )}

        <div className="auth-form-grid">
          {!otpStep && (
            <div>
              <label className="label">{copy.phone}</label>
              <input
                value={phoneNumber}
                onChange={(event) => setPhoneNumber(event.target.value)}
                placeholder={copy.phonePlaceholder}
              />
            </div>
          )}

          {otpStep && (
            <div>
              <label className="label">{copy.otp}</label>
              <input
                value={otpCode}
                onChange={(event) => setOtpCode(event.target.value)}
                placeholder={copy.otpPlaceholder}
              />
            </div>
          )}
        </div>

        {requestNote && <div className="notice-banner">{requestNote}</div>}
        {demoOtp && (
          <div className="otp-preview">
            <span className="label">{copy.demoOtp}</span>
            <strong>{demoOtp}</strong>
          </div>
        )}
        {error && <div className="error-banner">{error}</div>}

        <div className="action-row">
          {otpStep && (
            <button
              className="ghost-button"
              onClick={() => {
                setRequestId(null);
                setOtpCode('');
                setRequestNote(null);
                setDemoOtp(null);
                setError(null);
              }}
            >
              {copy.changeNumber}
            </button>
          )}
          {!otpStep ? (
            <button
              className="primary-button"
              disabled={sending || !role || phoneNumber.trim().length < 10}
              onClick={async () => {
                if (!role) {
                  setError(copy.chooseRole);
                  return;
                }
                setSending(true);
                setError(null);
                try {
                  const response = await requestLoginOtp({
                    role,
                    phone_number: phoneNumber,
                  });
                  setRequestId(response.request_id);
                  setRequestNote(response.note || null);
                  setDemoOtp(response.demo_otp || null);
                } catch (err) {
                  setError(err instanceof Error ? err.message : copy.sendError);
                } finally {
                  setSending(false);
                }
              }}
            >
              {sending ? copy.sending : copy.sendOtp}
            </button>
          ) : (
            <button
              className="primary-button"
              disabled={verifying || otpCode.trim().length < 4 || !requestId}
              onClick={async () => {
                if (!requestId) {
                  return;
                }
                setVerifying(true);
                setError(null);
                try {
                  const response = await verifyLoginOtp({
                    request_id: requestId,
                    otp_code: otpCode,
                  });
                  onSuccess(response.session);
                } catch (err) {
                  setError(err instanceof Error ? err.message : copy.verifyError);
                } finally {
                  setVerifying(false);
                }
              }}
            >
              {verifying ? copy.verifying : copy.verify}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
