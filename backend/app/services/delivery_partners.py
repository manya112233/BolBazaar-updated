from __future__ import annotations

from app.schemas import DeliveryPartner


def seeded_delivery_partners() -> list[DeliveryPartner]:
    roster = [
        ('DP-1001', 'Ramesh Kumar', '+91 98765 43210', 'Tempo', 'DL01AB1234'),
        ('DP-1002', 'Suresh Yadav', '+91 98765 43211', 'Bike', 'DL05CQ4412'),
        ('DP-1003', 'Anil Sharma', '+91 98765 43212', 'Auto', 'HR26BM2188'),
        ('DP-1004', 'Vijay Singh', '+91 98765 43213', 'Tempo', 'UP16AN7410'),
        ('DP-1005', 'Manoj Gupta', '+91 98765 43214', 'Bike', 'RJ14SM5521'),
        ('DP-1006', 'Deepak Verma', '+91 98765 43215', 'Tempo', 'MH12TR9821'),
        ('DP-1007', 'Rakesh Jha', '+91 98765 43216', 'Auto', 'BR01KP2204'),
        ('DP-1008', 'Sanjay Patil', '+91 98765 43217', 'Bike', 'KA03HH1098'),
        ('DP-1009', 'Imran Khan', '+91 98765 43218', 'Tempo', 'GJ01MT4500'),
        ('DP-1010', 'Karthik R', '+91 98765 43219', 'Bike', 'KA05ZW7781'),
    ]
    return [
        DeliveryPartner(
            id=partner_id,
            name=name,
            phone=phone,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
        )
        for partner_id, name, phone, vehicle_type, vehicle_number in roster
    ]
