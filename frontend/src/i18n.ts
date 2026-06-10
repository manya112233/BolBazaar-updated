export type Language = 'en' | 'hi';

const hi = {
  common: {
    close: '\u092c\u0902\u0926 \u0915\u0930\u0947\u0902',
    cancel: '\u0930\u0926\u094d\u0926 \u0915\u0930\u0947\u0902',
    logout: '\u0932\u0949\u0917\u0906\u0909\u091f',
    notifications: '\u0938\u0942\u091a\u0928\u093e\u090f\u0902',
    noNotifications: '\u0905\u092d\u0940 \u0915\u094b\u0908 \u0938\u0942\u091a\u0928\u093e \u0928\u0939\u0940\u0902 \u0939\u0948\u0964',
    markAllRead: '\u0938\u092d\u0940 \u092a\u0922\u093c\u0940 \u0917\u0908',
    markRead: '\u092a\u0922\u093c\u0940 \u0917\u0908',
    estimated: '\u0905\u0928\u0941\u092e\u093e\u0928\u093f\u0924',
    items: '\u0906\u0907\u091f\u092e',
  },
  dashboard: {
    buyerOs: '\u0916\u0930\u0940\u0926\u093e\u0930 OS',
    sellerOs: '\u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e OS',
    opsOs: '\u0911\u092a\u094d\u0938 OS',
    whatsAppFirst: '\u0935\u094d\u0939\u093e\u091f\u094d\u0938\u090f\u092a-\u092b\u0930\u094d\u0938\u094d\u091f',
    liveOps: '\u0932\u093e\u0907\u0935 \u092e\u093e\u0930\u094d\u0915\u0947\u091f\u092a\u094d\u0932\u0947\u0938 \u0911\u092a\u094d\u0938',
    whatsAppBody: '\u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917, \u0916\u093e\u0924\u093e, \u0921\u093f\u092e\u093e\u0902\u0921 \u0905\u0932\u0930\u094d\u091f \u0914\u0930 \u0935\u0947\u0930\u093f\u092b\u093f\u0915\u0947\u0936\u0928 \u0909\u0938\u0940 \u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e \u092b\u094b\u0928 \u0935\u0930\u094d\u0915\u092b\u094d\u0932\u094b \u0938\u0947 \u091c\u0941\u0921\u093c\u0947 \u0930\u0939\u0924\u0947 \u0939\u0948\u0902\u0964',
    searchWorkspace: '\u0935\u0930\u094d\u0915\u0938\u094d\u092a\u0947\u0938 \u0916\u094b\u091c\u0947\u0902',
    sellerSession: '\u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e \u0938\u0924\u094d\u0930',
    buyerSession: '\u0916\u0930\u0940\u0926\u093e\u0930 \u0938\u0924\u094d\u0930',
    opsSession: '\u0911\u092a\u094d\u0938 \u0938\u0924\u094d\u0930',
    marketplace: '\u092c\u093e\u095b\u093e\u0930',
    orders: '\u0911\u0930\u094d\u0921\u0930',
    sellers: '\u092d\u0930\u094b\u0938\u0947\u092e\u0902\u0926 \u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e',
    demand: '\u092e\u093e\u0902\u0917 \u0938\u0902\u0915\u0947\u0924',
    overview: '\u0913\u0935\u0930\u0935\u094d\u092f\u0942',
    listings: '\u0932\u093e\u0907\u0935 \u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917',
    ledger: '\u0916\u093e\u0924\u093e \u0932\u0947\u091c\u0930',
    insights: 'AI \u0938\u0941\u091d\u093e\u0935',
    profile: '\u0935\u0947\u0930\u093f\u092b\u093f\u0915\u0947\u0936\u0928/\u092a\u094d\u0930\u094b\u092b\u093e\u0907\u0932',
    opsVerification: '\u0911\u092a\u094d\u0938 \u0935\u0947\u0930\u093f\u092b\u093f\u0915\u0947\u0936\u0928',
    managedDelivery: '\u092e\u0948\u0928\u0947\u091c\u094d\u0921 \u0921\u093f\u0932\u093f\u0935\u0930\u0940',
    smartSupplyChain: '\u0938\u094d\u092e\u093e\u0930\u094d\u091f \u0938\u092a\u094d\u0932\u093e\u0908 \u091a\u0947\u0928',
    sellerDashboard: '\u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e \u0921\u0948\u0936\u092c\u094b\u0930\u094d\u0921',
    buyerDashboard: '\u0916\u0930\u0940\u0926\u093e\u0930 \u0921\u0948\u0936\u092c\u094b\u0930\u094d\u0921',
    opsDashboard: '\u0911\u092a\u094d\u0938 \u0921\u0948\u0936\u092c\u094b\u0930\u094d\u0921',
    sellerNetwork: 'BolBazaar Seller Network',
    buyerNetwork: 'BolBazaar Buyer Network',
    opsNetwork: 'BolBazaar Ops Network',
    toggleSidebar: '\u0938\u093e\u0907\u0921\u092c\u093e\u0930 \u091f\u0949\u0917\u0932 \u0915\u0930\u0947\u0902',
    closeNavigation: '\u0928\u0947\u0935\u093f\u0917\u0947\u0936\u0928 \u092c\u0902\u0926 \u0915\u0930\u0947\u0902',
    openNavigation: '\u0928\u0947\u0935\u093f\u0917\u0947\u0936\u0928 \u0916\u094b\u0932\u0947\u0902',
    languageSwitcher: '\u092d\u093e\u0937\u093e \u091a\u0941\u0928\u0947\u0902',
  },
  orderModal: {
    title: '{product} \u0915\u093e \u0911\u0930\u094d\u0921\u0930',
    buyerName: '\u0916\u0930\u0940\u0926\u093e\u0930 \u0915\u093e \u0928\u093e\u092e',
    buyerType: '\u0916\u0930\u0940\u0926\u093e\u0930 \u092a\u094d\u0930\u0915\u093e\u0930',
    quantity: '\u092e\u093e\u0924\u094d\u0930\u093e (\u0915\u093f\u0932\u094b)',
    pickupTime: '\u092a\u093f\u0915\u0905\u092a \u0938\u092e\u092f',
    phone: '\u092b\u094b\u0928',
    deliveryMode: '\u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u092e\u094b\u0921',
    deliveryAddress: '\u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u092a\u0924\u093e',
    unitPrice: '\u0930\u0947\u091f',
    subtotal: '\u092e\u093e\u0932 \u0915\u093e \u0915\u0941\u0932',
    deliveryFee: '\u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u0936\u0941\u0932\u094d\u0915',
    totalEstimate: '\u0915\u0941\u0932 \u0905\u0928\u0941\u092e\u093e\u0928',
    estimating: '\u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u0915\u093e \u0905\u0928\u0941\u092e\u093e\u0928 \u0932\u0917\u093e\u092f\u093e \u091c\u093e \u0930\u0939\u093e \u0939\u0948...',
    deliveryPending: '\u092a\u0924\u0947 \u0915\u0940 \u092a\u0941\u0937\u094d\u091f\u093f \u0915\u0947 \u092c\u093e\u0926 \u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u0936\u0941\u0932\u094d\u0915 \u092c\u0924\u093e\u092f\u093e \u091c\u093e\u090f\u0917\u093e\u0964',
    confirm: '\u0911\u0930\u094d\u0921\u0930 \u0915\u0930\u0947\u0902',
    placing: '\u092d\u0947\u091c\u093e \u091c\u093e \u0930\u0939\u093e \u0939\u0948...',
    qualityGrade: '\u0915\u094d\u0935\u093e\u0932\u093f\u091f\u0940 \u0917\u094d\u0930\u0947\u0921',
    verifiedFromPhoto: '\u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e \u0915\u0940 \u092b\u094b\u091f\u094b \u0938\u0947 \u0938\u0924\u094d\u092f\u093e\u092a\u093f\u0924\u0964',
    pickup: '\u092a\u093f\u0915\u0905\u092a',
    delivery: '\u0921\u093f\u0932\u093f\u0935\u0930\u0940',
  },
  notifications: {
    title: '\u0938\u0942\u091a\u0928\u093e \u0915\u0947\u0902\u0926\u094d\u0930',
  },
  sellerWorkspace: {
    dashboard: '\u0935\u093f\u0915\u094d\u0930\u0947\u0924\u093e \u0921\u0948\u0936\u092c\u094b\u0930\u094d\u0921',
    demandPools: '\u0921\u093f\u092e\u093e\u0902\u0921 \u092a\u0942\u0932',
    managedDelivery: '\u092e\u0948\u0928\u0947\u091c\u094d\u0921 \u0921\u093f\u0932\u093f\u0935\u0930\u0940',
  },
  buyerWorkspace: {
    browseMarketplace: '\u092e\u093e\u0930\u094d\u0915\u0947\u091f\u092a\u094d\u0932\u0947\u0938 \u0926\u0947\u0916\u0947\u0902',
    postDemand: '\u0921\u093f\u092e\u093e\u0902\u0921 \u092a\u094b\u0938\u094d\u091f \u0915\u0930\u0947\u0902',
    myDemandAndDelivery: '\u092e\u0947\u0930\u0940 \u0921\u093f\u092e\u093e\u0902\u0921 \u0914\u0930 \u0921\u093f\u0932\u093f\u0935\u0930\u0940',
  },
  demandPoolBoard: {
    title: '\u0921\u093f\u092e\u093e\u0902\u0921 \u092a\u0942\u0932',
    none: '\u0905\u092d\u0940 \u0915\u094b\u0908 \u090f\u0915\u094d\u091f\u093f\u0935 \u092a\u0942\u0932 \u0928\u0939\u0940\u0902',
    totalDemand: '\u0915\u0941\u0932 \u092e\u093e\u0902\u0917',
    buyers: '\u0916\u0930\u0940\u0926\u093e\u0930',
    mandiModal: '\u092e\u0902\u0921\u0940 \u092e\u094b\u0921\u0932',
    suggestedPrice: '\u0938\u0941\u091d\u093e\u0935\u093f\u0924 \u0930\u0947\u091f',
    chooseListing: '\u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917 \u091a\u0941\u0928\u0947\u0902',
    price: '\u0930\u0947\u091f',
    committing: '\u092d\u0947\u091c\u093e \u091c\u093e \u0930\u0939\u093e \u0939\u0948...',
    commitSupply: '\u0938\u092a\u094d\u0932\u093e\u0908 \u0915\u092e\u093f\u091f \u0915\u0930\u0947\u0902',
    noLiveListings: '\u0932\u093e\u0907\u0935 \u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917 \u0928\u0939\u0940\u0902',
    fulfillPool: '\u092f\u0939 \u092a\u0942\u0932 \u0932\u0947\u0902',
  },
  deliveryBoard: {
    none: '\u0905\u092d\u0940 \u0915\u094b\u0908 \u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u0928\u0939\u0940\u0902',
    title: '\u092e\u0948\u0928\u0947\u091c\u094d\u0921 \u0921\u093f\u0932\u093f\u0935\u0930\u0940',
    buyer: '\u0916\u0930\u0940\u0926\u093e\u0930',
    deliveryFee: '\u0921\u093f\u0932\u093f\u0935\u0930\u0940 \u0936\u0941\u0932\u094d\u0915',
    distance: '\u0926\u0942\u0930\u0940',
    updating: '\u0905\u092a\u0921\u0947\u091f \u0939\u094b \u0930\u0939\u093e \u0939\u0948...',
    advanceTo: '\u0905\u0917\u0932\u093e \u091a\u0930\u0923',
  },
} as const;

