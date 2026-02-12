/**
 * StepIndicator 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试 - 步骤指示器显示
 * 2. Props 传递测试 - currentStep, steps
 * 3. 样式测试 - 当前步骤高亮
 * 4. 空步骤处理测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StepIndicator } from '../StepIndicator';

describe('StepIndicator Component', () => {
  describe('Rendering', () => {
    it('should render with default steps', () => {
      render(<StepIndicator currentStep={0} />);

      // Check for default step titles
      expect(screen.getByText('基础信息')).toBeInTheDocument();
      expect(screen.getByText('调度配置')).toBeInTheDocument();
      expect(screen.getByText('确认')).toBeInTheDocument();
    });

    it('should render custom steps', () => {
      const customSteps = [
        { id: 0, title: '步骤一', type: 'basic' as const },
        { id: 1, title: '步骤二', type: 'schedule' as const },
        { id: 2, title: '步骤三', type: 'confirm' as const },
      ];

      render(<StepIndicator currentStep={0} steps={customSteps} />);

      expect(screen.getByText('步骤一')).toBeInTheDocument();
      expect(screen.getByText('步骤二')).toBeInTheDocument();
      expect(screen.getByText('步骤三')).toBeInTheDocument();
    });

    it('should render step numbers', () => {
      render(<StepIndicator currentStep={0} />);

      const stepNumbers = screen.getAllByText(/^[123]$/);
      expect(stepNumbers).toHaveLength(3);
    });

    it('should render connecting lines between steps', () => {
      const { container } = render(<StepIndicator currentStep={0} />);

      // Lines should be present (there should be 3 lines for 3 steps)
      const lines = container.querySelectorAll('.bg-muted, .bg-primary');
      expect(lines.length).toBeGreaterThan(0);
    });
  });

  describe('Step Active State', () => {
    it('should highlight first step when currentStep is 0', () => {
      const { container } = render(<StepIndicator currentStep={0} />);

      // First step should be active (has bg-primary class)
      const stepElements = container.querySelectorAll('.rounded-full');
      expect(stepElements[0]).toHaveClass('bg-primary');
    });

    it('should highlight second step when currentStep is 1', () => {
      const { container } = render(<StepIndicator currentStep={1} />);

      const stepElements = container.querySelectorAll('.rounded-full');
      expect(stepElements[0]).toHaveClass('bg-primary'); // Previous step also highlighted
      expect(stepElements[1]).toHaveClass('bg-primary');
    });

    it('should highlight all steps when currentStep is last', () => {
      const { container } = render(<StepIndicator currentStep={2} />);

      const stepElements = container.querySelectorAll('.rounded-full');
      expect(stepElements[0]).toHaveClass('bg-primary');
      expect(stepElements[1]).toHaveClass('bg-primary');
      expect(stepElements[2]).toHaveClass('bg-primary');
    });

    it('should apply active style to step title when selected', () => {
      render(<StepIndicator currentStep={1} />);

      const basicInfoText = screen.getByText('基础信息');
      const scheduleText = screen.getByText('调度配置');

      expect(basicInfoText).toHaveClass('text-muted-foreground');
      expect(scheduleText).toHaveClass('text-foreground');
      expect(scheduleText).toHaveClass('font-medium');
    });
  });

  describe('Line Colors', () => {
    it('should color line as primary when step is reached', () => {
      const { container } = render(<StepIndicator currentStep={1} />);

      // First line should be primary colored
      const lines = container.querySelectorAll('div[class*="bg-"]');
      // The first line (between step 0 and 1) should be primary
      expect(lines[0]).toHaveClass('bg-primary');
    });

    it('should color line as muted when step is not reached', () => {
      const { container } = render(<StepIndicator currentStep={0} />);

      const lines = container.querySelectorAll('div[class*="bg-"]');
      // Lines after current step should be muted
      expect(lines[lines.length - 1]).toHaveClass('bg-muted');
    });
  });

  describe('Empty Steps', () => {
    it('should use default steps when empty array is passed', () => {
      render(<StepIndicator currentStep={0} steps={[]} />);

      // Should fall back to default steps
      expect(screen.getByText('基础信息')).toBeInTheDocument();
    });

    it('should render correctly with single step', () => {
      const singleStep = [{ id: 0, title: '唯一步骤', type: 'basic' as const }];
      render(<StepIndicator currentStep={0} steps={singleStep} />);

      expect(screen.getByText('唯一步骤')).toBeInTheDocument();
    });
  });

  describe('Step Type Handling', () => {
    it('should render steps with type property', () => {
      const stepsWithType = [
        { id: 0, title: 'Basic', type: 'basic' as const },
        { id: 1, title: 'Schedule', type: 'schedule' as const },
        { id: 2, title: 'Meds', type: 'medications' as const },
        { id: 3, title: 'Confirm', type: 'confirm' as const },
      ];

      render(<StepIndicator currentStep={0} steps={stepsWithType} />);

      expect(screen.getByText('Basic')).toBeInTheDocument();
      expect(screen.getByText('Schedule')).toBeInTheDocument();
      expect(screen.getByText('Meds')).toBeInTheDocument();
      expect(screen.getByText('Confirm')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have clickable step titles', () => {
      const { container } = render(<StepIndicator currentStep={0} />);

      const stepTitles = container.querySelectorAll('span.cursor-pointer');
      expect(stepTitles.length).toBe(3);
    });

    it('should have proper spacing between elements', () => {
      const { container } = render(<StepIndicator currentStep={0} />);

      // Check for gap classes
      const gapContainers = container.querySelectorAll('.gap-2, .gap-8');
      expect(gapContainers.length).toBeGreaterThan(0);
    });
  });
});
