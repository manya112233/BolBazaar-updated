import { useEffect, useState } from 'react';
import type { Listing } from '../types';
import type { AppLanguage } from '../App';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const GENERIC_PRODUCE_FALLBACK = `${API_BASE}/media/default-produce/generic-produce.jpg`;
const GENERIC_VEGETABLES_FALLBACK = `${API_BASE}/media/default-produce/generic-vegetables.jpg`;
const GENERIC_FRUITS_FALLBACK = `${API_BASE}/media/default-produce/generic-fruits.jpg`;
const TOMATO_FALLBACK = `${API_BASE}/media/default-produce/tomato.jpg`;
const POTATO_FALLBACK = `${API_BASE}/media/default-produce/potato.jpg`;

const PRODUCT_IMAGE_FALLBACKS: Array<{ keywords: string[]; imageUrl: string }> = [
  { keywords: ['tomato', 'tamatar'], imageUrl: TOMATO_FALLBACK },
  { keywords: ['potato', 'aloo'], imageUrl: POTATO_FALLBACK },
  { keywords: ['onion', 'pyaz'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/2/25/Onion_on_White.JPG' },
  { keywords: ['carrot', 'gajar'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/0/05/CarrotDiversityLg.jpg' },
  { keywords: ['cabbage', 'patta gobhi'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Cabbage_and_cross_section_on_white.jpg' },
  { keywords: ['cauliflower', 'phool gobhi'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Cauliflower.JPG' },
  { keywords: ['spinach', 'palak'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/0/01/Cropped_image_of_spinach_leaves.jpg' },
  { keywords: ['leafy', 'greens', 'saag', 'methi', 'lettuce'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/0/01/Cropped_image_of_spinach_leaves.jpg' },
  { keywords: ['banana', 'kela'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/8/8a/Banana-Single.jpg' },
  { keywords: ['mango', 'aam'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/9/90/Hapus_Mango.jpg' },
  { keywords: ['apple', 'seb'], imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/1/15/Red_Apple.jpg' },
];

const GENERIC_IMAGE_SUFFIXES = [
  '/media/default-produce/generic-produce.jpg',
  '/media/default-produce/generic-vegetables.jpg',
  '/media/default-produce/generic-fruits.jpg',
];

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
    whatsappListing: 'WhatsApp à¤²à¤¿à¤¸à¥à¤Ÿà¤¿à¤‚à¤—',
    demoListing: 'à¤¡à¥‡à¤®à¥‹ à¤²à¤¿à¤¸à¥à¤Ÿà¤¿à¤‚à¤—',
    geoVerified: 'à¤²à¥‹à¤•à¥‡à¤¶à¤¨ à¤¸à¤¤à¥à¤¯à¤¾à¤ªà¤¿à¤¤',
    aiPhotoChecked: 'AI à¤«à¥‹à¤Ÿà¥‹ à¤œà¤¾à¤‚à¤šà¥€ à¤—à¤ˆ',
    aiVisualFreshness: 'AI à¤¦à¥ƒà¤¶à¥à¤¯ à¤¤à¤¾à¤œà¤—à¥€',
    qualityNote: 'à¤—à¥à¤£à¤µà¤¤à¥à¤¤à¤¾ à¤¨à¥‹à¤Ÿ',
    available: 'à¤‰à¤ªà¤²à¤¬à¥à¤§',
    pickup: 'à¤ªà¤¿à¤•à¤…à¤ª',
    seller: 'à¤µà¤¿à¤•à¥à¤°à¥‡à¤¤à¤¾',
    grade: 'à¤—à¥à¤°à¥‡à¤¡',
    standard: 'à¤¸à¤¾à¤®à¤¾à¤¨à¥à¤¯',
    placeOrder: 'à¤‘à¤°à¥à¤¡à¤° à¤•à¤°à¥‡à¤‚',
    maps: 'Google Maps à¤ªà¤° à¤¦à¥‡à¤–à¥‡à¤‚',
    currency: 'à¤°à¥',
    kg: 'à¤•à¤¿à¤²à¥‹',
  },
};

const gradeLabels: Record<AppLanguage, Record<string, string>> = {
  en: {
    premium: 'Premium',
    standard: 'Standard',
    economy: 'Economy',
  },
  hi: {
    premium: 'à¤ªà¥à¤°à¥€à¤®à¤¿à¤¯à¤®',
    standard: 'à¤¸à¤¾à¤®à¤¾à¤¨à¥à¤¯',
    economy: 'à¤‡à¤•à¥‰à¤¨à¤®à¥€',
  },
};

const productLabels: Record<string, string> = {
  tomato: 'à¤Ÿà¤®à¤¾à¤Ÿà¤°',
  potato: 'à¤†à¤²à¥‚',
  onion: 'à¤ªà¥à¤¯à¤¾à¤œ',
  carrot: 'à¤—à¤¾à¤œà¤°',
  cabbage: 'à¤ªà¤¤à¥à¤¤à¤¾ à¤—à¥‹à¤­à¥€',
  cauliflower: 'à¤«à¥‚à¤² à¤—à¥‹à¤­à¥€',
  spinach: 'à¤ªà¤¾à¤²à¤•',
  greens: 'à¤¹à¤°à¥€ à¤¸à¤¬à¥à¤œà¤¿à¤¯à¤¾à¤‚',
  banana: 'à¤•à¥‡à¤²à¤¾',
  mango: 'à¤†à¤®',
  apple: 'à¤¸à¥‡à¤¬',
};

const signalLabels: Record<string, string> = {
  'consistent color': 'à¤à¤•à¤¸à¤®à¤¾à¤¨ à¤°à¤‚à¤—',
  'firm appearance': 'à¤®à¤œà¤¬à¥‚à¤¤ à¤¦à¤¿à¤–à¤¾à¤µà¤Ÿ',
  'minimal blemishes': 'à¤•à¤® à¤¦à¤¾à¤—',
  'bright color': 'à¤šà¤®à¤•à¤¦à¤¾à¤° à¤°à¤‚à¤—',
  'minimal visible blemishes': 'à¤•à¤® à¤¦à¤¿à¤–à¤¾à¤ˆ à¤¦à¥‡à¤¨à¥‡ à¤µà¤¾à¤²à¥‡ à¤¦à¤¾à¤—',
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

function qualityStateLabel(listing: Listing): string {
  if (listing.quality_status === 'approved' && listing.verified_by_bolbazaar) {
    return `BolBazaar Verified${listing.quality_grade && ['A', 'B', 'C'].includes(listing.quality_grade) ? ` Grade ${listing.quality_grade}` : ''}`;
  }
  if (listing.quality_status === 'rejected') {
    return 'Rejected by Ops';
  }
  return 'Quality Pending';
}

function localizeSignal(signal: string, language: AppLanguage): string {
  if (language === 'en') return signal;
  return signalLabels[signal.toLowerCase()] || signal;
}

function listingDescription(listing: Listing, productName: string, language: AppLanguage): string | null | undefined {
  if (language === 'en') return listing.description;
  return `${productName} ${listing.seller_name} à¤¸à¥‡, à¤‰à¤¸à¥€ à¤¦à¤¿à¤¨ à¤ªà¤¿à¤•à¤…à¤ª à¤•à¥‡ à¤²à¤¿à¤ ${listing.pickup_location} à¤ªà¤° à¤‰à¤ªà¤²à¤¬à¥à¤§ à¤¹à¥ˆà¥¤`;
}

function qualitySummary(listing: Listing, productName: string, language: AppLanguage): string | null | undefined {
  if (language === 'en') return listing.quality_summary;
  if (!listing.quality_summary) return listing.quality_summary;
  const signals = listing.quality_signals.slice(0, 3).map((signal) => localizeSignal(signal, language));
  if (signals.length > 0) {
    return `${productName} à¤•à¥€ à¤—à¥à¤£à¤µà¤¤à¥à¤¤à¤¾ à¤…à¤šà¥à¤›à¥€ à¤¦à¤¿à¤– à¤°à¤¹à¥€ à¤¹à¥ˆ: ${signals.join(', ')}à¥¤`;
  }
  return `${productName} à¤•à¥€ AI à¤«à¥‹à¤Ÿà¥‹ à¤œà¤¾à¤‚à¤š à¤ªà¥‚à¤°à¥€ à¤¹à¥‹ à¤—à¤ˆ à¤¹à¥ˆà¥¤`;
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

function resolveListingImage(listing: Listing): string {
  const rawImageUrl = listing.image_url?.trim();
  const normalizedProduct = listing.product_name.toLowerCase();
  const matchedProductImage = PRODUCT_IMAGE_FALLBACKS.find(({ keywords }) =>
    keywords.some((keyword) => normalizedProduct.includes(keyword))
  )?.imageUrl;

  const isGenericCatalogImage = !!rawImageUrl && GENERIC_IMAGE_SUFFIXES.some((suffix) => rawImageUrl.endsWith(suffix));
  if (rawImageUrl && !isGenericCatalogImage) {
    return rawImageUrl;
  }
  if (matchedProductImage) {
    return matchedProductImage;
  }
  if (listing.category === 'vegetables') {
    return GENERIC_VEGETABLES_FALLBACK;
  }
  if (listing.category === 'fruits') {
    return GENERIC_FRUITS_FALLBACK;
  }
  return GENERIC_PRODUCE_FALLBACK;
}

function productVisualConfig(productName: string) {
  const normalized = productName.toLowerCase();
  const match = Object.entries(FALLBACK_COLORS).find(([key]) => normalized.includes(key));
  return match ? match[1] : { ...DEFAULT_FALLBACK, label: productName || DEFAULT_FALLBACK.label };
}

function productFallbackImage(productName: string): string {
  const config = productVisualConfig(productName);
  const label = config.label.replace(/[<>&"]/g, '');

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" role="img" aria-label="${label}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="${config.bg}"/>
      <stop offset="100%" stop-color="${config.fill}" stop-opacity="0.15"/>
    </linearGradient>
  </defs>
  <rect width="640" height="480" fill="url(#bg)"/>
  <g transform="translate(320,215)" stroke="${config.stroke}" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.45">
    <path d="M0 42 C-32 24 -42 -8 -28 -38 C-14 -60 14 -60 28 -38 C42 -8 32 24 0 42Z"/>
    <line x1="0" y1="42" x2="0" y2="-38"/>
    <path d="M0 6 C-14 2 -24 -8 -20 -22"/>
    <path d="M0 6 C14 2 24 -8 20 -22"/>
  </g>
  <text x="320" y="298" text-anchor="middle" font-family="Georgia, serif" font-size="21" font-weight="700" fill="${config.stroke}" opacity="0.52">${label}</text>
</svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
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
  const copy = listingCopy[language];
  const productName = localizeProductName(listing.product_name, language);
  const description = listingDescription(listing, productName, language);
  const visibleQualitySummary = qualitySummary(listing, productName, language);
  const orderDisabled = listing.quality_status === 'rejected';
  const resolvedImage = resolveListingImage(listing);
  const fallbackImage = productFallbackImage(listing.product_name);
  const [imageSrc, setImageSrc] = useState(resolvedImage);
  useEffect(() => {
    setImageSrc(resolvedImage);
  }, [resolvedImage]);

  return (
    <article className="card listing-card">
      <div className="listing-image-wrap">
        <img
          src={imageSrc}
          alt={productName}
          className="listing-image"
          onError={() => {
            setImageSrc((current) => current === fallbackImage ? current : fallbackImage);
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
              <span className={`mini-pill ${listing.quality_status === 'approved' ? 'success-pill' : listing.quality_status === 'rejected' ? 'danger-pill' : 'neutral-pill'}`}>
                {qualityStateLabel(listing)}
              </span>
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
              {listing.quality_status === 'approved' && ['A', 'B', 'C'].includes(listing.quality_grade)
                ? `Grade ${listing.quality_grade}`
                : localizeGrade(listing.quality_grade, language)}
              {listing.quality_confidence != null ? ` (${Math.round(listing.quality_confidence * 100)}%)` : listing.quality_score != null ? ` (${listing.quality_score}/100)` : ''}
            </strong>
          </div>
        </div>
        {listing.quality_notes && (
          <div className="quality-note">
            <strong>{listing.verified_by_bolbazaar ? 'Ops Verification' : copy.qualityNote}</strong>
            <p>{listing.quality_notes}</p>
          </div>
        )}
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
          <button className="primary-button" disabled={orderDisabled} onClick={() => onOrder(listing)}>
            {orderDisabled ? 'Ordering Blocked' : copy.placeOrder}
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
