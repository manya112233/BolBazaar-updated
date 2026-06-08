const architectureNodes = [
  'WhatsApp Seller',
  'Meta WhatsApp Cloud API',
  'FastAPI on Cloud Run',
  'Gemini Extraction & Insights',
  'Google Speech-to-Text',
  'Google Maps Geocoding',
  'Cloud Firestore',
  'React Dashboard',
  'Buyer Marketplace',
  'WhatsApp Seller Alert',
];

export default function ArchitectureFlow() {
  return (
    <div className="bb-landing-architecture" data-reveal>
      <div className="bb-landing-architecture-grid">
        {architectureNodes.map((node, index) => (
          <div key={node} className="bb-landing-architecture-node">
            <span className="bb-landing-architecture-index">{String(index + 1).padStart(2, '0')}</span>
            <strong>{node}</strong>
            {index < architectureNodes.length - 1 ? <span className="bb-landing-architecture-link" aria-hidden="true" /> : null}
          </div>
        ))}
      </div>

      <div className="bb-landing-architecture-legend">
        <span><i className="bb-legend-dot bb-legend-ai" /> AI</span>
        <span><i className="bb-legend-dot bb-legend-storage" /> Storage</span>
        <span><i className="bb-legend-dot bb-legend-comms" /> Communication</span>
        <span><i className="bb-legend-dot bb-legend-frontend" /> Frontend</span>
      </div>
    </div>
  );
}
