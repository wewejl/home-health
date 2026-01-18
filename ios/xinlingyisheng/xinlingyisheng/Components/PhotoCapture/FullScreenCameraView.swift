import SwiftUI
import AVFoundation
import Combine

// MARK: - 全屏相机界面
/// 符合设计规范的全屏相机界面，带取景框引导
struct FullScreenCameraView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var cameraService = CameraService()
    
    @State private var flashMode: AVCaptureDevice.FlashMode = .off
    @State private var capturedImage: UIImage?
    @State private var showPreview = false
    
    var onImageCaptured: (UIImage) -> Void
    
    var body: some View {
        ZStack {
            // 相机预览层
            CameraPreviewView(session: cameraService.session)
                .ignoresSafeArea()
            
            // 半透明遮罩（取景框外区域）
            CameraOverlayView()
            
            // 顶部工具栏
            VStack {
                topToolbar
                Spacer()
            }
            
            // 取景框和引导
            viewfinderGuide
            
            // 底部控制栏
            VStack {
                Spacer()
                bottomControls
            }
        }
        .statusBar(hidden: true)
        .onAppear {
            cameraService.startSession()
        }
        .onDisappear {
            cameraService.stopSession()
        }
        .fullScreenCover(isPresented: $showPreview) {
            if let image = capturedImage {
                PhotoPreviewView(
                    image: image,
                    onRetake: {
                        showPreview = false
                        capturedImage = nil
                    },
                    onConfirm: { confirmedImage, note in
                        showPreview = false
                        dismiss()
                        onImageCaptured(confirmedImage)
                    }
                )
            }
        }
    }
    
    // MARK: - 顶部工具栏
    private var topToolbar: some View {
        HStack {
            // 关闭按钮
            Button(action: { dismiss() }) {
                Image(systemName: "xmark")
                    .font(.system(size: ScaleFactor.size(20), weight: .medium))
                    .foregroundColor(.white)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .background(Color.black.opacity(0.5))
                    .clipShape(Circle())
            }
            
            Spacer()
            
            // 闪光灯按钮
            Button(action: toggleFlash) {
                Image(systemName: flashMode == .on ? "bolt.fill" : "bolt.slash.fill")
                    .font(.system(size: ScaleFactor.size(20), weight: .medium))
                    .foregroundColor(flashMode == .on ? .yellow : .white)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .background(Color.black.opacity(0.5))
                    .clipShape(Circle())
            }
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.top, ScaleFactor.padding(16))
    }
    
    // MARK: - 取景框引导
    private var viewfinderGuide: some View {
        VStack {
            Spacer()
            
            // 取景框
            ZStack {
                RoundedRectangle(cornerRadius: ScaleFactor.size(20))
                    .stroke(Color.white, lineWidth: 3)
                    .frame(width: ScaleFactor.size(280), height: ScaleFactor.size(280))
                
                // 角标装饰
                ViewfinderCorners()
                    .stroke(Color.white, lineWidth: 4)
                    .frame(width: ScaleFactor.size(280), height: ScaleFactor.size(280))
            }
            
            // 引导文字
            Text("将皮肤问题置于框内")
                .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.vertical, ScaleFactor.padding(8))
                .background(Color.black.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(8)))
                .padding(.top, ScaleFactor.padding(20))
            
            Spacer()
        }
    }
    
    // MARK: - 底部控制栏
    private var bottomControls: some View {
        HStack(spacing: ScaleFactor.spacing(60)) {
            // 切换摄像头按钮
            Button(action: { cameraService.switchCamera() }) {
                Image(systemName: "arrow.triangle.2.circlepath.camera")
                    .font(.system(size: ScaleFactor.size(28)))
                    .foregroundColor(.white)
                    .frame(width: ScaleFactor.size(50), height: ScaleFactor.size(50))
            }
            
            // 拍摄按钮
            Button(action: capturePhoto) {
                ZStack {
                    Circle()
                        .fill(Color.white)
                        .frame(width: ScaleFactor.size(70), height: ScaleFactor.size(70))
                    
                    Circle()
                        .stroke(Color.white, lineWidth: 4)
                        .frame(width: ScaleFactor.size(80), height: ScaleFactor.size(80))
                }
            }
            
            // 占位（保持对称）
            Color.clear
                .frame(width: ScaleFactor.size(50), height: ScaleFactor.size(50))
        }
        .padding(.bottom, ScaleFactor.padding(50))
    }
    
    // MARK: - 功能方法
    private func toggleFlash() {
        flashMode = flashMode == .on ? .off : .on
        cameraService.setFlashMode(flashMode)
    }
    
    private func capturePhoto() {
        cameraService.capturePhoto { image in
            if let image = image {
                capturedImage = image
                showPreview = true
            }
        }
    }
}

