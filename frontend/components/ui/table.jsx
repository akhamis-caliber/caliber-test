import React from 'react';

export const Table = ({ children, className = '', ...props }) => (
  <div className={`relative w-full overflow-auto ${className}`} {...props}>
    <table className="w-full caption-bottom text-sm">
      {children}
    </table>
  </div>
);

export const TableHeader = ({ children, className = '', ...props }) => (
  <thead className={`[&_tr]:border-b ${className}`} {...props}>
    {children}
  </thead>
);

export const TableBody = ({ children, className = '', ...props }) => (
  <tbody className={`[&_tr:last-child]:border-0 ${className}`} {...props}>
    {children}
  </tbody>
);

export const TableFooter = ({ children, className = '', ...props }) => (
  <tfoot className={`border-t bg-muted/50 [&>tr]:last:border-b-0 ${className}`} {...props}>
    {children}
  </tfoot>
);

export const TableRow = ({ children, className = '', ...props }) => (
  <tr className={`border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted ${className}`} {...props}>
    {children}
  </tr>
);

export const TableHead = ({ children, className = '', ...props }) => (
  <th className={`h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 ${className}`} {...props}>
    {children}
  </th>
);

export const TableCell = ({ children, className = '', ...props }) => (
  <td className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`} {...props}>
    {children}
  </td>
);

export const TableCaption = ({ children, className = '', ...props }) => (
  <caption className={`mt-4 text-sm text-muted-foreground ${className}`} {...props}>
    {children}
  </caption>
); 