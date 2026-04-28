# ruff: noqa: E501
"""OK.com property publishing automation.

Supports the AE-style property publish flow for "For Rent" and "For Sale".
The implementation intentionally drives the visible web UI so that cookies,
upload handling, and client-side validation match a real user session.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import selectors as sel
from .client.base import BaseClient
from .errors import OKElementNotFound, OKNotLoggedIn
from .human import medium_delay, short_delay

logger = logging.getLogger("ok-publish-property")

MODE_CATEGORY_IDS = {
    "rent": 5001,
    "sale": 5002,
}

PROPERTY_TYPE_LABELS = {
    "apartment": "Apartment",
    "villa": "Villa",
    "townhouse": "Townhouse",
    "land": "Land",
    "other": "Other",
}

RENTAL_TYPE_LABELS = {
    "entire": "Entire unit",
    "entire-unit": "Entire unit",
    "shared": "Shared unit",
    "shared-unit": "Shared unit",
}

FLOOR_LEVEL_LABELS = {
    "one": "One Level",
    "one-level": "One Level",
    "single": "One Level",
    "multi": "Multi Level",
    "multi-level": "Multi Level",
}

RENT_PERIOD_LABELS = {
    "day": "per day",
    "week": "per week",
    "month": "per month",
    "quarter": "per quarter",
    "year": "per year",
    "per-day": "per day",
    "per-week": "per week",
    "per-month": "per month",
    "per-quarter": "per quarter",
    "per-year": "per year",
}


@dataclass
class PublishPropertyRequest:
    mode: str
    property_type: str
    title: str
    description: str
    subdomain: str
    price: str | int | float | None = None
    location: str | None = None
    images: list[str] = field(default_factory=list)
    floor_plans: list[str] = field(default_factory=list)
    lang: str = "en"
    rental_type: str | None = None
    rent_period: str | None = None
    bedrooms: str | int | None = None
    bathrooms: str | int | None = None
    car_spaces: str | int | None = None
    floor_level: str | None = None
    floor: str | int | None = None
    area_size: str | int | float | None = None
    phone: str | None = None
    whatsapp: str | None = None
    unit_features: list[str] = field(default_factory=list)
    amenities: list[str] = field(default_factory=list)
    property_services: list[str] = field(default_factory=list)
    submit: bool = False
    save_draft: bool = False


@dataclass
class PublishPropertyResult:
    success: bool
    action: str
    mode: str
    property_type: str
    url: str
    submitted: bool = False
    draft_saved: bool = False
    submit_state: str | None = None
    warnings: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)


def publish_property(client: BaseClient, req: PublishPropertyRequest) -> PublishPropertyResult:
    """Fill and optionally submit the property publishing form."""
    mode = _normalize_mode(req.mode)
    property_type = _normalize_property_type(req.property_type)
    if mode == "rent" and property_type == "land":
        raise ValueError("For Rent does not support property_type=land")
    warnings: list[str] = []

    _navigate_to_property_form(client, req.subdomain, req.lang, mode)
    _require_logged_in(client, req.subdomain)

    category_label = PROPERTY_TYPE_LABELS[property_type]
    _click_option(client, category_label, group_title="Category", required=True)
    medium_delay()

    if req.images:
        _upload_files(client, "Pictures", req.images, warnings)
    if req.floor_plans:
        _upload_files(client, "Floor plan", req.floor_plans, warnings)

    if mode == "rent":
        rental_label = RENTAL_TYPE_LABELS.get(_norm(req.rental_type or "entire"))
        if rental_label:
            _click_option(client, rental_label, item_label="Rental type", required=False)
        else:
            warnings.append(f"Unsupported rental type: {req.rental_type}")

    if req.bedrooms is not None:
        _click_option(client, str(req.bedrooms), item_label="Beds", required=False)
    if req.bathrooms is not None:
        _click_option(client, str(req.bathrooms), item_label="Bathrooms", required=False)
    if mode == "sale" and req.car_spaces is not None:
        _click_option(client, _car_spaces_label(req.car_spaces), item_label="Car Spaces", required=False)

    if req.floor_level:
        floor_label = FLOOR_LEVEL_LABELS.get(_norm(req.floor_level))
        if floor_label:
            _click_option(client, floor_label, item_label="Floor", required=False)
        else:
            warnings.append(f"Unsupported floor level: {req.floor_level}")
    if req.floor is not None:
        _fill_floor(client, str(req.floor), warnings)

    if req.area_size is not None:
        _fill_text_field(client, "Area Size", _num_to_text(req.area_size), required=False)

    _select_many(client, "Unit Feature", req.unit_features, warnings)
    _select_many(client, "Amenities", req.amenities, warnings)
    _select_many(client, "Property Services", req.property_services, warnings)

    if req.price is not None:
        _fill_text_field(client, "Price", _num_to_text(req.price), required=False)
    if mode == "rent" and req.rent_period:
        period_label = RENT_PERIOD_LABELS.get(_norm(req.rent_period), req.rent_period)
        if not _select_affix_dropdown(client, "Price", period_label):
            warnings.append(f"Could not select rent period: {req.rent_period}")

    if req.phone:
        _fill_text_field(client, "Phone number", _local_phone(req.phone, req.subdomain), required=False)
    if req.whatsapp:
        _fill_text_field(client, "WhatsApp", _local_phone(req.whatsapp, req.subdomain), required=False)

    _fill_text_field(client, "Title", req.title, required=True)
    _fill_text_field(client, "Description", req.description, required=True)
    if req.location:
        _fill_location(client, req.location, warnings)

    action = "filled"
    submitted = False
    draft_saved = False
    submit_state: str | None = None

    if req.save_draft:
        action = "draft"
        draft_saved = _click_draft(client)
        medium_delay()
    elif req.submit:
        action = "submitted"
        submitted = _click_submit(client)
        submit_state = _wait_for_submit_result(client) if submitted else "not-clicked"

    validation_errors = _extract_validation_errors(client)
    success = (submitted or draft_saved or action == "filled") and not validation_errors
    if req.submit:
        success = submitted and submit_state == "navigated" and not validation_errors
        if submitted and submit_state == "timeout":
            warnings.append("Submit clicked but the page stayed on the publish form")
    return PublishPropertyResult(
        success=success,
        action=action,
        mode=mode,
        property_type=property_type,
        url=client.get_url() or "",
        submitted=submitted,
        draft_saved=draft_saved,
        submit_state=submit_state,
        warnings=warnings,
        validation_errors=validation_errors,
    )


def _navigate_to_property_form(client: BaseClient, subdomain: str, lang: str, mode: str) -> None:
    subdomain = subdomain.strip().lower()
    category_id = MODE_CATEGORY_IDS[mode]
    trace_id = int(time.time() * 1000)
    url = (
        f"https://{subdomain}pub.ok.com/biz/{lang}/publish/property"
        f"?categoryId={category_id}&traceId={trace_id}"
    )
    client.navigate(url)
    client.wait_dom_stable(timeout=15000)
    medium_delay()
    if "login" in (client.get_url() or "").lower():
        raise OKNotLoggedIn(f"Not logged in on {subdomain}.ok.com")


def _require_logged_in(client: BaseClient, subdomain: str) -> None:
    if not client.has_element(sel.USER_AVATAR):
        raise OKNotLoggedIn(f"Not logged in on {subdomain}.ok.com")


def _upload_files(
    client: BaseClient,
    label: str,
    files: list[str],
    warnings: list[str],
) -> None:
    paths = [_abs_existing_file(p) for p in files]
    selector = _mark_upload_input(client, label)
    if not selector:
        warnings.append(f"Upload input not found: {label}")
        return

    client.send_command("set_file_input", {"selector": selector, "files": paths})
    short_delay()
    client.evaluate(
        f"""(() => {{
            const input = document.querySelector({selector!r});
            if (input) {{
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }})()"""
    )
    medium_delay()


def _mark_upload_input(client: BaseClient, label: str) -> str | None:
    marker = f"ok-upload-{int(time.time() * 1000)}-{_norm(label)}"
    result = client.evaluate(
        f"""(() => {{
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            const label = {label!r}.toLowerCase();
            const items = [...document.querySelectorAll('.dy-form-item')];
            for (const item of items) {{
                const text = clean(item.querySelector('.dy-form-item-label, [class*="FormItemLabel"]')?.textContent || '');
                if (!text.toLowerCase().startsWith(label)) continue;
                const input = item.querySelector('input[type="file"]');
                if (!input) return null;
                input.setAttribute('data-ok-upload-target', {marker!r});
                return `[data-ok-upload-target="${{input.getAttribute('data-ok-upload-target')}}"]`;
            }}
            return null;
        }})()"""
    )
    return result


def _click_option(
    client: BaseClient,
    option: str,
    *,
    group_title: str | None = None,
    item_label: str | None = None,
    required: bool = False,
) -> bool:
    result = client.evaluate(
        f"""(() => {{
            const want = {_js(option)};
            const groupTitle = {_js(group_title)};
            const itemLabel = {_js(item_label)};
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            const visible = (el) => {{
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }};
            let scope = document;
            if (groupTitle) {{
                const groups = [...document.querySelectorAll('.dy-group')];
                scope = groups.find((g) => {{
                    const title = clean(g.querySelector('.dy-group-title, [class*="GroupTitle"], [class*="group-title"]')?.textContent || '');
                    return title.toLowerCase() === groupTitle.toLowerCase();
                }}) || document;
            }}
            if (itemLabel) {{
                const items = [...document.querySelectorAll('.dy-form-item')];
                scope = items.find((item) => {{
                    const label = clean(item.querySelector('.dy-form-item-label, [class*="FormItemLabel"]')?.textContent || '');
                    return label.toLowerCase() === itemLabel.toLowerCase();
                }}) || document;
            }}
            const nodes = [...scope.querySelectorAll('button, a, div, span, label')]
                .filter(visible)
                .filter((el) => clean(el.textContent).toLowerCase() === want.toLowerCase())
                .sort((a, b) => clean(a.textContent).length - clean(b.textContent).length);
            const node = nodes[0];
            if (!node) return false;
            let target = node;
            for (let cur = node; cur && cur !== scope.parentElement; cur = cur.parentElement) {{
                const cls = (cur.className && cur.className.toString ? cur.className.toString() : '');
                if (
                    cur.tagName === 'BUTTON' || cur.tagName === 'A' ||
                    /radio|Radio|pill|tag|option|dropdown-item|button-content/i.test(cls)
                ) {{
                    target = cur;
                    break;
                }}
            }}
            target.scrollIntoView({{ block: 'center' }});
            target.click();
            return true;
        }})()"""
    )
    if result:
        short_delay()
        return True
    if required:
        raise OKElementNotFound(f"Could not select option: {option}")
    return False


def _fill_text_field(
    client: BaseClient,
    label: str,
    value: str,
    *,
    required: bool = False,
) -> bool:
    result = client.evaluate(
        f"""(() => {{
            const label = {label!r};
            const value = {value!r};
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            const items = [...document.querySelectorAll('.dy-form-item')];
            const item = items.find((it) => {{
                const text = clean(it.querySelector('.dy-form-item-label, [class*="FormItemLabel"]')?.textContent || '');
                return text.toLowerCase() === label.toLowerCase();
            }});
            if (!item) return {{ ok: false, reason: 'item' }};
            const el = item.querySelector('textarea, input:not([type="file"])');
            if (!el) return {{ ok: false, reason: 'input' }};
            el.scrollIntoView({{ block: 'center' }});
            el.focus();
            const proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
            if (setter) setter.call(el, value);
            else el.value = value;
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            el.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true, key: 'a' }}));
            el.blur();
            return {{ ok: true, value: el.value }};
        }})()"""
    ) or {}
    if result.get("ok"):
        short_delay()
        return True
    if required:
        raise OKElementNotFound(f"Could not fill field {label}: {result.get('reason')}")
    return False


def _fill_floor(client: BaseClient, value: str, warnings: list[str]) -> None:
    result = client.evaluate(
        f"""(() => {{
            const value = {value!r};
            const inputs = [...document.querySelectorAll('.dy-form-item input:not([type="file"])')];
            const input = inputs.find((el) => el.placeholder === '0');
            if (!input) return false;
            input.scrollIntoView({{ block: 'center' }});
            input.focus();
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
            if (setter) setter.call(input, value);
            else input.value = value;
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            input.blur();
            return true;
        }})()"""
    )
    if not result:
        warnings.append("Could not fill floor number")
    else:
        short_delay()


def _fill_location(client: BaseClient, value: str, warnings: list[str]) -> None:
    selector = client.evaluate(
        """(() => {
            const input = [...document.querySelectorAll('input')]
                .find((el) => el.placeholder === 'Set the location for your post.');
            if (!input) return null;
            input.setAttribute('data-ok-location-target', '1');
            input.scrollIntoView({ block: 'center' });
            input.focus();
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
            if (setter) setter.call(input, '');
            else input.value = '';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            return '[data-ok-location-target="1"]';
        })()"""
    )
    if not selector:
        warnings.append("Could not fill location")
        return

    client.click_element(selector)
    short_delay()
    client.send_command("debugger_type_text", {"text": value, "delay": 35})
    medium_delay()

    location_script = """(async () => {
            const wanted = __LOCATION_VALUE__.trim().toLowerCase();
            const tokens = wanted.split(/\\s+/).filter(Boolean);
            const visible = (el) => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            };
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const getItems = () => [...document.querySelectorAll(
                '.res-list-group-item, .pac-container .pac-item, .pac-item'
            )].filter(visible);
            const pickMatchingItem = (items) => items.find((item) => {
                const text = clean(item.textContent).toLowerCase();
                return text.includes(wanted) || tokens.every((token) => text.includes(token));
            });

            let items = [];
            let item = null;
            const deadline = Date.now() + 5000;
            while (Date.now() < deadline) {
                items = getItems();
                item = pickMatchingItem(items);
                if (item) break;
                await sleep(250);
            }

            if (item) {
                item.scrollIntoView({ block: 'center' });
                const rect = item.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || item;
                const base = { bubbles: true, cancelable: true, view: window, clientX: x, clientY: y, button: 0 };
                const pointer = (type, buttons) => new PointerEvent(type, { ...base, buttons, pointerId: 1, pointerType: 'mouse', isPrimary: true });
                const mouse = (type, buttons) => new MouseEvent(type, { ...base, buttons });
                target.dispatchEvent(pointer('pointerover', 0));
                target.dispatchEvent(mouse('mouseover', 0));
                target.dispatchEvent(pointer('pointermove', 0));
                target.dispatchEvent(mouse('mousemove', 0));
                target.dispatchEvent(pointer('pointerdown', 1));
                target.dispatchEvent(mouse('mousedown', 1));
                target.dispatchEvent(pointer('pointerup', 0));
                target.dispatchEvent(mouse('mouseup', 0));
                target.dispatchEvent(mouse('click', 0));
                return { clicked: true, text: item.textContent || '' };
            }
            const input = document.querySelector('[data-ok-location-target="1"]');
            if (input) {
                input.dispatchEvent(new KeyboardEvent(
                    'keydown',
                    { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }
                ));
                input.dispatchEvent(new KeyboardEvent(
                    'keyup',
                    { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }
                ));
            }
            return { clicked: false, candidates: items.map((el) => clean(el.textContent)).slice(0, 5) };
        })()""".replace("__LOCATION_VALUE__", _js(value))
    selected = client.evaluate(location_script) or {}
    medium_delay()
    if not selected.get("clicked"):
        warnings.append("Location was typed but no Google Places suggestion was selected")


def _select_many(
    client: BaseClient,
    label: str,
    values: list[str],
    warnings: list[str],
) -> None:
    for value in values:
        opened = client.evaluate(
            f"""(() => {{
                const label = {label!r};
                const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
                const item = [...document.querySelectorAll('.dy-form-item')].find((it) => {{
                    const text = clean(it.querySelector('.dy-form-item-label, [class*="FormItemLabel"]')?.textContent || '');
                    return text.toLowerCase() === label.toLowerCase();
                }});
                if (!item) return false;
                const trigger = item.querySelector('[class*="SelectTrigger"], [class*="dySelect"], button');
                if (!trigger) return false;
                trigger.scrollIntoView({{ block: 'center' }});
                trigger.click();
                return true;
            }})()"""
        )
        if not opened:
            warnings.append(f"Could not open {label} selector")
            return
        short_delay()
        if not _click_option(client, value, required=False):
            warnings.append(f"Could not select {label}: {value}")
        short_delay()


def _select_affix_dropdown(client: BaseClient, label: str, option: str) -> bool:
    opened = client.evaluate(
        f"""(() => {{
            const label = {label!r};
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            const item = [...document.querySelectorAll('.dy-form-item')].find((it) => {{
                const text = clean(it.querySelector('.dy-form-item-label, [class*="FormItemLabel"]')?.textContent || '');
                return text.toLowerCase() === label.toLowerCase();
            }});
            if (!item) return false;
            const btns = [...item.querySelectorAll('button')];
            const btn = btns.find((b) => /^per\\s+/i.test(clean(b.textContent))) || btns.at(-1);
            if (!btn) return false;
            btn.scrollIntoView({{ block: 'center' }});
            btn.click();
            return true;
        }})()"""
    )
    if not opened:
        return False
    short_delay()
    return _click_option(client, option, required=False)


def _click_submit(client: BaseClient) -> bool:
    return bool(
        client.evaluate(
            """(() => {
                const btn = document.querySelector('.submit-button');
                if (!btn) return false;
                btn.scrollIntoView({ block: 'center' });
                btn.click();
                return true;
            })()"""
        )
    )


def _click_draft(client: BaseClient) -> bool:
    return bool(
        client.evaluate(
            """(() => {
                const btn = document.querySelector('.draft-button');
                if (!btn) return false;
                btn.scrollIntoView({ block: 'center' });
                btn.click();
                return true;
            })()"""
        )
    )


def _wait_for_submit_result(client: BaseClient, timeout: float = 20.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        url = client.get_url() or ""
        if "/publish/property" not in url:
            return "navigated"
        if _extract_validation_errors(client):
            return "validation"
        time.sleep(0.5)
    return "timeout"


def _extract_validation_errors(client: BaseClient) -> list[str]:
    raw = client.evaluate(
        """(() => {
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            const visible = (el) => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            };
            const nodes = [...document.querySelectorAll(
                '[class*="error"], [class*="Error"], [class*="invalid"], [class*="Invalid"], .invalid-feedback'
            )];
            return [...new Set(nodes.filter(visible).map((el) => clean(el.textContent)).filter(Boolean))];
        })()"""
    )
    return raw or []


def _normalize_mode(value: str) -> str:
    mode = _norm(value)
    aliases = {"for-rent": "rent", "rental": "rent", "for-sale": "sale", "buy": "sale"}
    mode = aliases.get(mode, mode)
    if mode not in MODE_CATEGORY_IDS:
        raise ValueError("mode must be rent or sale")
    return mode


def _normalize_property_type(value: str) -> str:
    kind = _norm(value)
    if kind not in PROPERTY_TYPE_LABELS:
        raise ValueError(
            "property_type must be one of: " + ", ".join(PROPERTY_TYPE_LABELS)
        )
    return kind


def _norm(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-").replace(" ", "-")


def _num_to_text(value: str | int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _car_spaces_label(value: str | int) -> str:
    text = str(value).strip().lower()
    if text in {"0", "none", "no", "no-car-space", "no car space"}:
        return "no car space"
    return str(value)


_PHONE_CODES_BY_SUBDOMAIN = {
    "ae": ("00971", "971"),
    "au": ("0061", "61"),
    "ca": ("001", "1"),
    "gb": ("0044", "44"),
    "hk": ("00852", "852"),
    "jp": ("0081", "81"),
    "my": ("0060", "60"),
    "nz": ("0064", "64"),
    "sg": ("0065", "65"),
    "us": ("001", "1"),
}


def _local_phone(value: str, subdomain: str) -> str:
    digits = re.sub(r"\D+", "", value)
    for prefix in _PHONE_CODES_BY_SUBDOMAIN.get(subdomain.strip().lower(), ()):
        if digits.startswith(prefix):
            digits = digits[len(prefix):]
            break
    if len(digits) == 10 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def _abs_existing_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return str(p)


def _js(value: Any) -> str:
    return json.dumps(value)


def result_to_dict(result: PublishPropertyResult) -> dict[str, Any]:
    return {
        "success": result.success,
        "action": result.action,
        "mode": result.mode,
        "property_type": result.property_type,
        "url": result.url,
        "submitted": result.submitted,
        "draft_saved": result.draft_saved,
        "submit_state": result.submit_state,
        "warnings": result.warnings,
        "validation_errors": result.validation_errors,
    }
