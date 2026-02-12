/* eslint-disable react-hooks/rules-of-hooks */
import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { doctorApi } from '@/api';
import type { MedicalOrder, BasicInfoData, ScheduleData, ScheduleType, FormErrors, OrderItem, StepType } from './types';

// 将 FormErrors 转换为 Record 类型以避免类型错误
const formErrorsToRecord = (errors: FormErrors): Record<string, string> => {
  return Object.fromEntries(
    Object.entries(errors).filter(([_, v]) => v !== undefined)
  ) as Record<string, string>;
};
import { StepIndicator } from './StepIndicator';
import { BasicInfoStep } from './steps/BasicInfoStep';
import { ScheduleStep } from './steps/ScheduleStep';
import { MedicationsStep } from './steps/MedicationsStep';
import { ConfirmStep } from './steps/ConfirmStep';
import { OrderTemplates } from './OrderTemplates';
import { FileText, Copy } from 'lucide-react';

interface CreateOrderDialogProps {
  open: boolean;
  editingOrder: MedicalOrder | null;
  onClose: () => void;
  onSuccess: () => void;
  patientId: number;
  initialBasicInfo?: BasicInfoData;
  initialSchedule?: ScheduleData;
  initialScheduleType?: ScheduleType;
}

export const CreateOrderDialog = ({
  open,
  editingOrder,
  onClose,
  onSuccess,
  patientId,
  initialBasicInfo,
  initialSchedule,
  initialScheduleType = 'once',
}: CreateOrderDialogProps) => {
  const toast = useToast();
  const [currentStep, setCurrentStep] = useState(0);
  const [scheduleType, setScheduleType] = useState<ScheduleType>(initialScheduleType);
  const [basicInfoData, setBasicInfoData] = useState<BasicInfoData>(initialBasicInfo || {});
  const [scheduleData, setScheduleData] = useState<ScheduleData>(initialSchedule || {});
  const [medicationsData, setMedicationsData] = useState<OrderItem[]>([]);
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // 模板对话框状态
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [showTemplateBtn, setShowTemplateBtn] = useState(false);

  // 步骤定义
  const steps = [
    { id: 0, title: '基础信息', type: 'basic' as StepType },
    { id: 1, title: '用药信息', type: 'medications' as StepType },
    { id: 2, title: '调度配置', type: 'schedule' as StepType },
    { id: 3, title: '确认', type: 'confirm' as StepType },
  ];

  // 当对话框打开或编辑数据改变时，重置表单状态
  useEffect(() => {
    if (open) {
      setCurrentStep(0);
      setScheduleType(initialScheduleType);
      setBasicInfoData(initialBasicInfo || {});
      setScheduleData(initialSchedule || {});
      setMedicationsData([]);
      setFormErrors({});

      // 根据医嘱类型决定是否显示模板按钮
      const orderType = initialBasicInfo?.order_type;
      setShowTemplateBtn(orderType === 'medication');
    }
  }, [open, initialBasicInfo, initialSchedule, initialScheduleType]);

  // 编辑模式：只有一步，直接编辑基础信息和结束日期
  const isEditMode = !!editingOrder;

  const validateStep = (step: number): boolean => {
    const errors: FormErrors = {};

    if (step === 0) {
      // 编辑模式只需要验证标题
      if (!basicInfoData.title) errors.title = '请输入医嘱标题';
    }

    if (!isEditMode && step === 2) {
      if (!scheduleData.schedule_type) errors.schedule_type = '请选择调度类型';
      if (!scheduleData.start_date) errors.start_date = '请选择开始日期';
      if (!scheduleData.reminder_times || scheduleData.reminder_times.length === 0) {
        errors.reminder_times = '请选择提醒时间';
      }
      if (scheduleData.schedule_type === 'weekly' && (!scheduleData.weekdays || scheduleData.weekdays.length === 0)) {
        errors.weekdays = '请至少选择一天';
      }
    }

    // 用药步骤验证
    if (step === 1) {
      if (basicInfoData.order_type === 'medication' && medicationsData.length === 0) {
        errors.medications = '请至少添加一种药品';
      }
    }

    setFormErrors(formErrorsToRecord(errors));
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (!validateStep(currentStep)) return;

    // 编辑模式：直接提交
    if (isEditMode) {
      handleSubmit();
      return;
    }

    // 创建模式：继续下一步
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else {
      onClose();
    }
  };

  // 应用模板
  const handleApplyTemplate = (basicInfo: BasicInfoData, scheduleData: ScheduleData, medications?: OrderItem[]) => {
    setBasicInfoData(basicInfo);
    setScheduleData(scheduleData);
    if (medications) {
      setMedicationsData(medications);
    }
    setShowTemplateBtn(basicInfo.order_type === 'medication');
  };

  const handleSubmit = async () => {
    try {
      // 构建请求数据
      const requestData: any = {
        ...basicInfoData,
        ...scheduleData,
        patient_id: patientId,
        status: 'draft',
      };

      // 如果是用药类型且添加了药品，包含在请求中
      if (basicInfoData.order_type === 'medication' && medicationsData.length > 0) {
        (requestData as any).items = medicationsData;
      }

      if (editingOrder) {
        await doctorApi.updateOrder(editingOrder.id, {
          title: basicInfoData.title,
          description: basicInfoData.description,
          end_date: scheduleData.end_date,
          items: medicationsData.length > 0 ? medicationsData : undefined,
        });
        toast.success('医嘱更新成功');
      } else {
        await doctorApi.createOrder(requestData as Parameters<typeof doctorApi.createOrder>[0]);
        toast.success('医嘱创建成功');
      }

      onSuccess();
    } catch (error) {
      console.error('操作失败', error);
      toast.error('操作失败，请稍后重试');
    }
  };

  // 跳转到指定步骤
  const goToStep = (stepIndex: number) => {
    if (validateStep(currentStep)) {
      setCurrentStep(stepIndex);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(open) => {
      if (!open && currentStep === 0) {
        onClose();
      }
    }}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="flex-row items-center justify-between space-y-0">
          <DialogTitle>{editingOrder ? '编辑医嘱' : '创建医嘱'}</DialogTitle>

          {/* 模板按钮 */}
          {showTemplateBtn && !isEditMode && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setTemplatesOpen(true)}
              className="gap-2"
            >
              <FileText className="h-4 w-4" />
              使用模板
            </Button>
          )}
        </DialogHeader>

        {/* 步骤指示器 */}
        <StepIndicator currentStep={currentStep} steps={steps} />

        {/* 步骤0：基础信息 */}
        {currentStep === 0 && (
          <BasicInfoStep
            data={basicInfoData}
            onChange={setBasicInfoData}
            errors={formErrors}
            isEditing={!!editingOrder}
            onOrderTypeChange={(orderType) => {
              setShowTemplateBtn(orderType === 'medication');
            }}
          />
        )}

        {/* 步骤1：用药信息 */}
        {currentStep === 1 && (
          <MedicationsStep
            items={medicationsData}
            onChange={setMedicationsData}
            errors={formErrors}
          />
        )}

        {/* 步骤2：调度配置 */}
        {currentStep === 2 && (
          <ScheduleStep
            data={scheduleData}
            scheduleType={scheduleType}
            onScheduleTypeChange={setScheduleType}
            onChange={setScheduleData}
            errors={formErrors}
          />
        )}

        {/* 步骤3：确认 */}
        {currentStep === 3 && (
          <ConfirmStep
            basicInfo={basicInfoData}
            scheduleData={scheduleData}
            medications={medicationsData}
          />
        )}

        <DialogFooter className="mt-6">
          {/* 模板按钮在非第一步时显示 */}
          {showTemplateBtn && !isEditMode && currentStep > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setTemplatesOpen(true)}
            >
              <Copy className="h-4 w-4 mr-2" />
              使用模板
            </Button>
          )}

          <div className="flex-1"></div>

          <Button variant="outline" onClick={handleBack}>
            {isEditMode || currentStep === 0 ? '取消' : '上一步'}
          </Button>

          {/* 最后一步显示创建按钮 */}
          {currentStep === 3 || isEditMode ? (
            <Button onClick={handleSubmit}>
              {isEditMode ? '保存' : '创建'}
            </Button>
          ) : (
            <Button onClick={handleNext}>
              下一步
            </Button>
          )}
        </DialogFooter>
      </DialogContent>

      {/* 模板选择对话框 */}
      <OrderTemplates
        open={templatesOpen}
        onClose={() => setTemplatesOpen(false)}
        onSelectTemplate={handleApplyTemplate}
        currentOrderData={{
          basicInfo: basicInfoData,
          scheduleData: scheduleData,
        }}
      />
    </Dialog>
  );
};
