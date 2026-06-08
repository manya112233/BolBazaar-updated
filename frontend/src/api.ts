import type { AuthRole, BuyerDemandSearchRequest, BuyerDemandSearchResponse, CommitDemandPool, Delivery, DemandPoolOpportunity, DemandPoolResponse, DemandRequest, DemandRequestCreate, FulfillmentDeliveryStatus, Insight, Listing, Notification, Order, OtpRequestResponse, OtpVerifyResponse, SellerDashboard, SellerLedgerView, SellerProfile } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      throw new Error(parsed.detail || text || 'Request failed');
    } catch {
      throw new Error(text || 'Request failed');
    }
  }

  return response.json() as Promise<T>;
}

export async function resetDemo(): Promise<void> {
  await request('/api/demo/seed', { method: 'POST' });
}

export async function createDemoListing(): Promise<void> {
  await request('/api/demo/seller-message', {
    method: 'POST',
    body: JSON.stringify({
      seller_id: 'seller-demo-1',
      seller_name: 'Shakti FPO',
      message_text: 'Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup',
      image_url: 'https://images.unsplash.com/photo-1546470427-e6ac89a99c4d?auto=format&fit=crop&w=1200&q=80',
    }),
  });
}

export async function requestLoginOtp(payload: {
  role: AuthRole;
  phone_number: string;
}): Promise<OtpRequestResponse> {
  return request<OtpRequestResponse>('/api/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function verifyLoginOtp(payload: {
  request_id: string;
  otp_code: string;
}): Promise<OtpVerifyResponse> {
  return request<OtpVerifyResponse>('/api/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchListings(): Promise<Listing[]> {
  const data = await request<{ items: Listing[] }>('/api/listings');
  return data.items;
}

export async function placeOrder(payload: {
  listing_id: string;
  buyer_name: string;
  buyer_type: 'kirana' | 'restaurant' | 'canteen' | 'retailer';
  quantity_kg: number;
  pickup_time: string;
  phone?: string;
  delivery_mode?: 'pickup' | 'delivery';
  delivery_address?: string;
}): Promise<Order> {
  const data = await request<{ ok: boolean; order: Order }>('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data.order;
}

export async function respondToOrder(orderId: string, decision: 'accept' | 'reject'): Promise<Order> {
  const data = await request<{ ok: boolean; order: Order }>(`/api/orders/${orderId}/respond`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  });
  return data.order;
}

export async function fetchNotifications(): Promise<Notification[]> {
  const data = await request<{ items: Notification[] }>('/api/notifications');
  return data.items;
}

export async function fetchOrders(): Promise<Order[]> {
  const data = await request<{ items: Order[] }>('/api/orders');
  return data.items;
}

export async function fetchInsight(sellerId: string): Promise<Insight | null> {
  try {
    return await request<Insight>(`/api/sellers/${sellerId}/insight`);
  } catch {
    return null;
  }
}

export async function fetchSellers(): Promise<SellerProfile[]> {
  const data = await request<{ items: SellerProfile[] }>('/api/sellers');
  return data.items;
}

export async function fetchSellerDashboard(sellerId: string): Promise<SellerDashboard | null> {
  try {
    return await request<SellerDashboard>(`/api/sellers/${sellerId}/dashboard`);
  } catch {
    return null;
  }
}

export async function fetchSellerLedger(sellerId: string): Promise<SellerLedgerView | null> {
  try {
    return await request<SellerLedgerView>(`/api/sellers/${sellerId}/ledger`);
  } catch {
    return null;
  }
}

export async function fetchDemandPools(): Promise<DemandPoolOpportunity[]> {
  const data = await request<DemandPoolResponse>('/api/demand-pools');
  return data.items;
}

export async function recordLedgerPayment(payload: {
  seller_id: string;
  buyer_name: string;
  amount_paid: number;
  notes?: string;
}): Promise<SellerLedgerView | null> {
  const data = await request<{ ok: boolean; ledger: SellerLedgerView | null }>(`/api/sellers/${payload.seller_id}/ledger/payments`, {
    method: 'POST',
    body: JSON.stringify({
      buyer_name: payload.buyer_name,
      amount_paid: payload.amount_paid,
      notes: payload.notes,
    }),
  });
  return data.ledger;
}

export async function reportBuyerDemandSearch(payload: BuyerDemandSearchRequest): Promise<BuyerDemandSearchResponse> {
  return request<BuyerDemandSearchResponse>('/api/buyers/demand-search', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createDemandRequest(payload: DemandRequestCreate): Promise<DemandRequest> {
  const data = await request<{ ok: boolean; request: DemandRequest }>('/api/buyers/demand-requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data.request;
}

export async function fetchBuyerDemandRequests(buyerId: string): Promise<DemandRequest[]> {
  const data = await request<{ items: DemandRequest[] }>(`/api/buyers/${buyerId}/demand-requests`);
  return data.items;
}

export async function fetchCommitPools(sellerId?: string): Promise<CommitDemandPool[]> {
  const query = sellerId ? `?seller_id=${encodeURIComponent(sellerId)}` : '';
  const data = await request<{ items: CommitDemandPool[] }>(`/api/commit-pools${query}`);
  return data.items;
}

export async function commitToPool(poolId: string, payload: { seller_id: string; listing_id: string; price_per_kg?: number }): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/api/commit-pools/${poolId}/commit`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchDeliveries(filters?: { seller_id?: string; buyer_id?: string }): Promise<Delivery[]> {
  const params = new URLSearchParams();
  if (filters?.seller_id) params.set('seller_id', filters.seller_id);
  if (filters?.buyer_id) params.set('buyer_id', filters.buyer_id);
  const qs = params.toString();
  const data = await request<{ items: Delivery[] }>(`/api/deliveries${qs ? `?${qs}` : ''}`);
  return data.items;
}

export async function advanceDelivery(deliveryId: string, status: FulfillmentDeliveryStatus): Promise<Delivery> {
  const data = await request<{ ok: boolean; delivery: Delivery }>(`/api/deliveries/${deliveryId}/advance`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  });
  return data.delivery;
}
