import { useState } from 'react';
import type { AppLanguage } from '../App';

export default function Filters({
  query,
  setQuery,
  maxPrice,
  setMaxPrice,
  language = 'en',
}: {
  query: string;
  setQuery: (value: string) => void;
  maxPrice: number;
  setMaxPrice: (value: number) => void;
  language?: AppLanguage;
}) {
  const [draftQuery, setDraftQuery] = useState(query);
  const [draftPrice, setDraftPrice] = useState(maxPrice === 0 ? '' : String(maxPrice));

  const copy = language === 'hi'
    ? {
        search: 'उपज खोजें',
        placeholder: 'टमाटर, प्याज, पालक...',
        maxPrice: 'प्रति किलो अधिकतम कीमत',
        button: 'खोजें',
      }
    : {
        search: 'Search produce',
        placeholder: 'Tomato, onion, spinach...',
        maxPrice: 'Max price per kg',
        button: 'Search',
      };

  function apply() {
    setQuery(draftQuery.trim());
    setMaxPrice(draftPrice === '' ? 0 : Number(draftPrice));
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') apply();
  }

  return (
    <div className="filters">
      <div>
        <label className="label">{copy.search}</label>
        <input
          value={draftQuery}
          onChange={(e) => setDraftQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={copy.placeholder}
        />
      </div>
      <div>
        <label className="label">{copy.maxPrice}</label>
        <input
          type="number"
          value={draftPrice}
          onChange={(e) => setDraftPrice(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="0"
        />
      </div>
      <button type="button" className="primary-button" onClick={apply}>
        {copy.button}
      </button>
    </div>
  );
}
