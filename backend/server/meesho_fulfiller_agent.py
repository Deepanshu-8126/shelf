"""Meesho AI Auto-Fulfillment Agent.

Eliminates manual entry for WhatsApp COD reselling orders:
- Parses customer delivery details into exact Meesho checkout fields
- Computes reseller margin (Selling Price - Wholesale Base Cost)
- Prepares 1-click clipboard dispatch payload
- Generates automated browser / deep-link bridge for 1-click execution
"""

import json
import re
from typing import Any, Dict, Optional


def extract_meesho_code(product_data: Dict[str, Any]) -> str:
    """Extract Meesho product ID (ext_id or code) from product dictionary."""
    ext_id = str(product_data.get("ext_id") or "").strip()
    if ext_id and ext_id.lower() != "none":
        return ext_id.replace("s-", "")
    
    url = str(product_data.get("productUrl") or product_data.get("product_url") or product_data.get("affiliateUrl") or "")
    if url:
        match = re.search(r"/p/([a-zA-Z0-9]+)", url, re.I) or re.search(r"[?&](?:p_id|ext_id)=([a-zA-Z0-9]+)", url, re.I)
        if match:
            return match.group(1)
            
    pid = str(product_data.get("id") or "").strip()
    digits = re.sub(r"\D", "", pid)
    return digits[:9] if digits else "374453404"


def parse_indian_address(full_address: str, pincode: str) -> Dict[str, str]:
    """Parse a single free-form address string into structured Meesho address fields."""
    clean_addr = str(full_address or "").strip()
    clean_pin = re.sub(r"\D", "", str(pincode or "")).strip()
    
    # Split into lines or comma segments
    parts = [p.strip() for p in re.split(r"[,\n]+", clean_addr) if p.strip()]
    
    house_flat = ""
    road_area = ""
    city_landmark = ""
    
    if len(parts) == 1:
        house_flat = parts[0][:40]
        road_area = parts[0]
        city_landmark = clean_pin
    elif len(parts) == 2:
        house_flat = parts[0]
        road_area = parts[1]
        city_landmark = parts[1]
    else:
        house_flat = parts[0]
        road_area = ", ".join(parts[1:-1])
        city_landmark = parts[-1]
        
    return {
        "house_flat": house_flat or "House / Flat No.",
        "road_area": road_area or clean_addr,
        "landmark": city_landmark or "",
        "pincode": clean_pin,
        "full_text": clean_addr
    }


def compute_reseller_financials(order: Dict[str, Any], product: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculate wholesale base cost, customer collection amount, and reseller net profit."""
    try:
        customer_price = float(re.sub(r"[^\d.]", "", str(order.get("price") or 499)))
    except Exception:
        customer_price = 499.0
        
    # Check if product has explicit base cost, else default to standard 30% wholesale discount
    base_cost = 0.0
    if product:
        raw_base = product.get("base_cost") or product.get("baseCost")
        if raw_base:
            try:
                base_cost = float(raw_base)
            except Exception:
                pass
                
    if base_cost <= 0:
        # Default estimated Meesho wholesale base price (typically 65-75% of customer retail price)
        base_cost = round(customer_price * 0.70, 0)
        
    reseller_margin = max(0.0, round(customer_price - base_cost, 0))
    
    return {
        "customer_price": customer_price,
        "base_cost": base_cost,
        "reseller_margin": reseller_margin,
        "margin_percentage": round((reseller_margin / customer_price * 100), 1) if customer_price > 0 else 0
    }


def build_ai_fulfillment_payload(order: Dict[str, Any], product: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create complete 1-click AI fulfillment packet for an incoming order."""
    product_data = product or {}
    meesho_code = extract_meesho_code(product_data) or order.get("ext_id") or "find"
    meesho_url = f"https://www.meesho.com/p/{meesho_code}" if meesho_code != "find" else "https://www.meesho.com"
    
    financials = compute_reseller_financials(order, product_data)
    addr = parse_indian_address(order.get("address") or order.get("customer_address") or "", order.get("pincode") or "")
    customer_phone = re.sub(r"\D", "", str(order.get("phone") or order.get("customer_phone") or ""))
    customer_name = (order.get("customer") or order.get("customer_name") or "Customer").strip()
    
    # 1-Click Clipboard payload ready to paste in Meesho app / web
    clipboard_text = (
        f"--- MEESHO RESELLER DISPATCH PACKET ---\n"
        f"Order Ref: {order.get('id') or order.get('order_ref')}\n"
        f"Item: {order.get('product') or order.get('product_title')}\n"
        f"Size: {order.get('size') or 'M'} | Color: {order.get('color') or 'Standard'}\n"
        f"Meesho Code: {meesho_code}\n\n"
        f"📦 DELIVERY ADDRESS:\n"
        f"Name: {customer_name}\n"
        f"Mobile: {customer_phone}\n"
        f"Address: {addr['full_text']}\n"
        f"Pincode: {addr['pincode']}\n\n"
        f"💰 RESELLING SETTINGS:\n"
        f"Reselling Order?: YES (Enable toggle)\n"
        f"Cash to Collect from Customer: ₹{int(financials['customer_price'])}\n"
        f"Wholesale Base Cost: ₹{int(financials['base_cost'])}\n"
        f"Your Net Profit Margin: ₹{int(financials['reseller_margin'])} (Credited to your bank)\n"
        f"Payment Mode: Cash on Delivery (COD)\n"
        f"----------------------------------------"
    )
    
    whatsapp_dispatch_msg = (
        f"Hi {customer_name}! 🌸 Great news from Shelf Store!\n\n"
        f"Your order *{order.get('id')}* for *{order.get('product')}* (Size: {order.get('size')}) "
        f"has been verified and scheduled for express dispatch via Meesho Logistics!\n\n"
        f"💵 Amount to pay on delivery: ₹{int(financials['customer_price'])} (Cash on Delivery)\n"
        f"🚚 Expected Delivery: 3-5 Business Days.\n\n"
        f"Thank you for shopping with us!"
    )
    
    return {
        "order_id": order.get("id") or order.get("order_ref"),
        "meesho_code": meesho_code,
        "meesho_url": meesho_url,
        "customer": {
            "name": customer_name,
            "phone": customer_phone,
            "address": addr,
            "size": order.get("size") or "M",
            "color": order.get("color") or "Standard"
        },
        "financials": financials,
        "clipboard_text": clipboard_text,
        "whatsapp_notify_text": whatsapp_dispatch_msg,
        "status": "ai_prepared",
        "action_required": "verify_and_confirm"
    }
