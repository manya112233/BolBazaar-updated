from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from secrets import randbelow
from typing import Any

from app.config import get_settings
from app.schemas import AuthSession, OtpRequestIn, OtpRequestRecord, OtpRequestResponse, OtpVerifyIn, OtpVerifyResponse
from app.services.whatsapp_service import WhatsAppService


class AuthService:
    def __init__(self, store: Any) -> None:
        self.store = store
        self.settings = get_settings()
        self.whatsapp = WhatsAppService()

    def normalize_phone_number(self, phone_number: str) -> str:
        digits = re.sub(r'\D+', '', phone_number or '')
        if digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if len(digits) == 10:
            digits = f'91{digits}'
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('Enter a valid phone number')
        return digits

    def _otp_hash(self, request_id: str, otp_code: str) -> str:
        return hashlib.sha256(f'{request_id}:{otp_code}'.encode('utf-8')).hexdigest()

    def _is_dev_mode(self) -> bool:
        return self.settings.app_env.lower() != 'production'

    def request_otp(self, payload: OtpRequestIn) -> OtpRequestResponse:
        phone_number = self.normalize_phone_number(payload.phone_number)
        seller_profile = None

        if payload.role == 'seller':
            seller_profile = self.store.get_seller_profile(phone_number)
            if seller_profile is None:
                raise ValueError('Seller login is available only after the same phone number finishes WhatsApp onboarding.')

        otp_code = f'{randbelow(900000) + 100000:06d}'
        request_record = OtpRequestRecord(
            role=payload.role,
            phone_number=phone_number,
            otp_code_hash='',
            seller_id=seller_profile.seller_id if seller_profile else None,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        request_record.otp_code_hash = self._otp_hash(request_record.id, otp_code)

        note = None
        if payload.role == 'seller' and self.whatsapp.is_configured():
            whatsapp_result = self.whatsapp.send_text_message(
                to=phone_number,
                body=(
                    f'BolBazaar dashboard login OTP: {otp_code}. '
                    'This code is valid for 5 minutes. Use it only on the web dashboard.'
                ),
            )
            if whatsapp_result.get('sent'):
                request_record.delivery_method = 'whatsapp'
                request_record.delivery_status = 'sent'
                note = 'OTP sent to the seller number over WhatsApp.'
            else:
                request_record.delivery_method = 'demo_preview'
                request_record.delivery_status = 'preview'
                note = 'WhatsApp delivery was unavailable, so a demo OTP preview is active for this seller login.'
        else:
            request_record.delivery_method = 'demo_preview'
            request_record.delivery_status = 'preview'
            if payload.role == 'seller':
                note = 'Seller login stays mapped to the WhatsApp number already used for onboarding.'
            else:
                note = 'Buyer OTP is running in demo preview mode until an SMS provider is connected.'

        request_record.note = note
        self.store.save_otp_request(request_record)

        return OtpRequestResponse(
            request_id=request_record.id,
            role=request_record.role,
            phone_number=request_record.phone_number,
            expires_at=request_record.expires_at,
            delivery_method=request_record.delivery_method,
            delivery_status=request_record.delivery_status,
            note=note,
            demo_otp=otp_code if self._is_dev_mode() else None,
        )

    def verify_otp(self, payload: OtpVerifyIn) -> OtpVerifyResponse:
        request_record = self.store.get_otp_request(payload.request_id)
        if request_record is None:
            raise ValueError('OTP request not found. Request a fresh code.')

        if request_record.verified_at is not None:
            raise ValueError('This OTP has already been used. Request a fresh code.')

        if request_record.expires_at < datetime.utcnow():
            raise ValueError('OTP expired. Request a fresh code.')

        expected_hash = self._otp_hash(request_record.id, payload.otp_code.strip())
        if expected_hash != request_record.otp_code_hash:
            request_record.failed_attempts += 1
            self.store.save_otp_request(request_record)
            raise ValueError('Incorrect OTP. Check the code and try again.')

        request_record.verified_at = datetime.utcnow()
        self.store.save_otp_request(request_record)

        seller_profile = None
        if request_record.role == 'seller' and request_record.seller_id:
            seller_profile = self.store.get_seller_profile(request_record.seller_id)

        return OtpVerifyResponse(
            session=AuthSession(
                role=request_record.role,
                phone_number=request_record.phone_number,
                seller_id=seller_profile.seller_id if seller_profile else request_record.seller_id,
                seller_name=seller_profile.seller_name if seller_profile else None,
                store_name=seller_profile.store_name if seller_profile else None,
            )
        )
