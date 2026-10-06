import React, { useState, useMemo } from 'react';
import Icon from './Icon.jsx';

function money(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

export default function AdminCustomerOrdersView({ onToast }) {
  const [orders, setOrders] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('shelf_customer_orders') || '[]');
    } catch {
      return [];
    }
  });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Fetch real orders from backend database on mount
  React.useEffect(() => {
    fetch('/api/orders')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && Array.isArray(data.orders)) {
          setOrders(data.orders);
          try {
            localStorage.setItem('shelf_customer_orders', JSON.stringify(data.orders));
          } catch {}
        }
      })
      .catch(() => {});
  }, []);

  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const q = search.toLowerCase().trim();
      if (q) {
        const matchesName = (o.customer || '').toLowerCase().includes(q);
        const matchesPhone = (o.phone || '').includes(q);
        const matchesId = (o.id || '').toLowerCase().includes(q);
        const matchesProduct = (o.product || '').toLowerCase().includes(q);
        if (!matchesName && !matchesPhone && !matchesId && !matchesProduct) return false;
      }
      if (statusFilter !== 'all' && (o.status || 'Pending') !== statusFilter) return false;
      return true;
    });
  }, [orders, search, statusFilter]);

  const [selectedFulfillOrder, setSelectedFulfillOrder] = useState(null);
  const [fulfillmentData, setFulfillmentData] = useState(null);
  const [isFulfilling, setIsFulfilling] = useState(false);
  const [copiedClipboard, setCopiedClipboard] = useState(false);

  const handleOpenAiFulfill = async (order) => {
    setSelectedFulfillOrder(order);
    setIsFulfilling(true);
    setFulfillmentData(null);
    setCopiedClipboard(false);
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(order.id)}/ai-fulfill`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success && data.fulfillment) {
        setFulfillmentData(data.fulfillment);
      } else {
        const price = Number(order.price || 499);
        const base = Number(order.base_cost || Math.round(price * 0.70));
        const margin = Math.max(0, price - base);
        setFulfillmentData({
          order_id: order.id,
          meesho_code: order.ext_id || '374453404',
          meesho_url: order.ext_id ? `https://www.meesho.com/p/${order.ext_id}` : 'https://www.meesho.com',
          financials: { customer_price: price, base_cost: base, reseller_margin: margin },
          customer: { name: order.customer, phone: order.phone, address: { full_text: order.address, pincode: order.pincode } },
          clipboard_text: `Customer: ${order.customer}\nPhone: ${order.phone}\nAddress: ${order.address}\nPincode: ${order.pincode}\nResell Order: YES\nCustomer COD: ₹${price}\nMargin: ₹${margin}`
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsFulfilling(false);
    }
  };

  const updateOrderStatus = (orderId, newStatus, fulfillmentStatus) => {
    const updated = orders.map((o) => (o.id === orderId ? { ...o, status: newStatus, ...(fulfillmentStatus ? { fulfillment_status: fulfillmentStatus } : {}) } : o));
    setOrders(updated);
    try {
      localStorage.setItem('shelf_customer_orders', JSON.stringify(updated));
    } catch {}

    const patchBody = { status: newStatus };
    if (fulfillmentStatus) patchBody.fulfillment_status = fulfillmentStatus;

    fetch(`/api/orders/${encodeURIComponent(orderId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patchBody)
    }).catch(() => {});

    onToast?.(`Order ${orderId} marked as ${newStatus}`);
  };

  const deleteOrder = (orderId) => {
    if (window.confirm(`Delete order ${orderId} from database?`)) {
      const updated = orders.filter((o) => o.id !== orderId);
      setOrders(updated);
      try {
        localStorage.setItem('shelf_customer_orders', JSON.stringify(updated));
      } catch {}

      fetch(`/api/orders/${encodeURIComponent(orderId)}`, {
        method: 'DELETE'
      }).catch(() => {});

      onToast?.(`Order ${orderId} removed`);
    }
  };

  const exportOrdersCSV = () => {
    if (orders.length === 0) {
      alert('No customer orders to export yet.');
      return;
    }
    const headers = ['Order Ref', 'Date', 'Customer Name', 'Phone', 'Address', 'Pincode', 'Product', 'Size', 'Color', 'Price', 'Payment Method', 'Status'];
    const rows = orders.map((o) => [
      o.id || '',
      o.date ? new Date(o.date).toLocaleDateString('en-IN') : '',
      `"${(o.customer || '').replace(/"/g, '""')}"`,
      `"${o.phone || ''}"`,
      `"${(o.address || '').replace(/"/g, '""')}"`,
      `"${o.pincode || ''}"`,
      `"${(o.product || '').replace(/"/g, '""')}"`,
      o.size || 'M',
      o.color || 'Standard',
      o.price || 0,
      o.paymentMethod || 'COD',
      o.status || 'Pending'
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `shelf-orders-${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    onToast?.('✓ Orders CSV exported successfully');
  };

  return (
    <div className="standard-view" style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            📦 Customer Orders & WhatsApp Log
            <span style={{ fontSize: '12px', background: 'rgba(34, 197, 94, 0.15)', color: '#16a34a', border: '1px solid rgba(34, 197, 94, 0.3)', padding: '3px 10px', borderRadius: '999px', fontWeight: 700 }}>
              {orders.length} Total Bookings
            </span>
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            Audit log of direct orders placed by shoppers via WhatsApp & Instant Checkout.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            type="button"
            className="button button-dark"
            onClick={exportOrdersCSV}
            style={{ fontSize: '13px', fontWeight: 700, gap: '6px' }}
          >
            <Icon name="download" size={16} /> Export Orders CSV
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ flex: '1 1 280px', position: 'relative' }}>
          <input
            type="text"
            placeholder="Search by customer name, phone, order ref (#SHF), or product..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--paper)', color: 'var(--ink)' }}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ height: '42px', borderRadius: '10px', border: '1px solid var(--line)', padding: '0 14px', fontSize: '13px', background: 'var(--paper)', color: 'var(--ink)', cursor: 'pointer' }}
        >
          <option value="all">All Statuses</option>
          <option value="Pending">Pending Confirmation</option>
          <option value="Confirmed">Confirmed</option>
          <option value="Dispatched">Dispatched</option>
          <option value="Delivered">Delivered</option>
        </select>
      </div>

      {/* Orders Table */}
      {filteredOrders.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--paper)', borderRadius: '16px', border: '1px solid var(--line)' }}>
          <span style={{ fontSize: '42px', display: 'block', marginBottom: '12px' }}>📭</span>
          <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--ink)' }}>No Customer Orders Found</h3>
          <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '4px' }}>
            {search ? 'Try clearing your search query.' : 'When shoppers click "Order Now" on your storefront, orders will appear here automatically.'}
          </p>
        </div>
      ) : (
        <div style={{ background: 'var(--paper)', borderRadius: '16px', border: '1px solid var(--line)', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'var(--canvas)', borderBottom: '1px solid var(--line)', color: 'var(--ink-soft)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '14px 16px' }}>Order Ref & Date</th>
                  <th style={{ padding: '14px 16px' }}>Customer & Contact</th>
                  <th style={{ padding: '14px 16px' }}>Item & Specifications</th>
                  <th style={{ padding: '14px 16px' }}>Delivery Address</th>
                  <th style={{ padding: '14px 16px' }}>Price & Payment</th>
                  <th style={{ padding: '14px 16px' }}>Status</th>
                  <th style={{ padding: '14px 16px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((order) => {
                  const cleanPhone = (order.phone || '').replace(/\D/g, '');
                  const waChatUrl = cleanPhone 
                    ? `https://wa.me/91${cleanPhone}?text=${encodeURIComponent(`Hi ${order.customer || 'there'}! This is regarding your order ${order.id} from Shelf Store.`)}` 
                    : '#';
                  const currentStatus = order.status || 'Pending';

                  return (
                    <tr key={order.id} style={{ borderBottom: '1px solid var(--line)', verticalAlign: 'top' }}>
                      <td style={{ padding: '14px 16px' }}>
                        <strong style={{ color: 'var(--primary)', display: 'block', fontSize: '13px' }}>{order.id}</strong>
                        <small style={{ color: 'var(--muted)', fontSize: '11px' }}>
                          {order.date ? new Date(order.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                        </small>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <strong style={{ color: 'var(--ink)', display: 'block' }}>{order.customer}</strong>
                        <span style={{ color: 'var(--ink-soft)', fontSize: '12px' }}>📞 +91 {cleanPhone}</span>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--ink)', display: 'block' }}>{order.product}</span>
                        <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                          <span style={{ fontSize: '11px', background: 'var(--canvas)', border: '1px solid var(--line)', padding: '2px 6px', borderRadius: '4px' }}>
                            Size: <strong>{order.size || 'M'}</strong>
                          </span>
                          {order.color && order.color !== 'Standard' && (
                            <span style={{ fontSize: '11px', background: 'var(--canvas)', border: '1px solid var(--line)', padding: '2px 6px', borderRadius: '4px' }}>
                              Color: <strong>{order.color}</strong>
                            </span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px', maxWidth: '240px' }}>
                        <span style={{ color: 'var(--ink)', fontSize: '12px', lineHeight: 1.4, display: 'block' }}>{order.address}</span>
                        <span style={{ color: 'var(--muted)', fontSize: '11px', fontWeight: 600 }}>Pincode: {order.pincode}</span>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <strong style={{ fontSize: '14px', color: 'var(--ink)' }}>{money(order.price)}</strong>
                        <small style={{ display: 'block', color: 'var(--ink-soft)', fontSize: '11px' }}>{order.paymentMethod || 'COD'}</small>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <select
                          value={currentStatus}
                          onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                          style={{
                            fontSize: '11.5px',
                            fontWeight: 700,
                            padding: '4px 8px',
                            borderRadius: '6px',
                            border: '1px solid var(--line)',
                            background: currentStatus === 'Delivered' ? '#dcfce7' : currentStatus === 'Dispatched' ? '#dbeafe' : '#fef9c3',
                            color: currentStatus === 'Delivered' ? '#15803d' : currentStatus === 'Dispatched' ? '#1d4ed8' : '#854d0e',
                            cursor: 'pointer'
                          }}
                        >
                          <option value="Pending">Pending</option>
                          <option value="Confirmed">Confirmed</option>
                          <option value="Dispatched">Dispatched</option>
                          <option value="Delivered">Delivered</option>
                        </select>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', alignItems: 'center' }}>
                          <button
                            type="button"
                            onClick={() => handleOpenAiFulfill(order)}
                            style={{
                              background: order.fulfillment_status === 'dispatched' ? 'rgba(34, 197, 94, 0.15)' : 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                              color: order.fulfillment_status === 'dispatched' ? '#16a34a' : '#fff',
                              border: order.fulfillment_status === 'dispatched' ? '1px solid rgba(34, 197, 94, 0.3)' : 'none',
                              borderRadius: '8px',
                              padding: '6px 12px',
                              fontSize: '11.5px',
                              fontWeight: 800,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                              boxShadow: order.fulfillment_status === 'dispatched' ? 'none' : '0 2px 8px rgba(99, 102, 241, 0.25)'
                            }}
                            title="Open 1-Click AI Auto-Fulfillment Assistant"
                          >
                            <span>🤖</span> {order.fulfillment_status === 'dispatched' ? '✓ Dispatched' : 'AI Auto-Fulfill'}
                          </button>
                          {cleanPhone && (
                            <a
                              href={waChatUrl}
                              target="_blank"
                              rel="noreferrer"
                              style={{ background: '#22c55e', color: '#fff', borderRadius: '8px', padding: '6px 10px', fontSize: '11px', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                              title="Chat with customer on WhatsApp"
                            >
                              <span>WA</span> ↗
                            </a>
                          )}
                          <button
                            type="button"
                            onClick={() => deleteOrder(order.id)}
                            style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px', fontSize: '14px' }}
                            title="Delete order"
                          >
                            ✕
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── AI 1-Click Auto-Fulfillment Assistant Modal ── */}
      {selectedFulfillOrder && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.75)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 99999,
            padding: '20px'
          }}
          onClick={() => setSelectedFulfillOrder(null)}
        >
          <div
            style={{
              background: 'var(--paper, #ffffff)',
              borderRadius: '24px',
              maxWidth: '680px',
              width: '100%',
              padding: '28px',
              boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.35)',
              border: '1px solid var(--line, #e2e8f0)',
              position: 'relative',
              maxHeight: '90vh',
              overflowY: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', color: '#fff', padding: '3px 8px', borderRadius: '6px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    🤖 AI Auto-Fulfillment Agent
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 600 }}>
                    Order {selectedFulfillOrder.id}
                  </span>
                </div>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--ink)' }}>
                  1-Click Meesho Reseller Dispatch
                </h2>
                <p style={{ fontSize: '12.5px', color: 'var(--muted)', marginTop: '2px' }}>
                  AI calculates reseller margins and prepares automated shipping payload. You only verify and dispatch!
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedFulfillOrder(null)}
                style={{ background: 'var(--canvas)', border: '1px solid var(--line)', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--ink)' }}
              >
                ✕
              </button>
            </div>

            {isFulfilling ? (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <span style={{ fontSize: '32px', display: 'block', marginBottom: '12px' }}>⚙️</span>
                <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--ink)' }}>AI analyzing order &amp; calculating reseller margins...</p>
              </div>
            ) : fulfillmentData ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {/* Product & Code Strip */}
                <div style={{ background: 'var(--canvas)', borderRadius: '14px', padding: '14px', border: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <strong style={{ fontSize: '13.5px', color: 'var(--ink)', display: 'block' }}>
                      {selectedFulfillOrder.product}
                    </strong>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '4px', fontSize: '11.5px', color: 'var(--muted)' }}>
                      <span>Size: <strong style={{ color: 'var(--ink)' }}>{selectedFulfillOrder.size || 'M'}</strong></span>
                      <span>·</span>
                      <span>Color: <strong style={{ color: 'var(--ink)' }}>{selectedFulfillOrder.color || 'Standard'}</strong></span>
                      <span>·</span>
                      <span>Meesho Code: <strong style={{ color: 'var(--primary, #6366f1)' }}>{fulfillmentData.meesho_code}</strong></span>
                    </div>
                  </div>

                  <a
                    href={fulfillmentData.meesho_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ background: 'var(--ink)', color: '#fff', padding: '6px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  >
                    Open on Meesho ↗
                  </a>
                </div>

                {/* Financial Margin Breakdown */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                  <div style={{ background: 'rgba(99, 102, 241, 0.08)', borderRadius: '12px', padding: '12px', border: '1px solid rgba(99, 102, 241, 0.2)', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', fontWeight: 600 }}>Customer Collect (COD)</span>
                    <strong style={{ fontSize: '18px', color: 'var(--ink)', marginTop: '2px', display: 'block' }}>
                      {money(fulfillmentData.financials?.customer_price)}
                    </strong>
                  </div>

                  <div style={{ background: 'var(--canvas)', borderRadius: '12px', padding: '12px', border: '1px solid var(--line)', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', fontWeight: 600 }}>Meesho Wholesale Base</span>
                    <strong style={{ fontSize: '18px', color: 'var(--muted)', marginTop: '2px', display: 'block' }}>
                      {money(fulfillmentData.financials?.base_cost)}
                    </strong>
                  </div>

                  <div style={{ background: 'rgba(34, 197, 94, 0.12)', borderRadius: '12px', padding: '12px', border: '1px solid rgba(34, 197, 94, 0.3)', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#15803d', display: 'block', fontWeight: 700 }}>Your Reseller Net Profit</span>
                    <strong style={{ fontSize: '18px', color: '#16a34a', marginTop: '2px', display: 'block' }}>
                      +{money(fulfillmentData.financials?.reseller_margin)}
                    </strong>
                  </div>
                </div>

                {/* Shipping Delivery Details Box */}
                <div style={{ background: 'var(--paper)', borderRadius: '14px', border: '1px solid var(--line)', padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--ink)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      📦 Customer Shipping Address
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard?.writeText(fulfillmentData.clipboard_text);
                        setCopiedClipboard(true);
                        onToast?.('✓ Copied formatted address & margin for Meesho app!');
                        setTimeout(() => setCopiedClipboard(false), 2500);
                      }}
                      style={{ background: 'none', border: 'none', color: 'var(--primary, #6366f1)', fontSize: '12px', fontWeight: 700, cursor: 'pointer' }}
                    >
                      {copiedClipboard ? '✓ Copied to Clipboard!' : '📋 Copy All Formatted Details'}
                    </button>
                  </div>

                  <div style={{ fontSize: '13px', color: 'var(--ink)', lineHeight: 1.5 }}>
                    <div><strong>Recipient:</strong> {fulfillmentData.customer?.name} (📞 +91 {fulfillmentData.customer?.phone})</div>
                    <div><strong>Address:</strong> {fulfillmentData.customer?.address?.full_text || selectedFulfillOrder.address}</div>
                    <div><strong>Pincode:</strong> {selectedFulfillOrder.pincode}</div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '8px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      updateOrderStatus(selectedFulfillOrder.id, 'Dispatched', 'dispatched');
                      setSelectedFulfillOrder(null);
                      onToast?.(`🚀 Order ${selectedFulfillOrder.id} marked as Dispatched! Net profit +${money(fulfillmentData.financials?.reseller_margin)}`);
                    }}
                    style={{
                      flex: '1 1 200px',
                      height: '44px',
                      borderRadius: '12px',
                      background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
                      color: '#fff',
                      fontSize: '13px',
                      fontWeight: 800,
                      border: 'none',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 14px rgba(22, 163, 74, 0.3)'
                    }}
                  >
                    <span>✓</span> Verify &amp; Confirm Dispatched
                  </button>

                  {fulfillmentData.whatsapp_notify_text && (
                    <a
                      href={`https://wa.me/91${fulfillmentData.customer?.phone}?text=${encodeURIComponent(fulfillmentData.whatsapp_notify_text)}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        padding: '0 16px',
                        height: '44px',
                        borderRadius: '12px',
                        background: '#22c55e',
                        color: '#fff',
                        fontSize: '12.5px',
                        fontWeight: 700,
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                      title="Send tracking message to customer on WhatsApp"
                    >
                      <span>💬 Notify Customer</span>
                    </a>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
