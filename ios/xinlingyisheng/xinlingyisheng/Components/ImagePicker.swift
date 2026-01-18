import SwiftUI
import UIKit
import PhotosUI

// MARK: - UIKit ImagePicker Wrapper
struct ImagePicker: UIViewControllerRepresentable {
    @Environment(\.dismiss) private var dismiss
    let sourceType: UIImagePickerController.SourceType
    let onImageSelected: (UIImage) -> Void
    
    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = sourceType
        picker.delegate = context.coordinator
        picker.allowsEditing = false
        
        if sourceType == .camera {
            picker.cameraCaptureMode = .photo
        }
        
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker
        
        init(_ parent: ImagePicker) {
            self.parent = parent
        }
        
        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let image = info[.originalImage] as? UIImage {
                parent.onImageSelected(image)
            }
            parent.dismiss()
        }
        
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}

// MARK: - 图片选择器视图（带权限检查）
struct DermaImagePicker: View {
    @Binding var isPresented: Bool
    let sourceType: UIImagePickerController.SourceType
    let onImageSelected: (UIImage) -> Void
    
    @State private var showPermissionAlert = false
    @State private var permissionAlertMessage = ""
    
    var body: some View {
        Group {
            if sourceType == .camera {
                CameraPickerView(
                    isPresented: $isPresented,
                    onImageSelected: onImageSelected,
                    showPermissionAlert: $showPermissionAlert,
                    permissionAlertMessage: $permissionAlertMessage
                )
            } else {
                PhotoLibraryPickerView(
                    isPresented: $isPresented,
                    onImageSelected: onImageSelected
                )
            }
        }
        .alert("权限提示", isPresented: $showPermissionAlert) {
            Button("去设置") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text(permissionAlertMessage)
        }
    }
}

// MARK: - 相机选择器
struct CameraPickerView: View {
    @Binding var isPresented: Bool
    let onImageSelected: (UIImage) -> Void
    @Binding var showPermissionAlert: Bool
    @Binding var permissionAlertMessage: String
    
    var body: some View {
        Color.clear
            .onAppear {
                checkCameraPermission()
            }
    }
    
    private func checkCameraPermission() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            break
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    if !granted {
                        isPresented = false
                        permissionAlertMessage = "需要相机权限才能拍照，请在设置中开启"
                        showPermissionAlert = true
                    }
                }
            }
        case .denied, .restricted:
            DispatchQueue.main.async {
                isPresented = false
                permissionAlertMessage = "需要相机权限才能拍照，请在设置中开启"
                showPermissionAlert = true
            }
        @unknown default:
            break
        }
    }
}

// MARK: - 相册选择器
struct PhotoLibraryPickerView: View {
    @Binding var isPresented: Bool
    let onImageSelected: (UIImage) -> Void
    
    var body: some View {
        PHPickerViewWrapper(
            isPresented: $isPresented,
            onImageSelected: onImageSelected
        )
    }
}

// MARK: - PHPicker Wrapper (iOS 14+)
struct PHPickerViewWrapper: UIViewControllerRepresentable {
    @Binding var isPresented: Bool
    let onImageSelected: (UIImage) -> Void
    
    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.filter = .images
        config.selectionLimit = 1
        
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }
    
    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: PHPickerViewWrapper
        
        init(_ parent: PHPickerViewWrapper) {
            self.parent = parent
        }
        
        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.isPresented = false
            
            guard let result = results.first else { return }
            
            result.itemProvider.loadObject(ofClass: UIImage.self) { [weak self] object, error in
                if let image = object as? UIImage {
                    DispatchQueue.main.async {
                        self?.parent.onImageSelected(image)
                    }
                }
            }
        }
    }
}

// MARK: - 图片选择操作表
struct ImagePickerActionSheet: View {
    @Binding var isPresented: Bool
    @Binding var showImagePicker: Bool
    @Binding var sourceType: UIImagePickerController.SourceType
    
    var body: some View {
        EmptyView()
            .confirmationDialog("选择图片来源", isPresented: $isPresented, titleVisibility: .visible) {
                Button("📷 拍照") {
                    sourceType = .camera
                    showImagePicker = true
                }
                
                Button("🖼️ 从相册选择") {
                    sourceType = .photoLibrary
                    showImagePicker = true
                }
                
                Button("取消", role: .cancel) {}
            }
    }
}

// MARK: - 导入 AVFoundation
import AVFoundation
