import type { Listing } from '../types';
import type { AppLanguage } from '../App';

const FALLBACK_COLORS: Record<string, { bg: string; fill: string; stroke: string; label: string }> = {
  tomato: { bg: '#fff0e8', fill: '#d9342b', stroke: '#8f1f1a', label: 'Tomato' },
  onion: { bg: '#f7edf8', fill: '#b06ab3', stroke: '#734075', label: 'Onion' },
  potato: { bg: '#f6ead8', fill: '#b98242', stroke: '#765028', label: 'Potato' },
  carrot: { bg: '#fff1dc', fill: '#f47a20', stroke: '#a84912', label: 'Carrot' },
  cabbage: { bg: '#edf8e6', fill: '#7fba63', stroke: '#4a7a39', label: 'Cabbage' },
  cauliflower: { bg: '#f5f2e8', fill: '#efe5c7', stroke: '#8f865d', label: 'Cauliflower' },
  spinach: { bg: '#e8f6e7', fill: '#2f8f46', stroke: '#1d5f30', label: 'Spinach' },
  greens: { bg: '#e8f6e7', fill: '#2f8f46', stroke: '#1d5f30', label: 'Greens' },
  banana: { bg: '#fff6cf', fill: '#efca32', stroke: '#a78412', label: 'Banana' },
  mango: { bg: '#fff2d7', fill: '#f6a829', stroke: '#a85f12', label: 'Mango' },
  apple: { bg: '#ffe9e6', fill: '#cf2f2f', stroke: '#8b1f1f', label: 'Apple' },
};

const DEFAULT_FALLBACK = { bg: '#eef7ef', fill: '#42a568', stroke: '#1f6f3e', label: 'Produce' };

function formatGrade(grade: string): string {
  if (!grade) return 'Standard';
  return grade.charAt(0).toUpperCase() + grade.slice(1);
}

const listingCopy = {
  en: {
    whatsappListing: 'WhatsApp listing',
    demoListing: 'Demo listing',
    geoVerified: 'Geo-verified',
    aiPhotoChecked: 'AI photo checked',
    aiVisualFreshness: 'AI visual freshness',
    qualityNote: 'Quality note',
    available: 'Available',
    pickup: 'Pickup',
    seller: 'Seller',
    grade: 'Grade',
    standard: 'Standard',
    placeOrder: 'Place order',
    maps: 'View on Google Maps',
    currency: 'Rs',
    kg: 'kg',
  },
  hi: {
    whatsappListing: 'WhatsApp लिस्टिंग',
    demoListing: 'डेमो लिस्टिंग',
    geoVerified: 'लोकेशन सत्यापित',
    aiPhotoChecked: 'AI फोटो जांची गई',
    aiVisualFreshness: 'AI दृश्य ताजगी',
    qualityNote: 'गुणवत्ता नोट',
    available: 'उपलब्ध',
    pickup: 'पिकअप',
    seller: 'विक्रेता',
    grade: 'ग्रेड',
    standard: 'सामान्य',
    placeOrder: 'ऑर्डर करें',
    maps: 'Google Maps पर देखें',
    currency: 'रु',
    kg: 'किलो',
  },
};

const gradeLabels: Record<AppLanguage, Record<string, string>> = {
  en: {
    premium: 'Premium',
    standard: 'Standard',
    economy: 'Economy',
  },
  hi: {
    premium: 'प्रीमियम',
    standard: 'सामान्य',
    economy: 'इकॉनमी',
  },
};

const productLabels: Record<string, string> = {
  tomato: 'टमाटर',
  potato: 'आलू',
  onion: 'प्याज',
  carrot: 'गाजर',
  cabbage: 'पत्ता गोभी',
  cauliflower: 'फूल गोभी',
  spinach: 'पालक',
  greens: 'हरी सब्जियां',
  banana: 'केला',
  mango: 'आम',
  apple: 'सेब',
};

const signalLabels: Record<string, string> = {
  'consistent color': 'एकसमान रंग',
  'firm appearance': 'मजबूत दिखावट',
  'minimal blemishes': 'कम दाग',
  'bright color': 'चमकदार रंग',
  'minimal visible blemishes': 'कम दिखाई देने वाले दाग',
};

function localizeProductName(productName: string, language: AppLanguage): string {
  if (language === 'en') return productName;
  const normalized = productName.toLowerCase();
  const match = Object.entries(productLabels).find(([key]) => normalized.includes(key));
  return match ? match[1] : productName;
}

function localizeGrade(grade: string, language: AppLanguage): string {
  if (!grade) return listingCopy[language].standard;
  return gradeLabels[language][grade.toLowerCase()] || formatGrade(grade);
}

function localizeSignal(signal: string, language: AppLanguage): string {
  if (language === 'en') return signal;
  return signalLabels[signal.toLowerCase()] || signal;
}

function listingDescription(listing: Listing, productName: string, language: AppLanguage): string | null | undefined {
  if (language === 'en') return listing.description;
  return `${productName} ${listing.seller_name} से, उसी दिन पिकअप के लिए ${listing.pickup_location} पर उपलब्ध है।`;
}

function qualitySummary(listing: Listing, productName: string, language: AppLanguage): string | null | undefined {
  if (language === 'en') return listing.quality_summary;
  if (!listing.quality_summary) return listing.quality_summary;
  const signals = listing.quality_signals.slice(0, 3).map((signal) => localizeSignal(signal, language));
  if (signals.length > 0) {
    return `${productName} की गुणवत्ता अच्छी दिख रही है: ${signals.join(', ')}।`;
  }
  return `${productName} की AI फोटो जांच पूरी हो गई है।`;
}

