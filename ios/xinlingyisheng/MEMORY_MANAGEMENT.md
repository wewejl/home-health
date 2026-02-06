# iOS App Memory Issues Analysis and Fixes

## Summary
The app "灵犀医生" was killed due to excessive memory usage. This document tracks the identified memory issues and their fixes.

## Identified Issues

### 1. UnifiedChatViewModel - High Priority
**File**: `ViewModels/UnifiedChatViewModel.swift`

**Issue**:
- `setupVoiceBindings()` creates Combine subscriptions and closures
- `cleanupVoiceBindings()` exists but may not be called when view disappears
- The `voiceCancellables` store subscriptions that may retain self
- Callbacks like `onPartialResult`, `onFinalResult`, `onTTSEnded`, `onError` are set on the singleton `SimpleVoiceService`

**Fix**: Ensure cleanupVoiceBindings is called properly and add deinit safety

### 2. VoiceCallViewModel - High Priority
**File**: `ViewModels/VoiceCallViewModel.swift`

**Issue**:
- `recordingTimer` may not be invalidated in all exit paths
- `endConsultation()` calls `stopRecordingTimer()` but other paths may not
- No explicit deinit cleanup

**Fix**: Add deinit cleanup and ensure timer is always invalidated

### 3. VoiceChatViewModel - Medium Priority
**File**: `ViewModels/VoiceChatViewModel.swift`

**Issue**:
- `setupCallbacks()` creates closures that capture self
- Uses `weak self` which is good, but no explicit cleanup
- `VoiceChatService` callbacks may persist after ViewModel is deallocated

**Fix**: Add cleanup method and deinit safety

### 4. SimpleVoiceService - Medium Priority
**File**: `Services/Voice/SimpleVoiceService.swift`

**Issue**:
- `asrContinuation` and `ttsContinuation` may not be cleaned up properly
- WebSocket delegates use weak references (good) but continuations may retain

**Fix**: Clear continuations in stop() method

### 5. VoiceChatService - Medium Priority
**File**: `Services/Voice/VoiceChatService.swift`

**Issue**:
- `connectionContinuation` may cause retain cycles
- WebSocket delegate is self, not a separate delegate class

**Fix**: Add separate delegate class or clear continuation properly

### 6. TTS Services - Low Priority
**Files**:
- `Services/Voice/TTS/CosyVoiceTTSService.swift`
- `Services/Voice/TTS/QwenTTSRealtimeService.swift`

**Issue**:
- `synthesisCompletionHandler` may retain self
- Both have `cleanup()` method but may not be called

**Fix**: Ensure cleanup is called and use weak self in completion handlers

## Fix Priority
1. **High**: UnifiedChatViewModel, VoiceCallViewModel - These are most likely causing the OOM
2. **Medium**: VoiceChatViewModel, SimpleVoiceService, VoiceChatService
3. **Low**: TTS Services

## Testing
After fixes:
1. Run Instruments Leaks tool
2. Monitor memory usage during voice chat
3. Test repeated enter/exit of voice mode
4. Verify ViewModels are properly deallocated
