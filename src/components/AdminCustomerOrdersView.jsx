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

  const updateOrderStatus = (orderId, newStatus) => {
    const updated = orders.map((o) => (o.id === orderId ? { ...o, status: newStatus } : o));
    setOrders(updated);
    try {
      localStorage.setItem('shelf_customer_orders', JSON.stringify(updated));
    } catch {}
    onToast?.(`Order ${orderId} marked as ${newStatus}`);
  };

  const deleteOrder = (orderId) => {
    if (window.confirm(`Delete order ${orderId} from log?`)) {
      const updated = orders.filter((o) => o.id !== orderId);
      setOrders(updated);
      try {
        localStorage.setItem('shelf_customer_orders', JSON.stringify(updated));
      } catch {}
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
                          {cleanPhone && (
                            <a
                              href={waChatUrl}
                              target="_blank"
                              rel="noreferrer"
                              style={{ background: '#22c55e', color: '#fff', borderRadius: '6px', padding: '6px 10px', fontSize: '11px', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                              title="Chat with customer on WhatsApp"
                            >
                              <span>Chat WA</span> ↗
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
    </div>
  );
}
