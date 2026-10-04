import React from 'react';
import Icon from './Icon.jsx';

export default function ShelfHeader({
  activeCategory = 'All Picks',
  onSelectCategory,
  searchQuery = '',
  onSearchChange,
  showSearch = false,
  onToggleSearch,
  wishlistCount = 0,
  cartCount = 0,
  onOpenWishlist,
  onOpenCart,
  categories = ['All Picks', 'Kurtis', 'Women Dresses', 'Tops & Tunics', 'Winter']
}) {
  return (
    <header className="shelf-header">
      <div className="shelf-header-inner">
        {/* Left: Brand Logo: shelf. */}
        <div className="shelf-brand-box" onClick={() => onSelectCategory && onSelectCategory('All Picks')}>
          <svg className="shelf-leaf-logo" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
            <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
          </svg>
          <span className="shelf-brand-title">shelf<span className="shelf-brand-period">.</span></span>
        </div>

        {/* Center: Minimal Category Navigation */}
        <nav className="shelf-categories-nav" aria-label="Store categories">
          {categories.map((cat) => {
            const isActive = activeCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                className={`shelf-nav-pill ${isActive ? 'active' : ''}`}
                onClick={() => onSelectCategory && onSelectCategory(cat)}
              >
                {cat}
                {isActive && <span className="shelf-nav-dot" />}
              </button>
            );
          })}
        </nav>

        {/* Right: Actions (Search, Wishlist, Cart) */}
        <div className="shelf-actions-group">
          {/* Search Toggle */}
          <div className="shelf-search-wrapper">
            {showSearch ? (
              <div className="shelf-search-input-pill">
                <Icon name="search" size={15} />
                <input
                  type="text"
                  placeholder="Search kurtis, dresses..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
                  autoFocus
                />
                <button
                  type="button"
                  className="shelf-icon-button"
                  onClick={onToggleSearch}
                  aria-label="Close search"
                >
                  <Icon name="close" size={13} />
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="shelf-icon-button"
                onClick={onToggleSearch}
                aria-label="Open search"
                title="Search shelf"
              >
                <Icon name="search" size={18} />
              </button>
            )}
          </div>

          {/* Wishlist Button with Badge */}
          <button
            type="button"
            className="shelf-icon-button shelf-badge-wrapper"
            onClick={onOpenWishlist}
            aria-label="Wishlist"
            title="Wishlisted items"
          >
            <Icon name="heart" size={18} />
            {wishlistCount > 0 && (
              <span className="shelf-count-badge">{wishlistCount}</span>
            )}
          </button>

          {/* Cart Bag with Badge */}
          <button
            type="button"
            className="shelf-icon-button shelf-badge-wrapper"
            onClick={onOpenCart}
            aria-label="Cart"
            title="Shopping cart"
          >
            <Icon name="bag" size={18} />
            {cartCount > 0 && (
              <span className="shelf-count-badge shelf-count-badge-black">{cartCount}</span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
