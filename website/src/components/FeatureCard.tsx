import { LucideIcon } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  color?: 'blue' | 'teal' | 'orange' | 'purple' | 'green';
  delay?: number;
}

const colorClasses = {
  blue: {
    bg: 'bg-primary-50',
    iconBg: 'bg-primary-500',
    text: 'text-primary-500',
  },
  teal: {
    bg: 'bg-teal-50',
    iconBg: 'bg-teal-500',
    text: 'text-teal-500',
  },
  orange: {
    bg: 'bg-orange-50',
    iconBg: 'bg-orange-500',
    text: 'text-orange-500',
  },
  purple: {
    bg: 'bg-purple-50',
    iconBg: 'bg-purple-500',
    text: 'text-purple-500',
  },
  green: {
    bg: 'bg-success/20',
    iconBg: 'bg-success',
    text: 'text-success-dark',
  },
};

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  color = 'blue',
  delay = 0,
}: FeatureCardProps) {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const colors = colorClasses[color];

  return (
    <div
      ref={ref}
      className={`group card-gradient hover:shadow-glow transition-all duration-500 ${
        inView ? 'animate-scale-in opacity-100' : 'opacity-0'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* 图标 */}
      <div className={`w-14 h-14 ${colors.iconBg} rounded-2xl flex items-center justify-center text-white mb-5 group-hover:scale-110 transition-transform duration-300`}>
        <Icon size={28} />
      </div>

      {/* 内容 */}
      <h3 className={`text-h4 mb-3 ${colors.text}`}>{title}</h3>
      <p className="text-body text-text-secondary leading-relaxed">
        {description}
      </p>

      {/* 装饰线 */}
      <div className={`mt-5 h-1 w-12 ${colors.iconBg} rounded-full group-hover:w-full transition-all duration-500`}></div>
    </div>
  );
}
