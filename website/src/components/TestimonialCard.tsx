import { Quote, Star } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

interface TestimonialCardProps {
  name: string;
  role: string;
  content: string;
  avatar: string;
  rating: number;
  delay?: number;
}

export default function TestimonialCard({
  name,
  role,
  content,
  avatar,
  rating,
  delay = 0,
}: TestimonialCardProps) {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <div
      ref={ref}
      className={`relative p-8 bg-white rounded-2xl shadow-card hover:shadow-card-hover transition-all duration-500 ${
        inView ? 'animate-scale-in opacity-100' : 'opacity-0'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* 装饰性引号 */}
      <div className="absolute top-6 right-6 text-primary-100">
        <Quote size={48} fill="currentColor" />
      </div>

      {/* 评分 */}
      <div className="flex items-center gap-1 mb-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            size={18}
            className={i < rating ? 'fill-orange-400 text-orange-400' : 'fill-gray-200 text-gray-200'}
          />
        ))}
      </div>

      {/* 内容 */}
      <p className="text-body text-text-secondary mb-6 leading-relaxed">
        "{content}"
      </p>

      {/* 用户信息 */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-gradient-primary flex items-center justify-center text-white font-semibold">
          {avatar}
        </div>
        <div>
          <div className="font-semibold text-text-primary">{name}</div>
          <div className="text-sm text-text-secondary">{role}</div>
        </div>
      </div>
    </div>
  );
}
