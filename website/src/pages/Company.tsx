import { Link } from 'react-router-dom';
import {
  Building2,
  Mail,
  Phone,
  MapPin,
  Users,
  Target,
  Award,
  Heart,
  ArrowRight,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const companyValues = [
  {
    icon: Heart,
    title: '用户至上',
    description: '始终将用户健康放在首位，用专业和温度服务每一位用户。',
    color: 'from-rose-500 to-pink-500',
  },
  {
    icon: Users,
    title: '团队协作',
    description: '汇聚医疗和技术领域专业人才，共同打造优质产品。',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Target,
    title: '持续创新',
    description: '不断探索 AI 技术在医疗健康领域的创新应用。',
    color: 'from-purple-500 to-violet-500',
  },
  {
    icon: Award,
    title: '诚信经营',
    description: '坚持诚实透明，保护用户隐私，建立可信赖品牌。',
    color: 'from-emerald-500 to-teal-500',
  },
];

const advantages = [
  {
    number: '01',
    title: '专业团队',
    description: '拥有丰富经验的医疗专家和技术团队，确保产品专业性',
  },
  {
    number: '02',
    title: '技术领先',
    description: '采用最新 AI 技术，提供智能化的健康咨询服务',
  },
  {
    number: '03',
    title: '服务周到',
    description: '7×24小时在线服务，随时响应用户需求',
  },
  {
    number: '04',
    title: '安全可靠',
    description: '严格的数据保护措施，保障用户信息安全',
  },
];

export default function Company() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-20 bg-gradient-soft">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-50 text-teal-600 text-sm font-medium mb-6">
                <Building2 size={16} />
                关于我们
              </div>
              <h1 className="text-h1 mb-6">
                <span className="text-gradient-brand">岳阳琳烨网络科技</span>
                有限公司
              </h1>
              <p className="text-body-lg text-text-secondary max-w-2xl mx-auto">
                我们是一家专注于医疗健康领域的科技公司，致力于通过人工智能技术，
                为用户提供专业、便捷、智能的健康管理解决方案。
              </p>
            </div>
          </div>
        </section>

        {/* 公司简介 */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="max-w-3xl mx-auto">
              <h2 className="text-h2 mb-8 text-center">公司简介</h2>
              <div className="prose prose-lg max-w-none">
                <p className="text-body text-text-secondary leading-relaxed mb-6">
                  岳阳琳烨网络科技有限公司成立于湖南岳阳，是一家专注于医疗健康领域的高科技企业。
                  公司以"让健康服务触手可及"为使命，通过先进的人工智能技术，
                  打破传统医疗服务的时空限制，为用户提供随时随地的高品质健康咨询服务。
                </p>
                <p className="text-body text-text-secondary leading-relaxed mb-6">
                  我们的核心产品"灵犀健康"是一款智能健康管理平台，集成了 AI 医生分身、
                  远程查房、健康档案管理等多项创新功能，为个人用户、养老机构、医院等
                  不同场景提供全方位的健康解决方案。
                </p>
                <p className="text-body text-text-secondary leading-relaxed">
                  公司拥有一支由医疗专家、AI 工程师、产品经理组成的专业团队，
                  深耕医疗健康行业，始终坚持以用户需求为导向，不断优化产品体验，
                  努力成为用户信赖的健康管理伙伴。
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 企业文化 */}
        <section className="py-20 bg-background">
          <div className="container-custom">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-h2 mb-4">企业文化</h2>
              <p className="text-body text-text-secondary">
                我们的价值观指引着每一个决策和行动
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {companyValues.map((value) => (
                <div
                  key={value.title}
                  className="bg-white rounded-2xl p-8 text-center shadow-card hover:shadow-card-hover transition-all duration-300 group"
                >
                  <div className={`w-16 h-16 bg-gradient-to-r ${value.color} rounded-2xl flex items-center justify-center text-white mx-auto mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <value.icon size={32} />
                  </div>
                  <h3 className="text-h5 mb-3 text-text-primary">{value.title}</h3>
                  <p className="text-body text-text-secondary">{value.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 核心优势 */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-h2 mb-4">核心优势</h2>
              <p className="text-body text-text-secondary">
                专业、技术、服务、安全，四大优势铸就品质
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {advantages.map((advantage) => (
                <div
                  key={advantage.number}
                  className="flex gap-6 p-6 bg-gradient-to-br from-primary-50 to-teal-50 rounded-2xl group hover:shadow-lg transition-all duration-300"
                >
                  <div className="flex-shrink-0">
                    <div className="w-14 h-14 bg-gradient-primary rounded-xl flex items-center justify-center text-white text-xl font-bold">
                      {advantage.number}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-h5 mb-2 text-text-primary">{advantage.title}</h3>
                    <p className="text-body text-text-secondary">{advantage.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 发展愿景 */}
        <section className="py-20 bg-gradient-to-br from-primary-500 to-teal-500">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto text-center text-white">
              <h2 className="text-h2 mb-8">发展愿景</h2>
              <p className="text-body-lg leading-relaxed mb-8 max-w-2xl mx-auto">
                成为国内领先的智能健康服务提供商，让每一个家庭都能享受到
                便捷、专业的健康管理服务，助力健康中国建设。
              </p>
              <div className="grid grid-cols-3 gap-8">
                <div className="bg-white/10 rounded-2xl p-6">
                  <div className="text-4xl font-bold mb-2">AI+</div>
                  <div className="text-white/80">智能驱动</div>
                </div>
                <div className="bg-white/10 rounded-2xl p-6">
                  <div className="text-4xl font-bold mb-2">O2O</div>
                  <div className="text-white/80">线上线下融合</div>
                </div>
                <div className="bg-white/10 rounded-2xl p-6">
                  <div className="text-4xl font-bold mb-2">100%</div>
                  <div className="text-white/80">用户满意</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 联系我们 */}
        <section className="py-20 bg-background">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-h2 mb-4">联系我们</h2>
                <p className="text-body text-text-secondary">
                  期待与您合作，共创健康未来
                </p>
              </div>
              <div className="grid md:grid-cols-3 gap-8">
                <a
                  href="mailto:1024344053@qq.com"
                  className="bg-white rounded-2xl p-8 text-center shadow-card hover:shadow-card-hover transition-all duration-300 group"
                >
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center text-white mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                    <Mail size={32} />
                  </div>
                  <h3 className="text-h5 mb-3 text-text-primary">电子邮箱</h3>
                  <p className="text-body text-text-secondary">1024344053@qq.com</p>
                </a>
                <a
                  href="tel:18107300167"
                  className="bg-white rounded-2xl p-8 text-center shadow-card hover:shadow-card-hover transition-all duration-300 group"
                >
                  <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center text-white mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                    <Phone size={32} />
                  </div>
                  <h3 className="text-h5 mb-3 text-text-primary">联系电话</h3>
                  <p className="text-body text-text-secondary">18107300167</p>
                </a>
                <div className="bg-white rounded-2xl p-8 text-center shadow-card">
                  <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-violet-500 rounded-2xl flex items-center justify-center text-white mx-auto mb-6">
                    <MapPin size={32} />
                  </div>
                  <h3 className="text-h5 mb-3 text-text-primary">公司地址</h3>
                  <p className="text-body text-text-secondary">湖南省岳阳市岳阳楼区<br />三眼桥街道李家冲社区<br />居民委员大楼605室</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-white">
          <div className="container-custom">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-h3 mb-4">开启智能健康之旅</h2>
              <p className="text-body text-text-secondary mb-8">
                立即下载灵犀健康，体验 AI 带来的便捷服务
              </p>
              <Link
                to="/download"
                className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-primary text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-primary-500/30 transition-all duration-300"
              >
                立即下载
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