// MARK: - 取景框角标装饰
struct ViewfinderCorners: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let cornerLength: CGFloat = 30
        let cornerRadius: CGFloat = 20
        
        // 左上角
        path.move(to: CGPoint(x: rect.minX, y: rect.minY + cornerLength))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.minY + cornerRadius))
        path.addQuadCurve(
            to: CGPoint(x: rect.minX + cornerRadius, y: rect.minY),
            control: CGPoint(x: rect.minX, y: rect.minY)
        )
        path.addLine(to: CGPoint(x: rect.minX + cornerLength, y: rect.minY))
        
        // 右上角
        path.move(to: CGPoint(x: rect.maxX - cornerLength, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.maxX - cornerRadius, y: rect.minY))
        path.addQuadCurve(
            to: CGPoint(x: rect.maxX, y: rect.minY + cornerRadius),
            control: CGPoint(x: rect.maxX, y: rect.minY)
        )
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.minY + cornerLength))
        
        // 右下角
        path.move(to: CGPoint(x: rect.maxX, y: rect.maxY - cornerLength))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY - cornerRadius))
        path.addQuadCurve(
            to: CGPoint(x: rect.maxX - cornerRadius, y: rect.maxY),
            control: CGPoint(x: rect.maxX, y: rect.maxY)
        )
        path.addLine(to: CGPoint(x: rect.maxX - cornerLength, y: rect.maxY))
        
        // 左下角
        path.move(to: CGPoint(x: rect.minX + cornerLength, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.minX + cornerRadius, y: rect.maxY))
        path.addQuadCurve(
            to: CGPoint(x: rect.minX, y: rect.maxY - cornerRadius),
            control: CGPoint(x: rect.minX, y: rect.maxY)
        )
        path.addLine(to: CGPoint(x: rect.minX, y: rect.maxY - cornerLength))
        
        return path
    }
}

// MARK: - 相机遮罩层（取景框外半透明）
struct CameraOverlayView: View {
    var body: some View {
        GeometryReader { geometry in
            let frameSize = ScaleFactor.size(280)
            let centerX = geometry.size.width / 2
            let centerY = geometry.size.height / 2
            
            Path { path in
                // 外部矩形（整个屏幕）
                path.addRect(CGRect(origin: .zero, size: geometry.size))
                
                // 内部矩形（取景框区域，使用 evenOdd 规则挖空）
                let frameRect = CGRect(
                    x: centerX - frameSize / 2,
                    y: centerY - frameSize / 2,
                    width: frameSize,
                    height: frameSize
                )
                path.addRoundedRect(in: frameRect, cornerSize: CGSize(width: 20, height: 20))
            }
            .fill(Color.black.opacity(0.5), style: FillStyle(eoFill: true))
        }
        .ignoresSafeArea()
    }
}

// MARK: - 相机预览视图
struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: .zero)
        view.backgroundColor = .black
        
        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        previewLayer.frame = UIScreen.main.bounds
        view.layer.addSublayer(previewLayer)
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        if let previewLayer = uiView.layer.sublayers?.first as? AVCaptureVideoPreviewLayer {
            previewLayer.frame = UIScreen.main.bounds
        }
    }
}

// MARK: - 相机服务
class CameraService: NSObject, ObservableObject {
    @Published var isSessionRunning = false
    
    let session = AVCaptureSession()
    private var photoOutput = AVCapturePhotoOutput()
    private var currentCameraPosition: AVCaptureDevice.Position = .back
    private var flashMode: AVCaptureDevice.FlashMode = .off
    private var photoCaptureCompletion: ((UIImage?) -> Void)?
    
    override init() {
        super.init()
        setupSession()
    }
    
    private func setupSession() {
        session.beginConfiguration()
        session.sessionPreset = .photo
        
        // 添加相机输入
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: camera) else {
            session.commitConfiguration()
            return
        }
        
        if session.canAddInput(input) {
            session.addInput(input)
        }
        
        // 添加照片输出
        if session.canAddOutput(photoOutput) {
            session.addOutput(photoOutput)
        }
        
        session.commitConfiguration()
    }
    
    func startSession() {
        guard !session.isRunning else { return }
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.session.startRunning()
            DispatchQueue.main.async {
                self?.isSessionRunning = true
            }
        }
    }
    
    func stopSession() {
        guard session.isRunning else { return }
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.session.stopRunning()
            DispatchQueue.main.async {
                self?.isSessionRunning = false
            }
        }
    }
    
    func switchCamera() {
        session.beginConfiguration()
        
        // 移除现有输入
        session.inputs.forEach { session.removeInput($0) }
        
        // 切换摄像头位置
        currentCameraPosition = currentCameraPosition == .back ? .front : .back
        
        // 添加新输入
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: currentCameraPosition),
              let input = try? AVCaptureDeviceInput(device: camera) else {
            session.commitConfiguration()
            return
        }
        
        if session.canAddInput(input) {
            session.addInput(input)
        }
        
        session.commitConfiguration()
    }
    
    func setFlashMode(_ mode: AVCaptureDevice.FlashMode) {
        flashMode = mode
    }
    
    func capturePhoto(completion: @escaping (UIImage?) -> Void) {
        photoCaptureCompletion = completion
        
        let settings = AVCapturePhotoSettings()
        if photoOutput.supportedFlashModes.contains(flashMode) {
            settings.flashMode = flashMode
        }
        
        photoOutput.capturePhoto(with: settings, delegate: self)
    }
}

// MARK: - AVCapturePhotoCaptureDelegate
extension CameraService: AVCapturePhotoCaptureDelegate {
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard error == nil,
              let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            photoCaptureCompletion?(nil)
            return
        }
        
        // 如果是前置摄像头，需要镜像翻转
        if currentCameraPosition == .front {
            let flippedImage = UIImage(cgImage: image.cgImage!, scale: image.scale, orientation: .leftMirrored)
            photoCaptureCompletion?(flippedImage)
        } else {
            photoCaptureCompletion?(image)
        }
    }
}

// MARK: - Preview
#Preview {
    FullScreenCameraView(onImageCaptured: { _ in })
}
