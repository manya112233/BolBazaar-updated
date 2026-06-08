import { useEffect, useState } from 'react';
import type { AppLanguage } from '../../App';

type DemoMessage = {
  speaker: 'seller' | 'system' | 'buyer';
  type?: 'text' | 'card';
  text: string;
  title?: string;
};

const demoMessages: Record<AppLanguage, DemoMessage[]> = {
  en: [
    { speaker: 'seller', text: 'Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup' },
    { speaker: 'system', type: 'card', title: 'Listing detected', text: 'Tomato · 50 kg · Rs 28/kg · Laxmi Nagar' },
    { speaker: 'seller', text: 'Photo sent' },
    { speaker: 'system', text: 'AI quality check complete. Listing is live.' },
    { speaker: 'buyer', text: 'Order placed for 20 kg' },
    { speaker: 'system', text: 'New order received. Accept or reject?' },
    { speaker: 'seller', text: 'Accept' },
    { speaker: 'system', text: 'Stock updated. Khata and dashboard synced.' },
  ],
  hi: [
    { speaker: 'seller', text: 'Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup' },
    { speaker: 'system', type: 'card', title: 'Listing detected', text: 'Tomato · 50 kg · Rs 28/kg · Laxmi Nagar' },
    { speaker: 'seller', text: 'Photo sent' },
    { speaker: 'system', text: 'AI quality check complete. Listing is live.' },
    { speaker: 'buyer', text: 'Order placed for 20 kg' },
    { speaker: 'system', text: 'New order received. Accept or reject?' },
    { speaker: 'seller', text: 'Accept' },
    { speaker: 'system', text: 'Stock updated. Khata and dashboard synced.' },
  ],
};

export default function WhatsAppCommerceDemo({ language }: { language: AppLanguage }) {
  const messages = demoMessages[language];
  const [visibleCount, setVisibleCount] = useState(1);

  useEffect(() => {
    setVisibleCount(1);
    const interval = window.setInterval(() => {
      setVisibleCount((count) => (count >= messages.length ? 1 : count + 1));
    }, 1400);
    return () => window.clearInterval(interval);
  }, [messages]);

  return (
    <div className="bb-landing-phone-stage" data-reveal>
      <div className="bb-landing-floating-badge bb-badge-ai">AI extraction</div>
      <div className="bb-landing-floating-badge bb-badge-map">Maps pickup normalized</div>
      <div className="bb-landing-floating-badge bb-badge-store">Firestore synced</div>

      <div className="bb-landing-phone-shell">
        <div className="bb-landing-phone-top">
          <span>9:41</span>
          <span>5G 88%</span>
        </div>
        <div className="bb-landing-phone-header">
          <div className="bb-landing-phone-avatar">BB</div>
          <div>
            <strong>BolBazaar</strong>
            <small>Seller commerce flow</small>
          </div>
          <span className="bb-landing-phone-status">Live</span>
        </div>

        <div className="bb-landing-chat-thread">
          {messages.slice(0, visibleCount).map((message, index) => (
            <div
              key={`${message.speaker}-${index}-${message.text}`}
              className={`bb-landing-chat-row bb-chat-${message.speaker}`}
            >
              <div className={`bb-landing-chat-bubble ${message.type === 'card' ? 'is-card' : ''}`}>
                {message.title ? <strong>{message.title}</strong> : null}
                <p>{message.text}</p>
              </div>
            </div>
          ))}
          {visibleCount < messages.length ? (
            <div className="bb-landing-chat-row bb-chat-system">
              <div className="bb-landing-typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          ) : null}
        </div>

        <div className="bb-landing-phone-input">
          <span>Voice note</span>
          <span>Photo</span>
          <span>Khata</span>
        </div>
      </div>
    </div>
  );
}
