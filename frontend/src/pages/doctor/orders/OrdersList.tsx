import type { MedicalOrder } from './types';
import { getOrderTypeLabel, getStatusLabel } from './utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Edit, Ban, Play } from 'lucide-react';
import dayjs from 'dayjs';

interface OrdersListProps {
  orders: MedicalOrder[];
  loading: boolean;
  onEdit: (order: MedicalOrder) => void;
  onToggleStatus: (order: MedicalOrder) => void;
}

export const OrdersList = ({ orders, loading, onEdit, onToggleStatus }: OrdersListProps) => {
  if (loading) {
    return null; // 骨架屏由父组件处理
  }

  return (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[60px]">ID</TableHead>
            <TableHead className="w-[120px]">医嘱类型</TableHead>
            <TableHead>医嘱标题</TableHead>
            <TableHead>描述</TableHead>
            <TableHead className="w-[120px]">开始日期</TableHead>
            <TableHead className="w-[120px]">结束日期</TableHead>
            <TableHead className="w-[100px]">状态</TableHead>
            <TableHead className="w-[180px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                暂无医嘱
              </TableCell>
            </TableRow>
          ) : (
            orders.map((order) => (
              <TableRow key={order.id}>
                <TableCell className="text-muted-foreground">{order.id}</TableCell>
                <TableCell>
                  <Badge className={getOrderTypeLabel(order.order_type).className}>
                    {getOrderTypeLabel(order.order_type).label}
                  </Badge>
                </TableCell>
                <TableCell>{order.title}</TableCell>
                <TableCell className="text-muted-foreground">{order.description || '-'}</TableCell>
                <TableCell>{dayjs(order.start_date).format('YYYY-MM-DD')}</TableCell>
                <TableCell>{order.end_date ? dayjs(order.end_date).format('YYYY-MM-DD') : '长期'}</TableCell>
                <TableCell>
                  <Badge className={getStatusLabel(order.status).className}>
                    {getStatusLabel(order.status).label}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    {order.status === 'draft' && (
                      <>
                        <Button variant="ghost" size="sm" className="h-8" onClick={() => onEdit(order)}>
                          <Edit className="h-3 w-3 mr-1" />
                          编辑
                        </Button>
                        <Button size="sm" className="h-8" onClick={() => onToggleStatus(order)}>
                          <Play className="h-3 w-3 mr-1" />
                          激活
                        </Button>
                      </>
                    )}
                    {order.status === 'active' && (
                      <>
                        <Button variant="ghost" size="sm" className="h-8" onClick={() => onEdit(order)}>
                          <Edit className="h-3 w-3 mr-1" />
                          编辑
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 text-destructive" onClick={() => onToggleStatus(order)}>
                          <Ban className="h-3 w-3 mr-1" />
                          停用
                        </Button>
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
