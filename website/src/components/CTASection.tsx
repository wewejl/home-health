import { Link } from 'react-router-dom';
import { ArrowRight, Download as DownloadIcon, QrCode } from 'lucide-react';

export default function CTASection() {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* 背景渐变 */}
      <div className="absolute inset-0 bg-gradient-primary"></div>
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-teal-400/20 rounded-full blur-3xl"></div>
      </div>

      <div className="container-custom relative z-10">
        <div className="max-w-4xl mx-auto text-center text-white">
          {/* 标题 */}
          <h2 className="text-h1 mb-6">
            开启您的智能健康之旅
          </h2>

          {/* 描述 */}
          <p className="text-xl text-white/80 mb-12 max-w-2xl mx-auto">
            立即下载灵犀健康 App，体验 AI 医生分身带来的便捷健康服务
          </p>

          {/* 下载选项 */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            {/* iOS 下载 */}
            <Link
              to="/download"
              className="group flex items-center gap-4 px-8 py-4 bg-white rounded-2xl hover:bg-white/90 transition-all duration-300 hover:scale-105 shadow-xl"
            >
              <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center">
                <DownloadIcon size={24} className="text-white" />
              </div>
              <div className="text-left">
                <div className="text-xs text-gray-500 mb-0.5">Download on the</div>
                <div className="text-xl font-semibold">App Store</div>
              </div>
            </Link>

            {/* 二维码 */}
            <div className="flex items-center gap-4 px-8 py-4 bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20">
              <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center">
                <QrCode size={32} className="text-primary-500" />
              </div>
              <div className="text-left">
                <div className="font-medium">扫码下载</div>
                <div className="text-sm text-white/70">支持 iOS 设备</div>
              </div>
            </div>
          </div>

          {/* 底部链接 */}
          <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-8 text-white/80">
            <Link
              to="/features"
              className="flex items-center gap-2 hover:text-white transition-colors duration-300 group"
            >
              了解产品功能
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/about"
              className="flex items-center gap-2 hover:text-white transition-colors duration-300 group"
            >
              联系商务合作
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
