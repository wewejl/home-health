import {
  Brain,
  Stethoscope,
  FileText,
  Mic,
  Pill,
  Video,
} from 'lucide-react';
import FeatureCard from './FeatureCard';
import { Link } from 'react-router-dom';

const features = [
  {
    icon: Brain,
    title: 'AI 智能咨询',
    description: '基于先进的自然语言处理技术，理解您的健康问题，提供专业的医疗建议和解答。',
    color: 'blue' as const,
  },
  {
    icon: Stethoscope,
    title: '医生分身系统',
    description: '多科室专家 AI 分身，模拟真实问诊体验，提供精准的专科健康咨询服务。',
    color: 'teal' as const,
  },
  {
    icon: FileText,
    title: '健康档案管理',
    description: '自动记录和管理您的健康数据，生成完整的健康档案，方便随时查看和分享。',
    color: 'purple' as const,
  },
  {
    icon: Mic,
    title: '语音交互',
    description: '支持自然语音对话，像与真人医生交流一样自然，使用更加便捷友好。',
    color: 'orange' as const,
  },
  {
    icon: Pill,
    title: '医嘱监督',
    description: '智能用药提醒和执行跟踪，确保按时按量服药，守护您的健康每一刻。',
    color: 'green' as const,
  },
  {
    icon: Video,
    title: '远程查房',
    description: '为养老机构提供远程查房服务，医生可远程了解患者情况，提高工作效率。',
    color: 'blue' as const,
  },
];

export default function FeaturesSection() {
  return (
    <section className="py-24 bg-gradient-soft relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-primary-500/5 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-teal-500/5 rounded-full blur-3xl"></div>

      <div className="container-custom relative z-10">
        {/* 标题 */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-h2 mb-4">
            <span className="text-gradient-teal">全方位</span> 健康管理服务
          </h2>
          <p className="text-body-lg text-text-secondary">
            集智能咨询、健康档案、医嘱监督于一体，为您提供一站式健康管理解决方案
          </p>
        </div>

        {/* 功能卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {features.map((feature, index) => (
            <FeatureCard
              key={feature.title}
              {...feature}
              delay={index * 100}
            />
          ))}
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link to="/features" className="btn btn-secondary">
            了解更多功能详情
          </Link>
        </div>
      </div>
    </section>
  );
}
