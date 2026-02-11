import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { OrdersTableSkeleton } from '@/components/medical/loading-skeleton';
import { doctorApi } from '@/api';
import type {
  MedicalOrder,
  BasicInfoData,
  ScheduleData,
  ScheduleType,
} from './orders/types';
import { OrdersList } from './orders/OrdersList';
import { CreateOrderDialog } from './orders/CreateOrderDialog';
import { ConfirmDialog } from './orders/ConfirmDialog';

interface OrdersTabProps {
  patientId: number;
  refresh: () => void;
}

const OrdersTab = ({ patientId, refresh }: OrdersTabProps) => {
  const toast = useToast();
  const [orders, setOrders] = useState<MedicalOrder[]>([]);
  const [loading, setLoading] = useState(true);

  // 对话框状态
  const [modalVisible, setModalVisible] = useState(false);
  const [editingOrder, setEditingOrder] = useState<MedicalOrder | null>(null);

  // 确认对话框状态
  const [confirmDialog, setConfirmDialog] = useState<{
    show: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    show: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });

  // 表单初始数据
  const [initialBasicInfo, setInitialBasicInfo] = useState<BasicInfoData>({});
  const [initialSchedule, setInitialSchedule] = useState<ScheduleData>({});
  const [initialScheduleType, setInitialScheduleType] = useState<ScheduleType>('once');

  useEffect(() => {
    fetchOrders();
  }, [patientId]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const { data } = await doctorApi.getPatientOrders(patientId);
      setOrders(data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingOrder(null);
    setInitialBasicInfo({});
    setInitialSchedule({});
    setInitialScheduleType('once');
    setModalVisible(true);
  };

  const handleEdit = (order: MedicalOrder) => {
    setEditingOrder(order);

    const basicInfo: BasicInfoData = {
      order_type: order.order_type,
      title: order.title,
      description: order.description,
      end_date: order.end_date,  // 编辑时可以修改结束日期
    };
    const schedule: ScheduleData = {
      schedule_type: (order.schedule_type as ScheduleType) || 'once',
      start_date: order.start_date,
      reminder_times: order.reminder_times || [],
      frequency: order.frequency,
    };

    setInitialBasicInfo(basicInfo);
    setInitialSchedule(schedule);
    setInitialScheduleType((order.schedule_type as ScheduleType) || 'once');
    setModalVisible(true);
  };

  const handleToggleStatus = (order: MedicalOrder) => {
    if (order.status === 'active') {
      // 停用医嘱
      setConfirmDialog({
        show: true,
        title: '确认停用',
        message: '确定要停用这条医嘱吗？停用后将不再生成任务。',
        onConfirm: async () => {
          try {
            await doctorApi.deleteOrder(order.id);
            toast.success('医嘱已停用');
            fetchOrders();
            refresh();
          } catch (error) {
            console.error('停用失败', error);
            toast.error('停用医嘱失败，请稍后重试');
          }
          closeConfirmDialog();
        },
      });
    } else if (order.status === 'draft') {
      // 激活医嘱
      setConfirmDialog({
        show: true,
        title: '确认激活',
        message: '确定要激活这条医嘱吗？激活后将开始生成任务。',
        onConfirm: async () => {
          try {
            await doctorApi.activateOrder(order.id, true);
            toast.success('医嘱已激活');
            fetchOrders();
            refresh();
          } catch (error) {
            console.error('激活医嘱失败:', error);
            toast.error('激活医嘱失败，请稍后重试');
          }
          closeConfirmDialog();
        },
      });
    }
  };

  const closeConfirmDialog = () => {
    setConfirmDialog({ show: false, title: '', message: '', onConfirm: () => {} });
  };

  const handleDialogSuccess = () => {
    setModalVisible(false);
    fetchOrders();
    refresh();
  };

  const handleDialogClose = () => {
    setModalVisible(false);
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">医嘱列表</h2>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          创建医嘱
        </Button>
      </div>

      {loading ? (
        <OrdersTableSkeleton />
      ) : (
        <OrdersList
          orders={orders}
          loading={loading}
          onEdit={handleEdit}
          onToggleStatus={handleToggleStatus}
        />
      )}

      {/* 创建/编辑医嘱对话框 */}
      <CreateOrderDialog
        open={modalVisible}
        editingOrder={editingOrder}
        onClose={handleDialogClose}
        onSuccess={handleDialogSuccess}
        patientId={patientId}
        initialBasicInfo={initialBasicInfo}
        initialSchedule={initialSchedule}
        initialScheduleType={initialScheduleType}
      />

      {/* 确认对话框 */}
      <ConfirmDialog
        show={confirmDialog.show}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onClose={closeConfirmDialog}
      />
    </div>
  );
};

export default OrdersTab;
