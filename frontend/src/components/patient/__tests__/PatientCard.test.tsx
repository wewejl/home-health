/**
 * PatientCard 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 用户交互测试
 * 4. 样式变化测试
 * 5. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PatientCard, type Patient } from '../PatientCard';

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

describe('PatientCard Component', () => {
  const mockOnClick = vi.fn();

  const defaultPatient: Patient = {
    id: 1,
    nickname: '张三',
    phone: '13800138000',
    gender: '男',
    age: 35,
    last_consultation_at: new Date().toISOString(),
    active_orders_count: 3,
    completion_rate: 0.75,
  };

  beforeEach(() => {
    // Mock getComputedStyle
    vi.stubGlobal('getComputedStyle', () => mockComputedStyle);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render patient card with all information', () => {
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      expect(screen.getByText('张三')).toBeInTheDocument();
      expect(screen.getByText('男')).toBeInTheDocument();
      expect(screen.getByText('35岁')).toBeInTheDocument();
      expect(screen.getByText('138****8000')).toBeInTheDocument();
    });

    it('should render patient without nickname', () => {
      const patientWithoutName = { ...defaultPatient, nickname: undefined };
      render(<PatientCard patient={patientWithoutName} onClick={mockOnClick} />);

      expect(screen.getByText('未设置姓名')).toBeInTheDocument();
    });

    it('should render patient without age', () => {
      const patientWithoutAge = { ...defaultPatient, age: undefined };
      render(<PatientCard patient={patientWithoutAge} onClick={mockOnClick} />);

      expect(screen.getByText('未填写年龄')).toBeInTheDocument();
    });

    it('should render patient without gender', () => {
      const patientWithoutGender = { ...defaultPatient, gender: undefined };
      render(<PatientCard patient={patientWithoutGender} onClick={mockOnClick} />);

      // Gender badge should not be rendered when gender is undefined
      expect(screen.queryByText('男')).not.toBeInTheDocument();
      expect(screen.queryByText('女')).not.toBeInTheDocument();
    });

    it('should render active orders count', () => {
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      expect(screen.getByText('进行中医嘱')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should render completion rate', () => {
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      expect(screen.getByText('完成率')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should render last consultation time', () => {
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      expect(screen.getByText('最后咨询')).toBeInTheDocument();
      expect(screen.getByText('今天')).toBeInTheDocument();
    });

    it('should render "never consulted" when no consultation date', () => {
      const patientWithoutConsultation = { ...defaultPatient, last_consultation_at: undefined };
      render(<PatientCard patient={patientWithoutConsultation} onClick={mockOnClick} />);

      expect(screen.getByText('从未咨询')).toBeInTheDocument();
    });
  });

  describe('Avatar and Gradient', () => {
    it('should display correct initial from nickname', () => {
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      const initial = screen.getByText('张');
      expect(initial).toBeInTheDocument();
    });

    it('should display question mark when no nickname', () => {
      const patientWithoutName = { ...defaultPatient, nickname: undefined };
      render(<PatientCard patient={patientWithoutName} onClick={mockOnClick} />);

      const questionMark = screen.getByText('?');
      expect(questionMark).toBeInTheDocument();
    });

    it('should apply gradient class to avatar', () => {
      const { container } = render(
        <PatientCard patient={defaultPatient} onClick={mockOnClick} />
      );

      const avatar = container.querySelector('.rounded-full');
      expect(avatar).toHaveClass('bg-gradient-to-br');
    });
  });

  describe('Phone Masking', () => {
    it('should mask phone number correctly', () => {
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      expect(screen.getByText('138****8000')).toBeInTheDocument();
      expect(screen.queryByText('13800138000')).not.toBeInTheDocument();
    });

    it('should handle short phone numbers', () => {
      const patientWithShortPhone = { ...defaultPatient, phone: '12345' };
      render(<PatientCard patient={patientWithShortPhone} onClick={mockOnClick} />);

      // Short numbers (< 7 chars) should be displayed as-is
      expect(screen.getByText('12345')).toBeInTheDocument();
    });

    it('should handle empty phone number', () => {
      const patientWithEmptyPhone = { ...defaultPatient, phone: '' };
      render(<PatientCard patient={patientWithEmptyPhone} onClick={mockOnClick} />);

      // Empty phone number should not display any masked number
      expect(screen.queryByText(/\d{4}\*\*\*\d{4}/)).not.toBeInTheDocument();
    });
  });

  describe('Gender Badge Styles', () => {
    it('should render badge for male gender', () => {
      const { container } = render(
        <PatientCard patient={{ ...defaultPatient, gender: '男' }} onClick={mockOnClick} />
      );

      const badge = screen.getByText('男');
      expect(badge).toBeInTheDocument();
    });

    it('should render badge for female gender', () => {
      const { container } = render(
        <PatientCard patient={{ ...defaultPatient, gender: '女' }} onClick={mockOnClick} />
      );

      const badge = screen.getByText('女');
      expect(badge).toBeInTheDocument();
    });

    it('should render badge for other gender', () => {
      render(
        <PatientCard patient={{ ...defaultPatient, gender: '未知' }} onClick={mockOnClick} />
      );

      const badge = screen.getByText('未知');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Completion Rate Colors', () => {
    it('should show success color for high completion rate (>= 80%)', () => {
      const patientWithHighRate = { ...defaultPatient, completion_rate: 0.85 };
      const { container } = render(
        <PatientCard patient={patientWithHighRate} onClick={mockOnClick} />
      );

      expect(screen.getByText('85%')).toBeInTheDocument();
      const percentElement = container.querySelector('.text-success');
      expect(percentElement).toBeInTheDocument();
    });

    it('should show warning color for medium completion rate (>= 50%)', () => {
      const patientWithMediumRate = { ...defaultPatient, completion_rate: 0.65 };
      const { container } = render(
        <PatientCard patient={patientWithMediumRate} onClick={mockOnClick} />
      );

      expect(screen.getByText('65%')).toBeInTheDocument();
      const percentElement = container.querySelector('.text-warning');
      expect(percentElement).toBeInTheDocument();
    });

    it('should show danger color for low completion rate (< 50%)', () => {
      const patientWithLowRate = { ...defaultPatient, completion_rate: 0.35 };
      const { container } = render(
        <PatientCard patient={patientWithLowRate} onClick={mockOnClick} />
      );

      expect(screen.getByText('35%')).toBeInTheDocument();
      const percentElement = container.querySelector('.text-danger');
      expect(percentElement).toBeInTheDocument();
    });

    it('should round completion percentage correctly', () => {
      const patientWithDecimalRate = { ...defaultPatient, completion_rate: 0.765 };
      render(<PatientCard patient={patientWithDecimalRate} onClick={mockOnClick} />);

      expect(screen.getByText('77%')).toBeInTheDocument();
    });
  });

  describe('Last Consultation Time Formatting', () => {
    it('should show "today" for today consultation', () => {
      const todayPatient = {
        ...defaultPatient,
        last_consultation_at: new Date().toISOString(),
      };
      render(<PatientCard patient={todayPatient} onClick={mockOnClick} />);

      expect(screen.getByText('今天')).toBeInTheDocument();
    });

    it('should show "yesterday" for yesterday consultation', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayPatient = {
        ...defaultPatient,
        last_consultation_at: yesterday.toISOString(),
      };
      render(<PatientCard patient={yesterdayPatient} onClick={mockOnClick} />);

      expect(screen.getByText('昨天')).toBeInTheDocument();
    });

    it('should show "X days ago" for recent consultations', () => {
      const threeDaysAgo = new Date();
      threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
      const recentPatient = {
        ...defaultPatient,
        last_consultation_at: threeDaysAgo.toISOString(),
      };
      render(<PatientCard patient={recentPatient} onClick={mockOnClick} />);

      expect(screen.getByText('3天前')).toBeInTheDocument();
    });

    it('should show "X weeks ago" for older consultations', () => {
      const twoWeeksAgo = new Date();
      twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
      const oldPatient = {
        ...defaultPatient,
        last_consultation_at: twoWeeksAgo.toISOString(),
      };
      render(<PatientCard patient={oldPatient} onClick={mockOnClick} />);

      expect(screen.getByText('2周前')).toBeInTheDocument();
    });

    it('should show formatted date for very old consultations', () => {
      const oldDate = new Date('2024-01-15');
      const veryOldPatient = {
        ...defaultPatient,
        last_consultation_at: oldDate.toISOString(),
      };
      render(<PatientCard patient={veryOldPatient} onClick={mockOnClick} />);

      // Should show formatted date like "1月15日"
      expect(screen.getByText(/1月/)).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should call onClick when card is clicked', async () => {
      const user = userEvent.setup();
      render(<PatientCard patient={defaultPatient} onClick={mockOnClick} />);

      const card = screen.getByText('张三').closest('.patient-card');
      if (card) {
        await user.click(card);
        expect(mockOnClick).toHaveBeenCalledTimes(1);
      }
    });

    it('should have cursor-pointer class', () => {
      const { container } = render(
        <PatientCard patient={defaultPatient} onClick={mockOnClick} />
      );

      const card = container.querySelector('.patient-card');
      expect(card).toHaveClass('cursor-pointer');
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero active orders count', () => {
      const patientWithNoOrders = { ...defaultPatient, active_orders_count: 0 };
      render(<PatientCard patient={patientWithNoOrders} onClick={mockOnClick} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle zero completion rate', () => {
      const patientWithZeroRate = { ...defaultPatient, completion_rate: 0 };
      render(<PatientCard patient={patientWithZeroRate} onClick={mockOnClick} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle 100% completion rate', () => {
      const patientWithFullRate = { ...defaultPatient, completion_rate: 1 };
      render(<PatientCard patient={patientWithFullRate} onClick={mockOnClick} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should handle very large active orders count', () => {
      const patientWithManyOrders = { ...defaultPatient, active_orders_count: 999 };
      render(<PatientCard patient={patientWithManyOrders} onClick={mockOnClick} />);

      expect(screen.getByText('999')).toBeInTheDocument();
    });

    it('should handle special characters in nickname', () => {
      const patientWithSpecialName = {
        ...defaultPatient,
        nickname: '张三-测试',
      };
      render(<PatientCard patient={patientWithSpecialName} onClick={mockOnClick} />);

      expect(screen.getByText('张三-测试')).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('should render card component', () => {
      const { container } = render(
        <PatientCard patient={defaultPatient} onClick={mockOnClick} />
      );

      const card = container.querySelector('.patient-card');
      expect(card).toBeInTheDocument();
    });

    it('should have group class for hover effects', () => {
      const { container } = render(
        <PatientCard patient={defaultPatient} onClick={mockOnClick} />
      );

      const card = container.querySelector('.patient-card');
      expect(card).toHaveClass('group');
    });

    it('should have overflow-hidden class', () => {
      const { container } = render(
        <PatientCard patient={defaultPatient} onClick={mockOnClick} />
      );

      const card = container.querySelector('.patient-card');
      expect(card).toHaveClass('overflow-hidden');
    });
  });
});
