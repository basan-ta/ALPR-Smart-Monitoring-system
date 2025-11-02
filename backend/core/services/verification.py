import time
from datetime import timedelta
from difflib import SequenceMatcher
from typing import Dict, Any, Optional, Tuple, List

from django.utils import timezone

from core.models import (
    PoliceVehicleRegistration,
    StolenVehicleReport,
    OwnerWatchlist,
    VerificationAttempt,
)


STOLEN_RECENT_DAYS = 30


def _ratio(a: Optional[str], b: Optional[str]) -> float:
    a = (a or '').strip().lower()
    b = (b or '').strip().lower()
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio() * 100.0


def _regional_cross_check(region_code: Optional[str], plate_number: Optional[str]) -> Tuple[bool, str]:
    """Stub regional cross-check; returns True and a note. Integrate real checks later."""
    if not region_code:
        return True, "No region provided; default pass"
    return True, f"Region {region_code} accepted (stub)"


def _recent_stolen_reports(reg: Optional[PoliceVehicleRegistration], plate_number: str) -> List[StolenVehicleReport]:
    since = timezone.now() - timedelta(days=STOLEN_RECENT_DAYS)
    qs = StolenVehicleReport.objects.filter(
        plate_number__iexact=plate_number,
        report_timestamp__gte=since,
        status=StolenVehicleReport.STATUS_OPEN,
    ).order_by('-report_timestamp')
    if reg:
        qs = qs | StolenVehicleReport.objects.filter(
            registration=reg,
            report_timestamp__gte=since,
            status=StolenVehicleReport.STATUS_OPEN,
        )
    return list(qs.distinct())


def verify_vehicle(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare incoming vehicle data against police records and return verification result.

    Input expects keys: plate_number (required), make, model, owner_name, region_code, timestamp.
    """
    t0 = time.perf_counter()
    now = timezone.now()

    plate = (input_payload.get('plate_number') or '').strip()
    make_in = input_payload.get('make')
    model_in = input_payload.get('model')
    owner_in = input_payload.get('owner_name')
    region_in = input_payload.get('region_code')

    result: Dict[str, Any] = {
        'match_status': False,
        'flag_category': 'normal',
        'confidence': 0.0,
        'verification_timestamp': now.isoformat(),
        'reference_case_numbers': [],
    }

    if not plate:
        result['message'] = 'Missing plate_number'
        result['response_time_ms'] = int((time.perf_counter() - t0) * 1000)
        VerificationAttempt.objects.create(
            input_payload=input_payload,
            match_status=False,
            flag_category=result['flag_category'],
            confidence=result['confidence'],
            verification_timestamp=now,
            response_time_ms=result['response_time_ms'],
            message=result['message'],
        )
        return result

    # Exact plate match in registration records
    reg = PoliceVehicleRegistration.objects.filter(plate_number__iexact=plate).first()

    plate_weight = 0.6
    make_weight = 0.2
    model_weight = 0.2
    base_conf = 0.0

    if reg:
        result['match_status'] = True
        base_conf += 100.0 * plate_weight

        make_score = _ratio(make_in, reg.make)
        model_score = _ratio(model_in, reg.model)
        owner_exact_match = bool(owner_in and reg.owner_name and owner_in.strip().lower() == reg.owner_name.strip().lower())
        owner_fuzzy = _ratio(owner_in, reg.owner_name)

        base_conf += make_score * make_weight
        base_conf += model_score * model_weight
        if owner_exact_match:
            base_conf = min(100.0, base_conf + 10.0)
        elif owner_fuzzy >= 80.0:
            base_conf = min(100.0, base_conf + 5.0)

        # Regional cross-check
        regional_ok, regional_note = _regional_cross_check(region_in, plate)
        if not regional_ok:
            base_conf = max(0.0, base_conf - 15.0)

        # Stolen report check (recent and open)
        stolen_reports = _recent_stolen_reports(reg, plate)
        watch_owner = reg.owner_name or owner_in
        watch_hit_qs = OwnerWatchlist.objects.filter(owner_name__iexact=watch_owner, active=True) if watch_owner else OwnerWatchlist.objects.none()
        watch_hit = watch_hit_qs.first()
        if stolen_reports:
            result['flag_category'] = 'stolen'
            result['reference_case_numbers'] = [s.case_number for s in stolen_reports]
            # Ensure high confidence if stolen
            base_conf = max(base_conf, 90.0)
        else:
            # Owner watchlist check
            
            if watch_hit:
                result['flag_category'] = 'suspicious'
                base_conf = max(base_conf, 75.0)
            else:
                # Partial matches can still be suspicious
                if make_score >= 70.0 or model_score >= 70.0 or owner_fuzzy >= 70.0:
                    # If plate matches but the rest is shaky, mark as suspicious at moderate confidence
                    if base_conf < 80.0:
                        result['flag_category'] = 'suspicious'
                else:
                    result['flag_category'] = 'normal'

        result['confidence'] = round(min(100.0, base_conf), 1)

        # Log attempt
        attempt = VerificationAttempt.objects.create(
            input_payload=input_payload,
            matched_registration=reg,
            matched_stolen_report=stolen_reports[0] if stolen_reports else None,
            matched_owner_watchlist=watch_hit,
            match_status=result['match_status'],
            flag_category=result['flag_category'],
            confidence=result['confidence'],
            verification_timestamp=now,
            response_time_ms=int((time.perf_counter() - t0) * 1000),
            reference_case_numbers=result['reference_case_numbers'],
            message=f"{regional_note}",
        )
        result['response_time_ms'] = attempt.response_time_ms
        return result

    # No registration match: decide suspicious vs normal based on owner watchlist and fuzzy inputs
    watch_hit = OwnerWatchlist.objects.filter(owner_name__iexact=owner_in, active=True).first() if owner_in else None
    if watch_hit:
        result['flag_category'] = 'suspicious'
        result['confidence'] = 60.0
        result['match_status'] = False
        msg = 'Owner on watchlist'
    else:
        result['flag_category'] = 'normal'
        result['confidence'] = 20.0
        result['match_status'] = False
        msg = 'No registration match'

    result['response_time_ms'] = int((time.perf_counter() - t0) * 1000)

    VerificationAttempt.objects.create(
        input_payload=input_payload,
        matched_owner_watchlist=watch_hit,
        match_status=result['match_status'],
        flag_category=result['flag_category'],
        confidence=result['confidence'],
        verification_timestamp=now,
        response_time_ms=result['response_time_ms'],
        reference_case_numbers=result['reference_case_numbers'],
        message=msg,
    )

    return result