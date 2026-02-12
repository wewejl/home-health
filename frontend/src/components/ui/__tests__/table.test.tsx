/**
 * Table 组件测试
 *
 * 测试覆盖：
 * 1. Table 基础渲染
 * 2. TableHeader, TableBody, TableFooter
 * 3. TableHead, TableCell
 * 4. TableRow
 * 5. TableCaption
 * 6. 样式类名应用
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from '../table';

describe('Table Components', () => {
  const sampleData = [
    { id: 1, name: 'John', age: 30 },
    { id: 2, name: 'Jane', age: 25 },
    { id: 3, name: 'Bob', age: 35 },
  ];

  describe('Table', () => {
    it('should render table wrapper div', () => {
      render(
        <Table>
          <tbody>
            <tr>
              <td>Content</td>
            </tr>
          </tbody>
        </Table>
      );

      const wrapper = screen.getByText('Content').closest('.relative');
      expect(wrapper).toBeInTheDocument();
      expect(wrapper).toHaveClass('w-full', 'overflow-auto');
    });

    it('should apply custom className', () => {
      render(
        <Table className="custom-table">
          <tbody>
            <tr>
              <td>Test</td>
            </tr>
          </tbody>
        </Table>
      );

      const table = screen.getByText('Test').closest('table');
      expect(table).toHaveClass('custom-table');
    });
  });

  describe('TableHeader', () => {
    it('should render thead element', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      );

      const thead = document.querySelector('thead');
      expect(thead).toBeInTheDocument();
    });

    it('should apply header styling', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Column 1</TableHead>
              <TableHead>Column 2</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      );

      const headerRow = screen.getByText('Column 1').closest('tr');
      expect(headerRow).toHaveClass('border-b', 'bg-muted\\/30');
    });
  });

  describe('TableBody', () => {
    it('should render tbody element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Row Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const tbody = document.querySelector('tbody');
      expect(tbody).toBeInTheDocument();
    });

    it('should remove bottom border from last row', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell 1</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Cell 2</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const tbody = document.querySelector('tbody');
      expect(tbody).toHaveClass('[&_tr:last-child]:border-0');
    });
  });

  describe('TableFooter', () => {
    it('should render tfoot element', () => {
      render(
        <Table>
          <TableFooter>
            <TableRow>
              <TableCell>Footer</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      );

      const tfoot = document.querySelector('tfoot');
      expect(tfoot).toBeInTheDocument();
    });

    it('should apply footer styling', () => {
      render(
        <Table>
          <TableFooter>
            <TableRow>
              <TableCell>Total</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      );

      const footerRow = screen.getByText('Total').closest('tr');
      expect(footerRow).toHaveClass('border-t', 'bg-secondary\\/50');
    });
  });

  describe('TableRow', () => {
    it('should render tr element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Row Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const row = screen.getByText('Row Content').closest('tr');
      expect(row?.tagName).toBe('TR');
    });

    it('should have bottom border', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const row = screen.getByText('Cell').closest('tr');
      expect(row).toHaveClass('border-b', 'border-border\\/50');
    });

    it('should have hover effect', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Hoverable</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const row = screen.getByText('Hoverable').closest('tr');
      expect(row).toHaveClass('hover:bg-muted\\/20');
    });

    it('should apply custom className', () => {
      render(
        <Table>
          <TableBody>
            <TableRow className="custom-row">
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const row = screen.getByText('Cell').closest('tr');
      expect(row).toHaveClass('custom-row');
    });
  });

  describe('TableHead', () => {
    it('should render th element', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header Cell</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      );

      const headerCell = screen.getByText('Header Cell');
      expect(headerCell.tagName).toBe('TH');
    });

    it('should have proper height and padding', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Column Name</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      );

      const th = screen.getByText('Column Name');
      expect(th).toHaveClass('h-12', 'px-4');
    });

    it('should have font weight styling', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Bold Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      );

      const th = screen.getByText('Bold Header');
      expect(th).toHaveClass('font-semibold');
    });

    it('should support custom align', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-right">Right Aligned</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      );

      const th = screen.getByText('Right Aligned');
      expect(th).toHaveClass('text-right');
    });
  });

  describe('TableCell', () => {
    it('should render td element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const cell = screen.getByText('Cell Content');
      expect(cell.tagName).toBe('TD');
    });

    it('should have proper padding', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const cell = screen.getByText('Content');
      expect(cell).toHaveClass('p-4');
    });

    it('should apply custom className', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className="text-right">Right</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const cell = screen.getByText('Right');
      expect(cell).toHaveClass('text-right');
    });
  });

  describe('TableCaption', () => {
    it('should render caption element', () => {
      render(
        <Table>
          <TableCaption>Table Caption</TableCaption>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const caption = screen.getByText('Table Caption');
      expect(caption.tagName).toBe('CAPTION');
    });

    it('should have proper text styling', () => {
      render(
        <Table>
          <TableCaption>Caption Text</TableCaption>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const caption = screen.getByText('Caption Text');
      expect(caption).toHaveClass('text-sm', 'text-foreground-secondary');
    });

    it('should have top margin', () => {
      render(
        <Table>
          <TableCaption>Margin Caption</TableCaption>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const caption = screen.getByText('Margin Caption');
      expect(caption).toHaveClass('mt-4');
    });
  });

  describe('Complete Table Structure', () => {
    it('should render full table with all components', () => {
      render(
        <Table>
          <TableCaption>User Data</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Age</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sampleData.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.id}</TableCell>
                <TableCell>{user.name}</TableCell>
                <TableCell>{user.age}</TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell colSpan={3}>Total: {sampleData.length} users</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      );

      expect(screen.getByText('User Data')).toBeInTheDocument();
      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Age')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('John')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('Total: 3 users')).toBeInTheDocument();
    });
  });

  describe('Display Names', () => {
    it('Table should have correct displayName', () => {
      expect(Table.displayName).toBe('Table');
    });

    it('TableHeader should have correct displayName', () => {
      expect(TableHeader.displayName).toBe('TableHeader');
    });

    it('TableBody should have correct displayName', () => {
      expect(TableBody.displayName).toBe('TableBody');
    });

    it('TableFooter should have correct displayName', () => {
      expect(TableFooter.displayName).toBe('TableFooter');
    });

    it('TableRow should have correct displayName', () => {
      expect(TableRow.displayName).toBe('TableRow');
    });

    it('TableHead should have correct displayName', () => {
      expect(TableHead.displayName).toBe('TableHead');
    });

    it('TableCell should have correct displayName', () => {
      expect(TableCell.displayName).toBe('TableCell');
    });

    it('TableCaption should have correct displayName', () => {
      expect(TableCaption.displayName).toBe('TableCaption');
    });
  });
});
