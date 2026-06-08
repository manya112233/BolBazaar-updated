import StatusBadge from '../dashboard/StatusBadge';

const rows = [
  {
    approach: 'Manual WhatsApp groups',
    sellerEffort: 'High',
    buyerTrust: 'Low',
    khata: 'Manual',
    demand: 'Weak',
    channel: 'Unstructured chat',
    highlight: false,
  },
  {
    approach: 'Local broker / agent',
    sellerEffort: 'Medium',
    buyerTrust: 'Medium',
    khata: 'Offline',
    demand: 'Indirect',
    channel: 'Phone and broker',
    highlight: false,
  },
  {
    approach: 'Generic marketplace',
    sellerEffort: 'High onboarding',
    buyerTrust: 'Medium',
    khata: 'Not native',
    demand: 'Limited',
    channel: 'Separate app',
    highlight: false,
  },
  {
    approach: 'BolBazaar',
    sellerEffort: 'Low',
    buyerTrust: 'High',
    khata: 'Built in',
    demand: 'Live feedback',
    channel: 'WhatsApp + dashboard',
    highlight: true,
  },
];

export default function ComparisonTable() {
  return (
    <div className="bb-landing-comparison" data-reveal>
      <div className="bb-landing-comparison-wrap">
        <table className="bb-landing-comparison-table">
          <thead>
            <tr>
              <th>Approach</th>
              <th>Seller effort</th>
              <th>Buyer trust</th>
              <th>Khata tracking</th>
              <th>Demand feedback</th>
              <th>Channel</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.approach} className={row.highlight ? 'is-highlight' : ''}>
                <td>
                  <strong>{row.approach}</strong>
                  {row.highlight ? <div><StatusBadge label="Best fit" tone="success" /></div> : null}
                </td>
                <td>{row.sellerEffort}</td>
                <td>{row.buyerTrust}</td>
                <td>{row.khata}</td>
                <td>{row.demand}</td>
                <td>{row.channel}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
