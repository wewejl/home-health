/**
 * Card 组件测试
 *
 * 测试覆盖：
 * 1. Card 基础渲染
 * 2. CardHeader, CardTitle, CardDescription
 * 3. CardContent
 * 4. CardFooter
 * 5. 组合使用
 * 6. 自定义 className
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../card';

describe('Card Components', () => {
  describe('Card', () => {
    it('should render card element', () => {
      render(<Card>Card Content</Card>);
      const card = screen.getByText('Card Content').parentElement;
      expect(card).toHaveClass('rounded-lg', 'border', 'bg-surface');
    });

    it('should apply custom className', () => {
      render(<Card className="custom-class">Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('custom-class');
    });

    it('should have hover shadow effect', () => {
      render(<Card>Hover Test</Card>);
      const card = screen.getByText('Hover Test').parentElement;
      expect(card).toHaveClass('hover:shadow-md');
    });
  });

  describe('CardHeader', () => {
    it('should render header with proper padding', () => {
      render(
        <Card>
          <CardHeader>Header Content</CardHeader>
        </Card>
      );
      const header = screen.getByText('Header Content');
      expect(header).toHaveClass('p-6');
    });

    it('should apply flex layout', () => {
      render(
        <Card>
          <CardHeader>Header</CardHeader>
        </Card>
      );
      const header = screen.getByText('Header');
      expect(header.parentElement).toHaveClass('flex', 'flex-col');
    });
  });

  describe('CardTitle', () => {
    it('should render title with proper styling', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
          </CardHeader>
        </Card>
      );
      const title = screen.getByText('Card Title');
      expect(title).toHaveClass('text-xl', 'font-semibold');
    });

    it('should have tracking-tight for text', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title</CardTitle>
          </CardHeader>
        </Card>
      );
      const title = screen.getByText('Title');
      expect(title).toHaveClass('tracking-tight');
    });
  });

  describe('CardDescription', () => {
    it('should render description with muted color', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription>Card Description</CardDescription>
          </CardHeader>
        </Card>
      );
      const description = screen.getByText('Card Description');
      expect(description).toHaveClass('text-foreground-secondary');
    });

    it('should have small text size', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription>Description</CardDescription>
          </CardHeader>
        </Card>
      );
      const description = screen.getByText('Description');
      expect(description).toHaveClass('text-sm');
    });
  });

  describe('CardContent', () => {
    it('should render content with padding', () => {
      render(
        <Card>
          <CardContent>Content Area</CardContent>
        </Card>
      );
      const content = screen.getByText('Content Area');
      expect(content).toHaveClass('p-6', 'pt-0');
    });

    it('should not have top padding when inside header', () => {
      render(
        <Card>
          <CardContent>No Top Padding</CardContent>
        </Card>
      );
      const content = screen.getByText('No Top Padding');
      expect(content).toHaveClass('pt-0');
    });
  });

  describe('CardFooter', () => {
    it('should render footer with proper alignment', () => {
      render(
        <Card>
          <CardFooter>Footer Content</CardFooter>
        </Card>
      );
      const footer = screen.getByText('Footer Content');
      expect(footer.parentElement).toHaveClass('flex', 'items-center');
    });

    it('should have proper padding', () => {
      render(
        <Card>
          <CardFooter>Footer</CardFooter>
        </Card>
      );
      const footer = screen.getByText('Footer');
      expect(footer.parentElement).toHaveClass('p-6', 'pt-0');
    });
  });

  describe('Combined Usage', () => {
    it('should render complete card with all components', () => {
      render(
        <Card className="test-card">
          <CardHeader>
            <CardTitle>Test Title</CardTitle>
            <CardDescription>Test Description</CardDescription>
          </CardHeader>
          <CardContent>Test Content</CardContent>
          <CardFooter>Test Footer</CardFooter>
        </Card>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(screen.getByText('Test Footer')).toBeInTheDocument();
    });

    it('should maintain proper spacing between sections', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title</CardTitle>
          </CardHeader>
          <CardContent>Content</CardContent>
        </Card>
      );

      const header = screen.getByText('Title');
      expect(header.parentElement).toHaveClass('space-y-1.5');
    });
  });

  describe('Display Names', () => {
    it('Card should have correct displayName', () => {
      expect(Card.displayName).toBe('Card');
    });

    it('CardHeader should have correct displayName', () => {
      expect(CardHeader.displayName).toBe('CardHeader');
    });

    it('CardTitle should have correct displayName', () => {
      expect(CardTitle.displayName).toBe('CardTitle');
    });

    it('CardDescription should have correct displayName', () => {
      expect(CardDescription.displayName).toBe('CardDescription');
    });

    it('CardContent should have correct displayName', () => {
      expect(CardContent.displayName).toBe('CardContent');
    });

    it('CardFooter should have correct displayName', () => {
      expect(CardFooter.displayName).toBe('CardFooter');
    });
  });

  describe('HTML Structure', () => {
    it('Card should render div element', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card?.tagName).toBe('DIV');
    });

    it('CardTitle should render div element', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title</CardTitle>
          </CardHeader>
        </Card>
      );
      const title = screen.getByText('Title');
      expect(title.tagName).toBe('DIV');
    });

    it('CardDescription should render div element', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription>Description</CardDescription>
          </CardHeader>
        </Card>
      );
      const description = screen.getByText('Description');
      expect(description.tagName).toBe('DIV');
    });
  });
});
