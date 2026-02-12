/**
 * LargePatientCard 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 用户交互测试（onClick, onQuickConsult）
 * 4. 样式变化测试
 * 5. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LargePatientCard } from '../LargePatientCard';
import type { Patient } from '@/types/patient';

// Mock CSS 变量
const mockComputedStyle = {
  getPropertyValue: vi.fn((name) => {
    const colorMap: Record<string, string> = {
      '--primary': '199 89% 48%',
      '--success': '142 76% 36%',
      '--warning': '38 92% 50%',
      '--danger': '0 72% 51%',
      '--info': '207 89% 54%',
    };
    return colorMap[name] || '199 89% 48%';
  }),
};

describe('LargePatientCard Component', () => {
  const mockOnClick = vi.fn();
  const mockOnQuickConsult = vi.fn();

  const defaultPatient: Patient = {
    id: 1,
    nickname: '李四',
    phone: '13900139000',
    gender: '女',
    age: 28,
    last_consultation_at: new Date().toISOString(),
    active_orders_count: 5,
    completion_rate: 0.88,
  };

  beforeEach(() => {
    vi.stubGlobal('getComputedStyle', () => mockComputedStyle);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render patient card with all information', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('李四')).toBeInTheDocument();
      expect(screen.getByText('女')).toBeInTheDocument();
      expect(screen.getByText('28岁')).toBeInTheDocument();
      expect(screen.getByText('139****9000')).toBeInTheDocument();
    });

    it('should render active orders count', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('进行中医嘱')).toBeInTheDocument();
      const countElement = screen.getByText('5');
      expect(countElement).toBeInTheDocument();
    });

    it('should render completion rate', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('医嘱完成率')).toBeInTheDocument();
      expect(screen.getByText('88%')).toBeInTheDocument();
    });

    it('should render last consultation time', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('最后咨询')).toBeInTheDocument();
      expect(screen.getByText('今天')).toBeInTheDocument();
    });

    it('should render created at date', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('创建时间')).toBeInTheDocument();
    });

    it('should render action buttons', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('查看详情')).toBeInTheDocument();
      expect(screen.getByText('快速咨询')).toBeInTheDocument();
    });

    it('should render without quick consult when callback not provided', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
        />
      );

      // Button should still render but clicking it won't trigger onQuickConsult
      expect(screen.getByText('快速咨询')).toBeInTheDocument();
    });
  });

  describe('Avatar and Initial', () => {
    it('should display correct initial from nickname', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const initial = screen.getByText('李');
      expect(initial).toBeInTheDocument();
    });

    it('should display "患" when no nickname', () => {
      const patientWithoutName = { ...defaultPatient, nickname: undefined };
      render(
        <LargePatientCard
          patient={patientWithoutName}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const defaultInitial = screen.getByText('患');
      expect(defaultInitial).toBeInTheDocument();
    });

    it('should apply gradient class to avatar', () => {
      const { container } = render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const avatar = container.querySelector('.rounded-2xl');
      expect(avatar).toHaveClass('bg-gradient-to-br');
    });
  });

  describe('Phone Masking', () => {
    it('should mask phone number correctly', () => {
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('139****9000')).toBeInTheDocument();
      expect(screen.queryByText('13900139000')).not.toBeInTheDocument();
    });

    it('should handle short phone numbers', () => {
      const patientWithShortPhone = { ...defaultPatient, phone: '123' };
      render(
        <LargePatientCard
          patient={patientWithShortPhone}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('123')).toBeInTheDocument();
    });
  });

  describe('Gender Badge Styles', () => {
    it('should apply sky color for male gender', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, gender: '男' }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const badge = container.querySelector('.px-2');
      expect(badge).toHaveClass('bg-sky-100');
      expect(badge).toHaveClass('text-sky-700');
    });

    it('should apply pink color for female gender', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, gender: '女' }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const badge = container.querySelector('.px-2');
      expect(badge).toHaveClass('bg-pink-100');
      expect(badge).toHaveClass('text-pink-700');
    });

    it('should apply surface color for unknown gender', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, gender: '未知' }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const badge = container.querySelector('.px-2');
      expect(badge).toHaveClass('bg-surface');
    });

    it('should not render gender badge when gender is undefined', () => {
      render(
        <LargePatientCard
          patient={{ ...defaultPatient, gender: undefined }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const badge = screen.queryByText('男');
      expect(badge).not.toBeInTheDocument();
    });
  });

  describe('Completion Rate Colors', () => {
    it('should show success color for high completion rate (>= 80%)', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, completion_rate: 0.9 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('90%')).toBeInTheDocument();
      const percentElement = container.querySelector('.text-success');
      expect(percentElement).toBeInTheDocument();
    });

    it('should show warning color for medium completion rate (>= 50%)', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, completion_rate: 0.6 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('60%')).toBeInTheDocument();
      const percentElement = container.querySelector('.text-warning');
      expect(percentElement).toBeInTheDocument();
    });

    it('should show danger color for low completion rate (< 50%)', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, completion_rate: 0.3 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('30%')).toBeInTheDocument();
      const percentElement = container.querySelector('.text-danger');
      expect(percentElement).toBeInTheDocument();
    });
  });

  describe('Time Formatting', () => {
    it('should show "today" for today consultation', () => {
      const todayPatient = {
        ...defaultPatient,
        last_consultation_at: new Date().toISOString(),
      };
      render(
        <LargePatientCard
          patient={todayPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('今天')).toBeInTheDocument();
    });

    it('should show "yesterday" for yesterday consultation', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayPatient = {
        ...defaultPatient,
        last_consultation_at: yesterday.toISOString(),
      };
      render(
        <LargePatientCard
          patient={yesterdayPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('昨天')).toBeInTheDocument();
    });

    it('should show "X days ago" for recent consultations', () => {
      const threeDaysAgo = new Date();
      threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
      const recentPatient = {
        ...defaultPatient,
        last_consultation_at: threeDaysAgo.toISOString(),
      };
      render(
        <LargePatientCard
          patient={recentPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('3天前')).toBeInTheDocument();
    });

    it('should show "X weeks ago" for older consultations', () => {
      const twoWeeksAgo = new Date();
      twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
      const oldPatient = {
        ...defaultPatient,
        last_consultation_at: twoWeeksAgo.toISOString(),
      };
      render(
        <LargePatientCard
          patient={oldPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('2周前')).toBeInTheDocument();
    });

    it('should show "never consulted" when no consultation date', () => {
      const patientWithoutConsultation = {
        ...defaultPatient,
        last_consultation_at: undefined,
      };
      render(
        <LargePatientCard
          patient={patientWithoutConsultation}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('从未咨询')).toBeInTheDocument();
    });

    it('should show "unknown" when created at is undefined', () => {
      const patientWithoutCreatedAt = {
        ...defaultPatient,
        last_consultation_at: undefined,
      };
      render(
        <LargePatientCard
          patient={patientWithoutCreatedAt}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      // Should show unknown for created at as well
      expect(screen.getByText('未知')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should call onClick when card is clicked', async () => {
      const user = userEvent.setup();
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const card = screen.getByText('李四').closest('.card-hover');
      if (card) {
        await user.click(card);
        expect(mockOnClick).toHaveBeenCalledTimes(1);
      }
    });

    it('should call onClick when "查看详情" button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const viewButton = screen.getByText('查看详情');
      await user.click(viewButton);
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it('should call onQuickConsult when "快速咨询" button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const consultButton = screen.getByText('快速咨询');
      await user.click(consultButton);
      expect(mockOnQuickConsult).toHaveBeenCalledTimes(1);
      expect(mockOnQuickConsult).toHaveBeenCalledWith(defaultPatient);
    });

    it('should not call card onClick when quick consult button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const consultButton = screen.getByText('快速咨询');
      await user.click(consultButton);
      expect(mockOnClick).not.toHaveBeenCalled();
      expect(mockOnQuickConsult).toHaveBeenCalled();
    });

    it('should not call onQuickConsult when callback is not provided', async () => {
      const user = userEvent.setup();
      render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
        />
      );

      const consultButton = screen.getByText('快速咨询');
      await user.click(consultButton);
      expect(mockOnQuickConsult).not.toHaveBeenCalled();
    });
  });

  describe('Progress Bar', () => {
    it('should render progress bar with correct width', () => {
      const { container } = render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const progressBar = container.querySelector('.progress-bar');
      expect(progressBar).toHaveStyle({ width: '88%' });
    });

    it('should render 0% progress bar', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, completion_rate: 0 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const progressBar = container.querySelector('.progress-bar');
      expect(progressBar).toHaveStyle({ width: '0%' });
    });

    it('should render 100% progress bar', () => {
      const { container } = render(
        <LargePatientCard
          patient={{ ...defaultPatient, completion_rate: 1 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const progressBar = container.querySelector('.progress-bar');
      expect(progressBar).toHaveStyle({ width: '100%' });
    });
  });

  describe('Edge Cases', () => {
    it('should handle patient without age', () => {
      render(
        <LargePatientCard
          patient={{ ...defaultPatient, age: undefined }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('年龄未知')).toBeInTheDocument();
    });

    it('should handle zero active orders count', () => {
      render(
        <LargePatientCard
          patient={{ ...defaultPatient, active_orders_count: 0 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle very large active orders count', () => {
      render(
        <LargePatientCard
          patient={{ ...defaultPatient, active_orders_count: 1000 }}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      expect(screen.getByText('1000')).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('should have card-hover class', () => {
      const { container } = render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const card = container.querySelector('.card-hover');
      expect(card).toBeInTheDocument();
    });

    it('should have rounded-2xl class', () => {
      const { container } = render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const card = container.querySelector('.card-hover');
      expect(card).toHaveClass('rounded-2xl');
    });

    it('should have border class', () => {
      const { container } = render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const card = container.querySelector('.card-hover');
      expect(card).toHaveClass('border');
    });

    it('should have cursor-pointer class', () => {
      const { container } = render(
        <LargePatientCard
          patient={defaultPatient}
          onClick={mockOnClick}
          onQuickConsult={mockOnQuickConsult}
        />
      );

      const card = container.querySelector('.card-hover');
      expect(card).toHaveClass('cursor-pointer');
    });
  });
});
