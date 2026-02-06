import TestimonialCard from './TestimonialCard';

const testimonials = [
  {
    name: '张女士',
    role: '慢性病患者',
    avatar: '张',
    content: '灵犀健康让我在家就能随时咨询健康问题，AI 医生非常专业，用药提醒功能帮我养成了按时服药的习惯。',
    rating: 5,
  },
  {
    name: '李院长',
    role: '养老院院长',
    avatar: '李',
    content: '远程查房功能大大提高了我们的工作效率，医生可以同时关注多位老人，家属也更放心了。',
    rating: 5,
  },
  {
    name: '王医生',
    role: '内科主治医师',
    avatar: '王',
    content: '作为医生分身系统，灵犀健康能很好地辅助我进行初步问诊，让我的时间能更集中在需要重点关注的病人身上。',
    rating: 5,
  },
];

export default function TestimonialsSection() {
  return (
    <section className="py-24 bg-white relative overflow-hidden">
      <div className="container-custom">
        {/* 标题 */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-h2 mb-4">
            用户<span className="text-gradient-teal">真实评价</span>
          </h2>
          <p className="text-body-lg text-text-secondary">
            来自各行各业的用户，分享他们使用灵犀健康的真实体验
          </p>
        </div>

        {/* 评价卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard
              key={testimonial.name}
              {...testimonial}
              delay={index * 150}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