const translations = {
  en: {
    common: {
      close: 'Close',
      cancel: 'Cancel',
      logout: 'Logout',
      notifications: 'Notifications',
      noNotifications: 'No notifications yet.',
      markAllRead: 'Mark all as read',
      markRead: 'Mark read',
      estimated: 'Estimated',
      items: 'items',
    },
    dashboard: {
      buyerOs: 'Buyer OS',
      sellerOs: 'Seller OS',
      opsOs: 'Ops OS',
      whatsAppFirst: 'WhatsApp-first',
      liveOps: 'Live marketplace operations',
      whatsAppBody: 'Listings, khata, demand alerts, and verification stay mapped to the same seller phone workflow.',
      searchWorkspace: 'Search workspace',
      sellerSession: 'Seller session',
      buyerSession: 'Buyer session',
      opsSession: 'Ops session',
      marketplace: 'Marketplace',
      orders: 'Orders',
      sellers: 'Trusted Sellers',
      demand: 'Demand Signals',
      overview: 'Overview',
      listings: 'Live Listings',
      ledger: 'Khata Ledger',
      insights: 'AI Insights',
      profile: 'Verification/Profile',
      opsVerification: 'Ops Verification',
      managedDelivery: 'Managed Delivery',
      smartSupplyChain: 'Smart Supply Chain',
      sellerDashboard: 'Seller dashboard',
      buyerDashboard: 'Buyer dashboard',
      opsDashboard: 'Ops dashboard',
      sellerNetwork: 'BolBazaar Seller Network',
      buyerNetwork: 'BolBazaar Buyer Network',
      opsNetwork: 'BolBazaar Ops Network',
      toggleSidebar: 'Toggle sidebar',
      closeNavigation: 'Close navigation',
      openNavigation: 'Open navigation',
      languageSwitcher: 'Language switcher',
    },
    orderModal: {
      title: 'Order {product}',
      buyerName: 'Buyer name',
      buyerType: 'Buyer type',
      quantity: 'Quantity (kg)',
      pickupTime: 'Pickup time',
      phone: 'Phone',
      deliveryMode: 'Delivery mode',
      deliveryAddress: 'Delivery address',
      unitPrice: 'Unit price',
      subtotal: 'Produce subtotal',
      deliveryFee: 'Delivery fee',
      totalEstimate: 'Total estimate',
      estimating: 'Estimating delivery...',
      deliveryPending: 'Delivery fee will be confirmed after address validation.',
      confirm: 'Confirm order',
      placing: 'Placing...',
      qualityGrade: 'Quality grade',
      verifiedFromPhoto: "Verified from the seller's produce photo.",
      pickup: 'Pickup',
      delivery: 'Delivery',
    },
    notifications: {
      title: 'Notification Center',
    },
    sellerWorkspace: {
      dashboard: 'Seller Dashboard',
      demandPools: 'Demand Pools',
      managedDelivery: 'Managed Delivery',
    },
    buyerWorkspace: {
      browseMarketplace: 'Browse Marketplace',
      postDemand: 'Post Demand',
      myDemandAndDelivery: 'My Demand & Delivery',
    },
    demandPoolBoard: {
      title: 'Demand Pools',
      none: 'No active pools right now',
      totalDemand: 'Total demand',
      buyers: 'Buyers',
      mandiModal: 'Mandi modal',
      suggestedPrice: 'Suggested price',
      chooseListing: 'Choose a listing',
      price: 'Price',
      committing: 'Committing...',
      commitSupply: 'Commit supply',
      noLiveListings: 'No live listings to commit',
      fulfillPool: 'Fulfill this pool',
    },
    deliveryBoard: {
      none: 'No deliveries yet',
      title: 'Managed Delivery',
      buyer: 'Buyer',
      deliveryFee: 'Delivery fee',
      distance: 'Distance',
      updating: 'Updating...',
      advanceTo: 'Advance to',
    },
  },
  hi,
} as const;

export function t(language: Language, key: string, params?: Record<string, string | number>): string {
  const parts = key.split('.');
  let value: unknown = translations[language];
  for (const part of parts) {
    if (value && typeof value === 'object' && part in (value as Record<string, unknown>)) {
      value = (value as Record<string, unknown>)[part];
    } else {
      value = undefined;
      break;
    }
  }
  if (typeof value !== 'string') {
    value = parts.reduce<unknown>((acc, part) => {
      if (acc && typeof acc === 'object' && part in (acc as Record<string, unknown>)) {
        return (acc as Record<string, unknown>)[part];
      }
      return undefined;
    }, translations.en);
  }
  const template = typeof value === 'string' ? value : key;
  return template.replace(/\{(\w+)\}/g, (_, token) => String(params?.[token] ?? `{${token}}`));
}