function productVisualConfig(productName: string) {
  const normalized = productName.toLowerCase();
  const match = Object.entries(FALLBACK_COLORS).find(([key]) => normalized.includes(key));
  return match ? match[1] : { ...DEFAULT_FALLBACK, label: productName || DEFAULT_FALLBACK.label };
}

function productFallbackImage(productName: string): string {
  const config = productVisualConfig(productName);
  const label = config.label.replace(/[<>&"]/g, '');
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 520" role="img" aria-label="${label}">
      <defs>
        <radialGradient id="glow" cx="50%" cy="42%" r="62%">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="58%" stop-color="${config.bg}"/>
          <stop offset="100%" stop-color="#dcebdd"/>
        </radialGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="22" stdDeviation="18" flood-color="#123522" flood-opacity="0.18"/>
        </filter>
      </defs>
      <rect width="640" height="520" fill="url(#glow)"/>
      <ellipse cx="320" cy="418" rx="178" ry="35" fill="#123522" opacity="0.12"/>
      <g filter="url(#shadow)">
        <circle cx="260" cy="270" r="92" fill="${config.fill}" stroke="${config.stroke}" stroke-width="10"/>
        <circle cx="374" cy="264" r="108" fill="${config.fill}" stroke="${config.stroke}" stroke-width="10"/>
        <circle cx="325" cy="340" r="98" fill="${config.fill}" stroke="${config.stroke}" stroke-width="10"/>
        <path d="M290 163c27 20 55 18 84 0-13 41-36 66-84 0Z" fill="#2d8a47"/>
        <path d="M319 180c-4-35 6-63 31-84" fill="none" stroke="#2d8a47" stroke-width="14" stroke-linecap="round"/>
        <circle cx="232" cy="234" r="18" fill="#fff" opacity="0.35"/>
        <circle cx="338" cy="219" r="24" fill="#fff" opacity="0.28"/>
      </g>
      <text x="320" y="472" text-anchor="middle" font-family="Manrope, Arial, sans-serif" font-size="34" font-weight="800" fill="#123522">${label}</text>
    </svg>
  `;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

function mapUrl(listing: Listing): string | null {
  if (listing.latitude != null && listing.longitude != null) {
    return `https://www.google.com/maps/search/?api=1&query=${listing.latitude},${listing.longitude}`;
  }
  if (listing.pickup_location) {
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(listing.pickup_location)}`;
  }
  return null;
}

export default function ListingCard({
  listing,
  language,
  onOrder,
}: {
  listing: Listing;
  language: AppLanguage;
  onOrder: (listing: Listing) => void;
}) {
  const mapsHref = mapUrl(listing);
  const isAiVisualGrade = listing.quality_assessment_source === 'ai_visual';
  const fallbackImage = productFallbackImage(listing.product_name);
  const copy = listingCopy[language];
  const productName = localizeProductName(listing.product_name, language);
  const description = listingDescription(listing, productName, language);
  const visibleQualitySummary = qualitySummary(listing, productName, language);

  return (
    <article className="card listing-card">
      <div className="listing-image-wrap">
        <img
          src={listing.image_url || fallbackImage}
          alt={productName}
          className="listing-image"
          onError={(event) => {
            if (event.currentTarget.src !== fallbackImage) {
              event.currentTarget.src = fallbackImage;
            }
          }}
        />
        <span className="badge">{isAiVisualGrade ? copy.aiPhotoChecked : listing.freshness_label}</span>
      </div>
      <div className="listing-body">
        <div className="listing-title-row">
          <div>
            <h3>{productName}</h3>
            <div className="pill-row">
              <span className="mini-pill">{listing.source_channel === 'whatsapp' ? copy.whatsappListing : copy.demoListing}</span>
              {listing.latitude != null && listing.longitude != null && <span className="mini-pill">{copy.geoVerified}</span>}
              {isAiVisualGrade && <span className="mini-pill success-pill">{copy.aiPhotoChecked}</span>}
            </div>
          </div>
          <span className="price">{copy.currency} {listing.price_per_kg}/{copy.kg}</span>
        </div>
        <p className="muted">{description}</p>
        {visibleQualitySummary && (
          <div className="quality-note">
            <strong>{isAiVisualGrade ? copy.aiVisualFreshness : copy.qualityNote}</strong>
            <p>{visibleQualitySummary}</p>
          </div>
        )}
        <div className="details-grid">
          <div>
            <span className="label">{copy.available}</span>
            <strong>{listing.available_kg} {copy.kg}</strong>
          </div>
          <div>
            <span className="label">{copy.pickup}</span>
            <strong>{listing.pickup_location}</strong>
          </div>
          <div>
            <span className="label">{copy.seller}</span>
            <strong>{listing.seller_name}</strong>
          </div>
          <div>
            <span className="label">{copy.grade}</span>
            <strong>
              {localizeGrade(listing.quality_grade, language)}
              {listing.quality_score != null ? ` (${listing.quality_score}/100)` : ''}
            </strong>
          </div>
        </div>
        {listing.quality_signals.length > 0 && (
          <div className="pill-row">
            {listing.quality_signals.slice(0, 3).map((signal) => (
              <span key={signal} className="mini-pill neutral-pill">
                {localizeSignal(signal, language)}
              </span>
            ))}
          </div>
        )}
        <div className="action-cluster">
          <button className="primary-button" onClick={() => onOrder(listing)}>
            {copy.placeOrder}
          </button>
          {mapsHref && (
            <a className="ghost-button inline-link-button" href={mapsHref} target="_blank" rel="noreferrer">
              {copy.maps}
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
