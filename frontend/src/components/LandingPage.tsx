import { useEffect, useMemo, useState } from 'react';
import type { AppLanguage } from '../App';
import './LandingPage.css';
import ArchitectureFlow from './landing/ArchitectureFlow';
import ComparisonTable from './landing/ComparisonTable';
import WhatsAppCommerceDemo from './landing/WhatsAppCommerceDemo';

type LandingStats = {
  liveListings: number;
  activeSellers: number;
  acceptedOrders: number;
  alertsSent: number;
};

const navIds = ['problem', 'solution', 'how-it-works', 'impact', 'architecture', 'dashboard'] as const;

const landingCopy = {
  en: {
    badge: 'Google Solution Challenge · WhatsApp-first agri-commerce',
    title: 'Turn a farmer’s WhatsApp message into a live produce marketplace.',
    body:
      'BolBazaar helps farmers, FPOs, and local sellers create verified listings, manage orders, track khata, and pool fragmented buyer demand into bulk supply opportunities without installing a new app.',
    ctaPrimary: 'See how it works',
    ctaSecondary: 'Open dashboard',
    login: 'Login',
    navProblem: 'Problem',
    navSolution: 'Solution',
    navHow: 'How It Works',
    navImpact: 'Impact',
    navArchitecture: 'Architecture',
    navDashboard: 'Dashboard',
    proof: [
      'No app download for sellers',
      'Hindi/English voice-note support',
      'AI verified listings',
      'Khata and orders in one dashboard',
    ],
    metrics: [
      { value: '<30 sec', label: 'Listing creation', body: 'Seller stock becomes structured inventory in under half a minute.' },
      { value: '0', label: 'App downloads', body: 'Sellers continue on WhatsApp instead of learning a new app.' },
      { value: '3', label: 'Input modes', body: 'Text, voice, and image all feed the same operating pipeline.' },
      { value: '1', label: 'Unified dashboard', body: 'Orders, khata, verification, and insights live in one workspace.' },
    ],
  },
  hi: {
    badge: 'Google Solution Challenge · WhatsApp-first agri-commerce',
    title: 'Turn a farmer’s WhatsApp message into a live produce marketplace.',
    body:
      'BolBazaar farmers, FPOs, और local sellers को बिना नया app install कराए verified listings, orders, khata, और pooled buyer demand opportunities manage करने देता है.',
    ctaPrimary: 'How it works देखें',
    ctaSecondary: 'Dashboard खोलें',
    login: 'Login',
    navProblem: 'Problem',
    navSolution: 'Solution',
    navHow: 'How It Works',
    navImpact: 'Impact',
    navArchitecture: 'Architecture',
    navDashboard: 'Dashboard',
    proof: [
      'Sellers के लिए कोई app download नहीं',
      'Hindi/English voice-note support',
      'AI verified listings',
      'Khata और orders एक dashboard में',
    ],
    metrics: [
      { value: '<30 sec', label: 'Listing creation', body: 'Seller stock आधे मिनट से कम समय में structured inventory बन जाता है.' },
      { value: '0', label: 'App downloads', body: 'Sellers WhatsApp पर ही रहते हैं, नए app की जरूरत नहीं.' },
      { value: '3', label: 'Input modes', body: 'Text, voice, और image एक ही operating pipeline में जाते हैं.' },
      { value: '1', label: 'Unified dashboard', body: 'Orders, khata, verification, और insights एक workspace में मिलते हैं.' },
    ],
  },
};

const problemCards = [
  'Sellers lose time manually broadcasting stock every morning.',
  'Buyers have no trusted live view of local produce supply.',
  'Informal khata is difficult to track, reconcile, and follow up.',
  'Demand signals rarely reach farmers before produce value starts dropping.',
];

const features = [
  'WhatsApp-first listing creation',
  'Gemini-powered extraction',
  'AI produce photo quality check',
  'Google Maps pickup normalization',
  'Firestore-backed live marketplace',
  'WhatsApp order alerts',
  'Khata ledger',
  'Buyer demand signals',
  'Seller/FPO verification',
  'AI seller insights',
];

