# BolBazaar Demo Script

## Problem

Small farmers and local produce sellers still run supply through scattered WhatsApp chats, manual trust checks, and untracked delivery handoffs. Buyers cannot quickly see which lots are verified, sellers lose time chasing orders, and ops teams lack a clean delivery view.

## Solution

BolBazaar turns a seller's WhatsApp message into a structured marketplace listing, routes it through BolBazaar quality verification, shows graded trusted supply to buyers, and then manages the full delivery lifecycle through seller, ops, and buyer confirmations.

## Seller WhatsApp Flow

Start with the seller story.

1. Show the seller sending produce details on WhatsApp.
2. Explain that BolBazaar converts that message into a listing.
3. Point out that the new WhatsApp-created listing starts as `Quality Pending`.
4. If needed, mention seller WhatsApp commands:
   `DELIVERIES`, `STATUS`, `QUALITY`, `ACCEPT ORDER <id>`, `delivery <id> packed`, `delivery <id> handover`, `delivery <id> cancel`

## Ops Quality Verification

Open the Ops workspace.

1. Show the pending tomato lot in the quality queue.
2. Approve it and assign a grade.
3. Emphasize the label change to `BolBazaar Verified` and `Grade A`, `Grade B`, or `Grade C`.
4. Mention that rejected lots stay visible to ops but are blocked from buyer ordering.

## Buyer Verified Marketplace

Switch to the buyer view.

1. Show the verified badge and grade on live listings.
2. Point out that buyers can distinguish trusted graded supply from pending or rejected lots.
3. Place an order on a verified listing.

## Managed Delivery Flow

Continue the same order through fulfillment.

1. Seller accepts the order.
2. Seller manages fulfillment from WhatsApp with `DELIVERIES`.
3. Show the seller marking the lot `packed` and then `handover`.
4. Switch to ops and move the delivery through `Ready for Pickup`, `In Transit`, and `Delivered`.
5. Switch to buyer and confirm receipt.
6. Point out the final `Buyer Confirmed` state.

## Impact Metrics

Return to the Ops workspace.

1. Show `Smart Supply Chain Metrics`.
2. Highlight verified listings, pending quality checks, active deliveries, completed deliveries, and matched supply.
3. Explain that this creates visibility across quality, trust, and fulfillment in one flow.

## Closing Pitch

BolBazaar makes informal produce trade reliable without changing seller behavior. Sellers stay on WhatsApp, buyers get trusted graded supply, ops gets managed delivery visibility, and the whole system becomes a smart supply chain instead of a loose chat thread.
