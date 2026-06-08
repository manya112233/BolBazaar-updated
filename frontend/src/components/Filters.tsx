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
  const copy = language === 'hi'
    ? {
        search: 'उपज खोजें',
        placeholder: 'टमाटर, प्याज, पालक...',
        maxPrice: 'प्रति किलो अधिकतम कीमत',
      }
    : {
        search: 'Search produce',
        placeholder: 'Tomato, onion, spinach...',
        maxPrice: 'Max price per kg',
      };

  return (
    <div className="filters">
      <div>
        <label className="label">{copy.search}</label>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={copy.placeholder} />
      </div>
      <div>
        <label className="label">{copy.maxPrice}</label>
        <input type="number" value={maxPrice} onChange={(e) => setMaxPrice(Number(e.target.value || 0))} />
      </div>
    </div>
  );
}