const personas = [
  {
    title: 'Farmer / small seller',
    body: 'Publishes daily stock over WhatsApp, accepts orders, and tracks khata without learning a new app.',
  },
  {
    title: 'FPO / aggregator',
    body: 'Manages pooled inventory, verified listings, and multiple buyer conversations with structured visibility.',
  },
  {
    title: 'Restaurant / kirana buyer',
    body: 'Discovers live produce lots, compares trusted suppliers, and places structured orders quickly.',
  },
  {
    title: 'Operator / admin',
    body: 'Monitors marketplace activity, order movement, buyer demand, and seller onboarding from one dashboard.',
  },
];

const impactCards = [
  'Reduces listing friction by turning informal WhatsApp messages into live inventory.',
  'Improves buyer trust with verified listings, pickup normalization, and AI quality signals.',
  'Digitizes khata so dues and collections stay visible beside day-to-day operations.',
  'Helps sellers respond faster to real buyer demand before stock goes stale.',
];

const steps = [
  'Seller sends WhatsApp text, voice note, or image.',
  'BolBazaar extracts product, quantity, price, quality, and pickup location.',
  'Buyer discovers a verified live listing and places an order.',
  'Seller accepts, stock updates, khata syncs, and AI insight is generated.',
];

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

export default function LandingPage({
  language,
  onLanguageChange,
  stats,
  onOpenLogin,
}: {
  language: AppLanguage;
  onLanguageChange: (language: AppLanguage) => void;
  stats: LandingStats;
  onOpenLogin: (role: 'buyer' | 'seller' | null) => void;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const copy = landingCopy[language];

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const elements = Array.from(document.querySelectorAll<HTMLElement>('[data-reveal]'));
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
          }
        }
      },
      { threshold: 0.12 },
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  const metrics = useMemo(
    () => [
      { ...copy.metrics[0] },
      { ...copy.metrics[1] },
      { ...copy.metrics[2] },
      { ...copy.metrics[3] },
    ],
    [copy.metrics],
  );

  return (
    <div className="bb-landing">
      <div className="bb-landing-inner">
        <div className={`bb-landing-nav ${scrolled ? 'is-scrolled' : ''}`}>
          <div className="bb-landing-nav-bar">
            <div className="bb-landing-brand">
              <span className="bb-landing-brand-mark">BB</span>
              <div className="bb-landing-brand-copy">
                <strong>BolBazaar</strong>
                <small>WhatsApp-first AI produce commerce</small>
              </div>
            </div>

            <div className="bb-landing-nav-links" aria-label="Landing sections">
              <button type="button" onClick={() => scrollToSection('problem')}>{copy.navProblem}</button>
              <button type="button" onClick={() => scrollToSection('solution')}>{copy.navSolution}</button>
              <button type="button" onClick={() => scrollToSection('how-it-works')}>{copy.navHow}</button>
              <button type="button" onClick={() => scrollToSection('impact')}>{copy.navImpact}</button>
              <button type="button" onClick={() => scrollToSection('architecture')}>{copy.navArchitecture}</button>
              <button type="button" onClick={() => scrollToSection('dashboard')}>{copy.navDashboard}</button>
            </div>

            <div className="bb-landing-nav-actions">
              <div className="language-switcher" aria-label="Language switcher">
                <button type="button" className={language === 'en' ? 'language-switch-active' : ''} onClick={() => onLanguageChange('en')}>EN</button>
                <button type="button" className={language === 'hi' ? 'language-switch-active' : ''} onClick={() => onLanguageChange('hi')}>HI</button>
              </div>
              <button type="button" className="ghost-button small" onClick={() => onOpenLogin(null)}>{copy.login}</button>
              <button type="button" className="primary-button small" onClick={() => onOpenLogin(null)}>{copy.ctaSecondary}</button>
              <button type="button" className="bb-landing-menu-button" aria-label="Open navigation" onClick={() => setMobileMenuOpen((value) => !value)}>
                <span />
              </button>
            </div>
          </div>

          {mobileMenuOpen ? (
            <div className="bb-landing-mobile-panel">
              <div className="bb-landing-mobile-links">
                <button type="button" onClick={() => { scrollToSection('problem'); setMobileMenuOpen(false); }}>{copy.navProblem}</button>
                <button type="button" onClick={() => { scrollToSection('solution'); setMobileMenuOpen(false); }}>{copy.navSolution}</button>
                <button type="button" onClick={() => { scrollToSection('how-it-works'); setMobileMenuOpen(false); }}>{copy.navHow}</button>
                <button type="button" onClick={() => { scrollToSection('impact'); setMobileMenuOpen(false); }}>{copy.navImpact}</button>
                <button type="button" onClick={() => { scrollToSection('architecture'); setMobileMenuOpen(false); }}>{copy.navArchitecture}</button>
                <button type="button" onClick={() => { scrollToSection('dashboard'); setMobileMenuOpen(false); }}>{copy.navDashboard}</button>
              </div>
              <div className="bb-landing-mobile-actions">
                <button type="button" className="ghost-button" onClick={() => onOpenLogin(null)}>{copy.login}</button>
                <button type="button" className="primary-button" onClick={() => onOpenLogin(null)}>{copy.ctaSecondary}</button>
              </div>
            </div>
          ) : null}
        </div>

        <section className="bb-landing-section bb-landing-hero" id="hero">
          <div className="bb-landing-hero-copy" data-reveal>
            <span className="eyebrow">{copy.badge}</span>
            <h1>{copy.title}</h1>
            <p>{copy.body}</p>
            <div className="bb-landing-hero-actions">
              <button type="button" className="primary-button" onClick={() => scrollToSection('how-it-works')}>
                {copy.ctaPrimary}
              </button>
              <button type="button" className="ghost-button" onClick={() => onOpenLogin(null)}>
                {copy.ctaSecondary}
              </button>
            </div>
            <div className="bb-landing-proof-row">
              {copy.proof.map((item) => (
                <span key={item} className="bb-landing-proof-chip">{item}</span>
              ))}
            </div>
          </div>

          <WhatsAppCommerceDemo language={language} />
        </section>

        <section className="bb-landing-metric-strip" data-reveal>
          {metrics.map((metric) => (
            <article key={metric.label} className="bb-landing-metric-card">
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <p>{metric.body}</p>
            </article>
          ))}
        </section>

        <section id="problem" className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">Problem</span>
            <h2>Fresh produce trade still runs on scattered calls, WhatsApp messages, and handwritten khata.</h2>
            <p>BolBazaar starts where the trade already happens, then adds structure, trust, and operational visibility.</p>
          </div>
          <div className="bb-landing-problem-grid">
            {problemCards.map((item, index) => (
              <article key={item} className="bb-landing-problem-card" data-reveal>
                <div className="bb-landing-card-icon">{index + 1}</div>
                <h3>{item}</h3>
              </article>
            ))}
          </div>
        </section>

        <section id="solution" className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">Solution</span>
            <h2>The WhatsApp-first AI operating system for fresh produce trade.</h2>
            <p>BolBazaar turns informal stock messages into digital listings, live buyer orders, khata records, demand signals, and seller insights.</p>
          </div>
          <div className="bb-landing-bento-grid">
            {features.map((feature, index) => (
              <article
                key={feature}
                className={`bb-landing-feature-card ${index === 0 || index === 3 || index === 8 ? 'bb-landing-bento-wide' : ''}`}
                data-reveal
              >
                <div className="bb-landing-card-icon">{String(index + 1).padStart(2, '0')}</div>
                <h3>{feature}</h3>
                <p>
                  {feature === 'WhatsApp-first listing creation' && 'Sellers stay in the channel they already use daily.'}
                  {feature === 'Gemini-powered extraction' && 'Product, price, quantity, and context are converted into structured inventory.'}
                  {feature === 'AI produce photo quality check' && 'Photos add freshness cues and trust signals for buyers.'}
                  {feature === 'Google Maps pickup normalization' && 'Pickup locations become consistent, searchable, and buyer-friendly.'}
                  {feature === 'Firestore-backed live marketplace' && 'Listings, orders, and khata stay synced across dashboard views.'}
                  {feature === 'WhatsApp order alerts' && 'Sellers get instant prompts to accept or reject new buyer demand.'}
                  {feature === 'Khata ledger' && 'Informal credit becomes trackable with structured dues and collections.'}
                  {feature === 'Buyer demand signals' && 'Search activity can now roll into pooled bulk-demand opportunities before demand is lost.'}
                  {feature === 'Seller/FPO verification' && 'Profiles become more trusted for B2B buyers and repeat trade.'}
                  {feature === 'AI seller insights' && 'Operational suggestions help sellers move stock and respond faster.'}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section id="how-it-works" className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">How It Works</span>
            <h2>One seller message becomes live marketplace activity.</h2>
            <p>BolBazaar keeps the entry point simple for sellers while building a structured workflow for the full marketplace.</p>
          </div>
          <div className="bb-landing-steps">
            {steps.map((step, index) => (
              <article key={step} className="bb-landing-step" data-reveal>
                <span className="bb-landing-step-index">{index + 1}</span>
                <h3>Step {index + 1}</h3>
                <p>{step}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">Personas</span>
            <h2>Built for the real people moving produce every day.</h2>
            <p>From farmers to FPOs to restaurants, each persona gets a lower-friction workflow than a generic marketplace.</p>
          </div>
          <div className="bb-landing-persona-grid">
            {personas.map((persona, index) => (
              <article key={persona.title} className="bb-landing-persona-card" data-reveal>
                <div className="bb-landing-card-icon">{index + 1}</div>
                <h3>{persona.title}</h3>
                <p>{persona.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="impact" className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">Impact</span>
            <h2>Designed to reduce friction, improve trust, and digitize the informal edges of produce trade.</h2>
            <p>BolBazaar works on WhatsApp first, which lowers adoption barriers while still giving buyers and operators a serious digital operating layer.</p>
          </div>
          <div className="bb-landing-impact-grid">
            {impactCards.map((item, index) => (
              <article key={item} className="bb-landing-impact-card" data-reveal>
                <div className="bb-landing-card-icon">{index + 1}</div>
                <h3>{item}</h3>
              </article>
            ))}
          </div>
        </section>

        <section id="architecture" className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">Google Architecture</span>
            <h2>A Google-powered commerce pipeline from WhatsApp input to live marketplace output.</h2>
            <p>Meta handles messaging, FastAPI orchestrates commerce logic, Gemini extracts structured signals, and Firestore keeps every workflow in sync.</p>
          </div>
          <ArchitectureFlow />
        </section>

        <section className="bb-landing-section">
          <div className="bb-landing-section-head" data-reveal>
            <span className="eyebrow">Comparison</span>
            <h2>BolBazaar gives local produce trade a better operating model than manual coordination.</h2>
            <p>It combines the low-friction familiarity of WhatsApp with the visibility and trust of a structured marketplace.</p>
          </div>
          <ComparisonTable />
        </section>

        <section id="dashboard" className="bb-landing-section">
          <div className="bb-landing-cta-panel" data-reveal>
            <div>
              <span className="eyebrow">See BolBazaar in action</span>
              <h2>Open the dashboard and move directly into the buyer or seller workflow.</h2>
              <p>
                Live listings: {stats.liveListings || 4} · Active sellers: {stats.activeSellers || 1} · Accepted orders: {stats.acceptedOrders || 1} · Alerts sent: {stats.alertsSent || 6}
              </p>
            </div>
            <div className="bb-landing-hero-actions">
              <button type="button" className="primary-button" onClick={() => onOpenLogin(null)}>
                Open dashboard
              </button>
              <button type="button" className="ghost-button" onClick={() => onOpenLogin('seller')}>
                Try demo flow
              </button>
            </div>
          </div>
        </section>

        <footer className="bb-landing-footer" data-reveal>
          <div className="bb-landing-footer-copy">
            <strong>BolBazaar</strong>
            <p>WhatsApp-first AI agri-commerce operating system for farmers, FPOs, aggregators, and B2B buyers. Built for Google Solution Challenge storytelling and real marketplace utility.</p>
          </div>
          <div className="bb-landing-footer-links">
            {navIds.map((id) => (
              <button key={id} type="button" onClick={() => scrollToSection(id)}>
                {id === 'problem' && copy.navProblem}
                {id === 'solution' && copy.navSolution}
                {id === 'how-it-works' && copy.navHow}
                {id === 'impact' && copy.navImpact}
                {id === 'architecture' && copy.navArchitecture}
                {id === 'dashboard' && copy.navDashboard}
              </button>
            ))}
          </div>
        </footer>
      </div>
    </div>
  );
}
