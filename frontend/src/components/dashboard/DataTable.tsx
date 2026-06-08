import type { ReactNode } from 'react';

type Column<T> = {
  key: string;
  label: string;
  width?: string;
  align?: 'left' | 'right' | 'center';
  render: (row: T) => ReactNode;
};

export default function DataTable<T>({
  columns,
  rows,
  emptyTitle,
  emptyBody,
}: {
  columns: Column<T>[];
  rows: T[];
  emptyTitle: string;
  emptyBody: string;
}) {
  if (rows.length === 0) {
    return (
      <div className="bb-empty-state">
        <strong>{emptyTitle}</strong>
        <p>{emptyBody}</p>
      </div>
    );
  }

  return (
    <div className="bb-table-wrap">
      <table className="bb-data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} style={column.width ? { width: column.width } : undefined} data-align={column.align || 'left'}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key} data-align={column.align || 'left'}>
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
