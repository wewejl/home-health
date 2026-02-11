import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

export interface FeatureCardProps {
  title: string;
  content: string;
  icon: React.ReactNode;
  className?: string;
}

/**
 * FeatureCard - 特性卡片组件
 *
 * 用于展示带图标的功能卡片，常用于功能列表或特性展示
 */
export const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  content,
  icon,
  className,
}) => (
  <Card className={className}>
    <CardContent className="p-4">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="text-primary">{icon}</div>
          <p className="font-medium text-sm">{title}</p>
        </div>
        <p className="text-sm text-foreground-secondary">{content}</p>
      </div>
    </CardContent>
  </Card>
);

export default FeatureCard;
