import React from 'react';
import Icon from './Icon.jsx';

export default function Pagination({ page, pageCount, totalItems, pageSize, onPageChange }) {
  if (pageCount <= 1) return null;
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);
  const visiblePages = [...new Set([1, page - 1, page, page + 1, pageCount])]
    .filter((number) => number >= 1 && number <= pageCount)
    .sort((a, b) => a - b);
  const pages = [];
  visiblePages.forEach((number, index) => {
    if (index > 0 && number - visiblePages[index - 1] > 1) pages.push('gap');
    pages.push(number);
  });

  return (
    <nav className="pagination" aria-label="Product pages">
      <span className="pagination-summary">Showing <strong>{start}–{end}</strong> of {totalItems} picks</span>
      <div className="pagination-controls">
        <button className="pagination-arrow" type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1} aria-label="Previous page"><Icon name="chevronRight" size={14} className="pagination-prev-icon" /></button>
        {pages.map((number, index) => number === 'gap'
          ? <span className="pagination-gap" key={`gap-${index}`}>…</span>
          : <button className={`pagination-page${page === number ? ' is-current' : ''}`} type="button" key={number} onClick={() => onPageChange(number)} aria-label={`Page ${number}`} aria-current={page === number ? 'page' : undefined}>{number}</button>)}
        <button className="pagination-arrow" type="button" onClick={() => onPageChange(page + 1)} disabled={page >= pageCount} aria-label="Next page"><Icon name="chevronRight" size={14} /></button>
      </div>
    </nav>
  );
}
