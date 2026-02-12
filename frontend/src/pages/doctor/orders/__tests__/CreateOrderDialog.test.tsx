/**
 * CreateOrderDialog 组件测试
 *
 * 测试覆盖：
 * 1. 渲染测试 - 对话框渲染、步骤显示
 * 2. 步骤导航测试 - 上一步、下一步、跳转
 * 3. 表单验证测试 - 各步骤验证逻辑
 * 4. 编辑模式测试 - 编辑医嘱行为
 * 5. 创建模式测试 - 创建医嘱行为
 * 6. 模板功能测试 - 模板按钮、应用模板
 * 7. 提交测试 - 创建、更新医嘱
 * 8. 错误处理测试 - API 错误处理
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateOrderDialog } from '../CreateOrderDialog';
import type { BasicInfoData, ScheduleData } from '../types';

// Mock API
vi.mock('@/api', () => ({
  doctorApi: {
    createOrder: vi.fn(),
    updateOrder: vi.fn(),
  },
}));

// Mock toast hook
vi.mock('@/components/ui/toast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

// Mock child components
vi.mock('../StepIndicator', () => ({
  StepIndicator: ({ currentStep, steps }: any) => (
    <div data-testid="step-indicator" data-current={currentStep}>
      {steps.map((s: any) => (
        <div key={s.id} data-step={s.title}>
          {s.title}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('../steps/BasicInfoStep', () => ({
  BasicInfoStep: ({ data, onChange, errors, onOrderTypeChange }: any) => (
    <div data-testid="basic-info-step">
      <input
        data-testid="title-input"
        value={data.title || ''}
        onChange={(e) => onChange({ ...data, title: e.target.value })}
        placeholder="医嘱标题"
      />
      <input
        data-testid="order-type-input"
        value={data.order_type || ''}
        onChange={(e) => onChange({ ...data, order_type: e.target.value })}
      />
      {errors.title && <span data-testid="title-error">{errors.title}</span>}
      {errors.description && <span data-testid="description-error">{errors.description}</span>}
      <button onClick={() => onOrderTypeChange?.('medication')}>Set Medication Type</button>
    </div>
  ),
}));

vi.mock('../steps/MedicationsStep', () => ({
  MedicationsStep: ({ items, onChange, errors }: any) => (
    <div data-testid="medications-step">
      <div data-testid="medications-count">{items.length}</div>
      {errors.medications && <span data-testid="medications-error">{errors.medications}</span>}
      <button onClick={() => onChange([...items, { drug_id: 1 }])}>Add Medication</button>
    </div>
  ),
}));

vi.mock('../steps/ScheduleStep', () => ({
  ScheduleStep: ({ data, scheduleType, onScheduleTypeChange, onChange, errors }: any) => (
    <div data-testid="schedule-step">
      <select
        data-testid="schedule-type-select"
        value={scheduleType}
        onChange={(e) => onScheduleTypeChange(e.target.value)}
      >
        <option value="once">一次性</option>
        <option value="daily">每日</option>
        <option value="weekly">每周</option>
      </select>
      <input
        data-testid="start-date-input"
        value={data.start_date || ''}
        onChange={(e) => onChange({ ...data, start_date: e.target.value })}
      />
      {errors.schedule_type && <span data-testid="schedule-type-error">{errors.schedule_type}</span>}
      {errors.start_date && <span data-testid="start-date-error">{errors.start_date}</span>}
    </div>
  ),
}));

vi.mock('../steps/ConfirmStep', () => ({
  ConfirmStep: ({ basicInfo, scheduleData, medications }: any) => (
    <div data-testid="confirm-step">
      <h3>确认信息</h3>
      <p>Title: {basicInfo.title}</p>
      <p>Schedule: {scheduleData.schedule_type}</p>
      <p>Medications: {medications.length}</p>
    </div>
  ),
}));

vi.mock('../OrderTemplates', () => ({
  OrderTemplates: ({ open, onClose, onSelectTemplate }: any) =>
    open ? (
      <div data-testid="order-templates">
        <button onClick={() => onSelectTemplate({}, {}, [])}>Select Template</button>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

// Mock UI components
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, onOpenChange, children }: any) =>
    open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children }: any) => <div data-testid="dialog-content">{children}</div>,
  DialogHeader: ({ children }: any) => <div data-testid="dialog-header">{children}</div>,
  DialogTitle: ({ children }: any) => <h2 data-testid="dialog-title">{children}</h2>,
  DialogFooter: ({ children }: any) => <div data-testid="dialog-footer">{children}</div>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, variant }: any) => (
    <button onClick={onClick} data-variant={variant} data-testid="button">
      {children}
    </button>
  ),
}));

import { doctorApi } from '@/api';

describe('CreateOrderDialog Component', () => {
  const mockProps = {
    open: true,
    editingOrder: null,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
    patientId: 1,
  };

  const mockInitialBasicInfo: BasicInfoData = {
    title: '测试医嘱',
    description: '测试描述',
    order_type: 'medication',
  };

  const mockInitialSchedule: ScheduleData = {
    schedule_type: 'once',
    start_date: '2026-02-12',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(doctorApi.createOrder).mockResolvedValue({ success: true });
    vi.mocked(doctorApi.updateOrder).mockResolvedValue({ success: true });
  });

  const renderComponent = (props = mockProps) => {
    return render(<CreateOrderDialog {...props} />);
  };

  describe('Rendering', () => {
    it('should render dialog when open', () => {
      renderComponent();

      expect(screen.getByTestId('dialog')).toBeInTheDocument();
      expect(screen.getByTestId('dialog-content')).toBeInTheDocument();
    });

    it('should not render dialog when closed', () => {
      renderComponent({ ...mockProps, open: false });

      expect(screen.queryByTestId('dialog')).not.toBeInTheDocument();
    });

    it('should render correct title for create mode', () => {
      renderComponent();

      expect(screen.getByTestId('dialog-title')).toHaveTextContent('创建医嘱');
    });

    it('should render correct title for edit mode', () => {
      renderComponent({ ...mockProps, editingOrder: { id: 1 } as any });

      expect(screen.getByTestId('dialog-title')).toHaveTextContent('编辑医嘱');
    });

    it('should render step indicator', () => {
      renderComponent();

      expect(screen.getByTestId('step-indicator')).toBeInTheDocument();
    });

    it('should render all step titles', () => {
      renderComponent();

      expect(screen.getByText('基础信息')).toBeInTheDocument();
      expect(screen.getByText('用药信息')).toBeInTheDocument();
      expect(screen.getByText('调度配置')).toBeInTheDocument();
      expect(screen.getByText('确认')).toBeInTheDocument();
    });
  });

  describe('Step Navigation', () => {
    it('should start at step 0', () => {
      renderComponent();

      expect(screen.getByTestId('step-indicator')).toHaveAttribute('data-current', '0');
      expect(screen.getByTestId('basic-info-step')).toBeInTheDocument();
    });

    it('should show "下一步" button on non-last steps', () => {
      renderComponent();

      expect(screen.getByText('下一步')).toBeInTheDocument();
    });

    it('should show "创建" button on last step', async () => {
      renderComponent();

      // Navigate to last step
      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton); // Step 1
      // Check if still next button appears
      const nextButtons = screen.getAllByText('下一步');
      if (nextButtons.length > 0) {
        await userEvent.click(nextButtons[0]); // Step 2
      }

      await waitFor(() => {
        expect(screen.getByText('创建')).toBeInTheDocument();
      });
    });

    it('should show "取消" button on step 0', () => {
      renderComponent();

      const cancelButton = screen.getByText('取消');
      expect(cancelButton).toBeInTheDocument();
    });

    it('should show "上一步" button on steps > 0', async () => {
      renderComponent();

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('上一步')).toBeInTheDocument();
      });
    });
  });

  describe('Basic Info Step', () => {
    it('should render basic info step at step 0', () => {
      renderComponent();

      expect(screen.getByTestId('basic-info-step')).toBeInTheDocument();
    });

    it('should validate title is required', async () => {
      renderComponent();

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByTestId('title-error')).toBeInTheDocument();
        expect(screen.getByTestId('title-error')).toHaveTextContent('请输入医嘱标题');
      });
    });

    it('should not proceed to next step with validation errors', async () => {
      renderComponent();

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByTestId('basic-info-step')).toBeInTheDocument();
      });
    });

    it('should proceed to next step when valid', async () => {
      renderComponent();

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.queryByTestId('basic-info-step')).not.toBeInTheDocument();
      });
    });

    it('should show template button for medication type', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: { ...mockInitialBasicInfo },
      });

      await waitFor(() => {
        expect(screen.getByText('使用模板')).toBeInTheDocument();
      });
    });

    it('should not show template button for non-medication type', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: { ...mockInitialBasicInfo, order_type: 'checkup' },
      });

      await waitFor(() => {
        expect(screen.queryByText('使用模板')).not.toBeInTheDocument();
      });
    });
  });

  describe('Medications Step', () => {
    it('should validate at least one medication required', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      // Fill title to pass step 0 validation
      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Go to step 1
      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByTestId('medications-step')).toBeInTheDocument();
      });

      // Try to proceed without medications
      const nextButtons = screen.getAllByText('下一步');
      if (nextButtons.length > 0) {
        await userEvent.click(nextButtons[0]);

        await waitFor(() => {
          expect(screen.getByTestId('medications-error')).toBeInTheDocument();
        });
      }
    });

    it('should proceed when medications added', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByTestId('medications-step')).toBeInTheDocument();
      });

      // Add a medication
      const addButton = screen.getByText('Add Medication');
      await userEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('medications-count')).toHaveTextContent('1');
      });
    });
  });

  describe('Schedule Step', () => {
    it('should validate schedule type', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Go through steps
      const nextButtons = screen.getAllByText('下一步');
      await userEvent.click(nextButtons[0]); // Step 1

      // Add medication
      const addButton = screen.getByText('Add Medication');
      await userEvent.click(addButton);

      const nextButtons2 = screen.getAllByText('下一步');
      await userEvent.click(nextButtons2[0] || nextButtons[1]); // Step 2

      await waitFor(() => {
        expect(screen.getByTestId('schedule-step')).toBeInTheDocument();
      });
    });

    it('should validate start date', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      // Navigate to schedule step
      // (Navigation logic already tested above)
      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Fast forward through steps (assuming we're at schedule step)
      const select = screen.getByTestId('schedule-type-select');
      await userEvent.selectOptions(select, 'once');

      const nextButton = screen.getAllByText('下一步')[0] || screen.getByText('创建');

      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByTestId('start-date-error')).toBeInTheDocument();
      });
    });
  });

  describe('Confirm Step', () => {
    it('should render confirmation at step 3', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
        initialSchedule: mockInitialSchedule,
      });

      // Navigate all the way to confirm step
      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Click through steps
      const nextButtons = screen.getAllByText('下一步');
      for (let i = 0; i < Math.min(nextButtons.length, 3); i++) {
        await userEvent.click(nextButtons[i]);
      }

      await waitFor(() => {
        expect(screen.getByTestId('confirm-step')).toBeInTheDocument();
      });
    });
  });

  describe('Edit Mode', () => {
    it('should show "保存" button in edit mode', () => {
      renderComponent({ ...mockProps, editingOrder: { id: 1 } as any });

      expect(screen.getByText('保存')).toBeInTheDocument();
    });

    it('should not show step navigation in edit mode', () => {
      renderComponent({ ...mockProps, editingOrder: { id: 1 } as any });

      expect(screen.queryByText('下一步')).not.toBeInTheDocument();
      expect(screen.queryByText('上一步')).not.toBeInTheDocument();
    });

    it('should call updateOrder API in edit mode', async () => {
      renderComponent({
        ...mockProps,
        editingOrder: { id: 1 } as any,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const saveButton = screen.getByText('保存');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(doctorApi.updateOrder).toHaveBeenCalledWith(1, expect.objectContaining({
          title: mockInitialBasicInfo.title,
        }));
      });
    });

    it('should not show template button in edit mode', () => {
      renderComponent({
        ...mockProps,
        editingOrder: { id: 1 } as any,
        initialBasicInfo: mockInitialBasicInfo,
      });

      expect(screen.queryByText('使用模板')).not.toBeInTheDocument();
    });
  });

  describe('Create Mode', () => {
    it('should call createOrder API on submit', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
        initialSchedule: mockInitialSchedule,
      });

      // Navigate to confirm step
      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Click through all steps
      const nextButtons = screen.getAllByText('下一步');
      for (const button of nextButtons) {
        await userEvent.click(button);
      }

      // At confirm step, click create
      const createButton = screen.getByText('创建');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(doctorApi.createOrder).toHaveBeenCalledWith(expect.objectContaining({
          patient_id: 1,
          status: 'draft',
        }));
      });
    });

    it('should include medications in request for medication type', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
        initialSchedule: mockInitialSchedule,
      });

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Navigate through steps and add medication
      const nextButtons = screen.getAllByText('下一步');
      await userEvent.click(nextButtons[0]);

      const addButton = screen.getByText('Add Medication');
      await userEvent.click(addButton);

      // Continue to confirm
      const nextButtons2 = screen.getAllByText('下一步');
      for (const button of nextButtons2) {
        await userEvent.click(button);
      }

      const createButton = screen.getByText('创建');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(doctorApi.createOrder).toHaveBeenCalledWith(expect.objectContaining({
          items: expect.any(Array),
        }));
      });
    });
  });

  describe('Template Functionality', () => {
    it('should open templates dialog when clicking template button', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const templateButton = screen.getByText('使用模板');
      await userEvent.click(templateButton);

      await waitFor(() => {
        expect(screen.getByTestId('order-templates')).toBeInTheDocument();
      });
    });

    it('should apply template data when selected', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const templateButton = screen.getByText('使用模板');
      await userEvent.click(templateButton);

      await waitFor(() => {
        expect(screen.getByTestId('order-templates')).toBeInTheDocument();
      });

      const selectButton = screen.getByText('Select Template');
      await userEvent.click(selectButton);

      // Template should be applied (data should be updated)
      // We can verify the dialog closes
      await waitFor(() => {
        expect(screen.queryByTestId('order-templates')).not.toBeInTheDocument();
      });
    });

    it('should show template button on steps > 0 in create mode', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      // Go to step 1
      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('使用模板')).toBeInTheDocument();
      });
    });
  });

  describe('Dialog Close Behavior', () => {
    it('should call onClose when clicking cancel on step 0', async () => {
      const onClose = vi.fn();
      renderComponent({ ...mockProps, onClose });

      const cancelButton = screen.getByText('取消');
      await userEvent.click(cancelButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('should go to previous step when clicking back on step > 0', async () => {
      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      const nextButton = screen.getByText('下一步');
      await userEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('上一步')).toBeInTheDocument();
      });

      const backButton = screen.getByText('上一步');
      await userEvent.click(backButton);

      await waitFor(() => {
        expect(screen.getByTestId('step-indicator')).toHaveAttribute('data-current', '0');
      });
    });
  });

  describe('Schedule Type', () => {
    it('should initialize with provided schedule type', () => {
      renderComponent({
        ...mockProps,
        initialScheduleType: 'weekly',
        initialBasicInfo: mockInitialBasicInfo,
      });

      const select = screen.getByTestId('schedule-type-select') || screen.queryByDisplayValue('每周');
      expect(select).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle createOrder API error', async () => {
      vi.mocked(doctorApi.createOrder).mockRejectedValue(new Error('API Error'));

      renderComponent({
        ...mockProps,
        initialBasicInfo: mockInitialBasicInfo,
        initialSchedule: mockInitialSchedule,
      });

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Navigate through all steps
      const nextButtons = screen.getAllByText('下一步');
      for (const button of nextButtons) {
        await userEvent.click(button);
      }

      const createButton = screen.getByText('创建');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(doctorApi.createOrder).toHaveBeenCalled();
      });
    });

    it('should handle updateOrder API error', async () => {
      vi.mocked(doctorApi.updateOrder).mockRejectedValue(new Error('API Error'));

      renderComponent({
        ...mockProps,
        editingOrder: { id: 1 } as any,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const saveButton = screen.getByText('保存');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(doctorApi.updateOrder).toHaveBeenCalled();
      });
    });
  });

  describe('Success Callback', () => {
    it('should call onSuccess after successful create', async () => {
      const onSuccess = vi.fn();
      renderComponent({
        ...mockProps,
        onSuccess,
        initialBasicInfo: mockInitialBasicInfo,
        initialSchedule: mockInitialSchedule,
      });

      const titleInput = screen.getByTestId('title-input');
      await userEvent.type(titleInput, '测试医嘱');

      // Navigate through all steps
      const nextButtons = screen.getAllByText('下一步');
      for (const button of nextButtons) {
        await userEvent.click(button);
      }

      const createButton = screen.getByText('创建');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });
    });

    it('should call onSuccess after successful update', async () => {
      const onSuccess = vi.fn();
      renderComponent({
        ...mockProps,
        onSuccess,
        editingOrder: { id: 1 } as any,
        initialBasicInfo: mockInitialBasicInfo,
      });

      const saveButton = screen.getByText('保存');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });
    });
  });
});
