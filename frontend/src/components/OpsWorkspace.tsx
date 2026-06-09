import DeliveryBoard from './DeliveryBoard';
import DataTable from './dashboard/DataTable';
import KpiCard from './dashboard/KpiCard';
import StatusBadge from './dashboard/StatusBadge';
import type { FulfillmentDeliveryStatus, Listing, ListingQualityGrade, ListingQualityStatus, OpsDashboardResponse } from '../types';

export default function OpsWorkspace({
  sectionId,
  dashboard,
  onUpdateQuality,
  onAdvanceDelivery,
}: {
  sectionId: string;
  dashboard: OpsDashboardResponse | null;
  onUpdateQuality: (listingId: string, payload: {
    status: ListingQualityStatus;
    grade?: ListingQualityGrade | null;
    notes?: string;
    checked_by: string;
    confidence?: number | null;
    proof_images?: string[];
  }) => Promise<void>;
  onAdvanceDelivery: (deliveryId: string, nextStatus: FulfillmentDeliveryStatus) => Promise<void>;
}) {
  if (!dashboard) {
    return <div className="bb-empty-state"><strong>Ops dashboard loading</strong><p>Supply-chain metrics and queues will appear here.</p></div>;
  }

  const metrics = dashboard.metrics;

  return (
    <div className="bb-page">
      <section className="bb-page-copy">
        <div>
          <h1>BolBazaar Ops</h1>
          <p>Quality verification, trusted graded supply, managed delivery, and smart supply-chain impact in one workspace.</p>
        </div>
        <div className="bb-page-chips">
          <StatusBadge label="Ops Verification" tone="success" />
          <StatusBadge label="Managed Delivery" tone="info" />
          <StatusBadge label="Smart Supply Chain" tone="warning" />
        </div>
      </section>

      <section className="bb-kpi-grid">
        <div className="bb-panel-head" style={{ gridColumn: '1 / -1', paddingBottom: 0 }}>
          <div>
            <h3>Smart Supply Chain Metrics</h3>
            <p>Judge-friendly snapshot of verified supply, delivery execution, and marketplace impact.</p>
          </div>
        </div>
        <KpiCard label="Total listings" value={String(metrics.total_listings)} meta="Supply created" tone="info" />
        <KpiCard label="Verified listings" value={String(metrics.verified_listings)} meta="Trusted graded produce" tone="success" />
        <KpiCard label="Pending quality" value={String(metrics.pending_quality_checks)} meta="Needs ops review" tone="warning" />
        <KpiCard label="Rejected lots" value={String(metrics.rejected_listings)} meta="Blocked from buyer ordering" tone="danger" />
        <KpiCard label="Active deliveries" value={String(metrics.active_deliveries)} meta="Managed fulfillment" tone="info" />
        <KpiCard label="Completed deliveries" value={String(metrics.completed_deliveries)} meta="Delivered supply" tone="success" />
        <KpiCard label="Demand pools matched" value={String(metrics.demand_pools_matched)} meta="Pooled buyer demand converted" tone="warning" />
        <KpiCard label="Supply matched" value={`${metrics.estimated_supply_matched_kg} kg`} meta="Estimated wastage reduced" tone="neutral" />
      </section>

      {(sectionId === 'quality' || sectionId === 'metrics') && (
        <section className="bb-panel">
          <div className="bb-panel-head">
            <div>
              <h3>Pending quality checks</h3>
              <p>Approve, reject, and grade lots before buyers see verified supply.</p>
            </div>
          </div>
          <DataTable
            columns={[
              { key: 'produce', label: 'Produce', render: (row: Listing) => <strong>{row.product_name}</strong> },
              { key: 'seller', label: 'Seller', render: (row) => row.seller_name },
              { key: 'qty', label: 'Quantity', align: 'right', render: (row) => `${row.available_kg} kg` },
              { key: 'price', label: 'Price', align: 'right', render: (row) => `Rs ${row.price_per_kg}/kg` },
              { key: 'pickup', label: 'Pickup', render: (row) => row.pickup_location },
              { key: 'state', label: 'State', render: () => <StatusBadge label="Quality Pending" tone="warning" /> },
              {
                key: 'actions',
                label: 'Actions',
                render: (row) => (
                  <div className="action-row">
                    <button className="primary-button small" onClick={() => void onUpdateQuality(row.id, { status: 'approved', grade: 'A', notes: 'Ops verified for buyer marketplace.', checked_by: 'ops-demo-1', confidence: 0.91 })}>Approve A</button>
                    <button className="ghost-button small" onClick={() => void onUpdateQuality(row.id, { status: 'approved', grade: 'B', notes: 'Ops approved with normal trade grade.', checked_by: 'ops-demo-1', confidence: 0.82 })}>Approve B</button>
                    <button className="ghost-button small" onClick={() => void onUpdateQuality(row.id, { status: 'rejected', notes: 'Ops rejected after quality inspection.', checked_by: 'ops-demo-1', confidence: 0.74 })}>Reject</button>
                  </div>
                ),
              },
            ]}
            rows={dashboard.pending_quality_checks}
            emptyTitle="No pending lots"
            emptyBody="All current marketplace listings have already been reviewed."
          />
        </section>
      )}

      {sectionId === 'deliveries' && (
        <DeliveryBoard
          deliveries={dashboard.active_deliveries}
          onAdvance={onAdvanceDelivery}
          role="ops"
        />
      )}

      {(sectionId === 'metrics' || sectionId === 'quality') && (
        <div className="bb-two-column">
          <section className="bb-panel">
            <div className="bb-panel-head">
              <div>
                <h3>Verified listings</h3>
                <p>Trusted produce buyers can order with confidence.</p>
              </div>
            </div>
            <DataTable
              columns={[
                { key: 'produce', label: 'Produce', render: (row: Listing) => <strong>{row.product_name}</strong> },
                { key: 'grade', label: 'Grade', render: (row) => <StatusBadge label={`Grade ${row.quality_grade}`} tone="success" /> },
                { key: 'seller', label: 'Seller', render: (row) => row.seller_name },
                { key: 'confidence', label: 'Confidence', align: 'right', render: (row) => row.quality_confidence != null ? `${Math.round(row.quality_confidence * 100)}%` : '-' },
              ]}
              rows={dashboard.verified_listings}
              emptyTitle="No verified lots"
              emptyBody="Approve a pending lot to create trusted supply."
            />
          </section>

          <section className="bb-panel">
            <div className="bb-panel-head">
              <div>
                <h3>Rejected listings</h3>
                <p>Rejected lots stay visible for ops review but blocked from trusted ordering.</p>
              </div>
            </div>
            <DataTable
              columns={[
                { key: 'produce', label: 'Produce', render: (row: Listing) => <strong>{row.product_name}</strong> },
                { key: 'seller', label: 'Seller', render: (row) => row.seller_name },
                { key: 'note', label: 'Quality note', render: (row) => row.quality_notes || 'Rejected by ops' },
              ]}
              rows={dashboard.rejected_listings}
              emptyTitle="No rejected lots"
              emptyBody="Rejected supply lots will appear here for the demo."
            />
          </section>
        </div>
      )}
    </div>
  );
}
