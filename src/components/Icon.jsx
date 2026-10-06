import React from 'react';

const shapes = {
  overview: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.6" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.6" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.6" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.6" /></>,
  collections: <><path d="M4 6.5h16" /><path d="M6 3.5h12a1 1 0 0 1 1 1v15l-7-4-7 4v-15a1 1 0 0 1 1-1Z" /></>,
  products: <><path d="m12 3 8.5 4.5v9L12 21l-8.5-4.5v-9L12 3Z" /><path d="m3.8 7.7 8.2 4.4 8.2-4.4M12 12v8.6" /></>,
  analytics: <><path d="M4 19.5V12" /><path d="M10 19.5V5" /><path d="M16 19.5v-9" /><path d="M22 19.5v-13" /></>,
  integrations: <><path d="M8.5 15.5 6 18a4 4 0 0 1-5.7-5.7l4-4a4 4 0 0 1 5.7 0" transform="translate(1 0)" /><path d="m15.5 8.5 2.5-2.5a4 4 0 0 1 5.7 5.7l-4 4a4 4 0 0 1-5.7 0" transform="translate(-1 0)" /><path d="m8.5 15.5 7-7" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06-1.6 2.77-.09-.03a1.7 1.7 0 0 0-1.83.3l-.07.06h-3.2l-.02-.09a1.7 1.7 0 0 0-1.24-1.35l-.09-.02-1.6-2.77.06-.06A1.7 1.7 0 0 0 10.4 14v-.08l1.6-2.77.09.02a1.7 1.7 0 0 0 1.83-.3l.07-.06h3.2l.02.09a1.7 1.7 0 0 0 1.24 1.35l.09.02 1.6 2.77-.06.06A1.7 1.7 0 0 0 19.4 15Z" transform="translate(-1.4 -1.1) scale(.93)" /></>,
  search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  arrowUpRight: <><path d="M7 17 17 7M8 7h9v9" /></>,
  arrowRight: <><path d="M4 12h15M13 5l7 7-7 7" /></>,
  chevronDown: <><path d="m6 9 6 6 6-6" /></>,
  chevronLeft: <><path d="m15 18-6-6 6-6" /></>,
  chevronRight: <><path d="m9 18 6-6-6-6" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4" /></>,
  link: <><path d="M10 13a5 5 0 0 0 7.1 0l2.2-2.2a5 5 0 0 0-7.1-7.1L11 4.9" /><path d="M14 11a5 5 0 0 0-7.1 0l-2.2 2.2a5 5 0 0 0 7.1 7.1l1.2-1.2" /></>,
  heart: <><path d="M20.8 8.9c0 4.4-8.8 10-8.8 10s-8.8-5.6-8.8-10A4.7 4.7 0 0 1 12 6.4a4.7 4.7 0 0 1 8.8 2.5Z" /></>,
  bag: <><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" /><path d="M3 6h18" /><path d="M16 10a4 4 0 0 1-8 0" /></>,
  copy: <><rect x="8" y="8" width="12" height="12" rx="2" /><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3" /></>,
  check: <><path d="m5 12 4 4L19 6" /></>,
  sparkles: <><path d="m12 3 1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3Z" /><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z" /></>,
  filter: <><path d="M4 6h16M7 12h10m-7 6h4" /></>,
  ellipsis: <><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  eye: <><path d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.4" /></>,
  download: <><path d="M12 3v12m-5-5 5 5 5-5M4 20h16" /></>,
  arrowUp: <><path d="m5 14 7-7 7 7M12 7v14" /></>,
  arrowDown: <><path d="M12 4v15m-7-7 7 7 7-7" /></>,
  globe: <><circle cx="12" cy="12" r="9" /><path d="M3.5 12h17M12 3c2.4 2.5 3.5 5.5 3.5 9s-1.1 6.5-3.5 9c-2.4-2.5-3.5-5.5-3.5-9S9.6 5.5 12 3Z" /></>,
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 1 1 8 0v3" /></>,
  shield: <><path d="M12 3 19 6v5c0 4.5-2.6 7.7-7 10-4.4-2.3-7-5.5-7-10V6l7-3Z" /><path d="m9 12 2 2 4-4" /></>,
  image: <><rect x="3.5" y="4" width="17" height="16" rx="2" /><circle cx="9" cy="9" r="1.5" /><path d="m20.5 15-5-5L7 18" /></>,
  x: <><path d="M18 6 6 18M6 6l12 12" /></>,
};

export default function Icon({ name, size = 18, strokeWidth = 1.8, className = '' }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {shapes[name] || shapes.sparkles}
    </svg>
  );
}
