<template>
  <el-dialog
    :model-value="modelValue"
    width="620px"
    align-center
    @close="handleClose"
  >
    <template #header>
      <div class="ped-header">
        <p class="ped-eyebrow">PROFILE ARCHIVE</p>
        <h3 class="ped-title">编辑个人资料</h3>
      </div>
    </template>

    <div class="ped-body">
      <div class="ped-avatar-section">
        <div class="ped-avatar-wrap" @click="triggerFileInput">
          <UserAvatar
            :username="user?.username || ''"
            :avatar="avatarPreview || form.avatar_url"
            size="large"
          />
          <div class="ped-avatar-overlay">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            class="ped-file-input"
            @change="handleFileChange"
          />
        </div>
        <div class="ped-avatar-info">
          <span class="ped-avatar-hint">{{ avatarUploading ? '头像上传中…' : '点击更换头像' }}</span>
          <span class="ped-avatar-limit">支持 JPG/PNG/GIF/WEBP，不超过 2MB</span>
        </div>
      </div>

      <el-form label-position="top" class="ped-form">
        <div class="ped-form-grid">
          <el-form-item label="昵称">
            <el-input
              v-model="form.nickname"
              maxlength="50"
              placeholder="为自己取一个更有诗意的名字"
            />
          </el-form-item>

          <el-form-item label="邮箱">
            <el-input
              v-model="form.email"
              maxlength="100"
              placeholder="your@email.com"
            />
          </el-form-item>

          <el-form-item label="手机号">
            <el-input
              v-model="form.phone"
              maxlength="11"
              placeholder="11 位手机号，可留空"
            />
          </el-form-item>
        </div>

        <el-form-item label="个人简介">
          <el-input
            v-model="form.bio"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="写下一句属于你的诗心自述"
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="ped-footer">
        <button
          type="button"
          class="ped-btn ped-btn--ghost"
          :disabled="submitting"
          @click="handleClose"
        >
          取消
        </button>
        <button
          type="button"
          class="ped-btn ped-btn--primary"
          :disabled="submitting"
          @click="handleSubmit"
        >
          {{ submitting ? '保存中…' : '保存资料' }}
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch, type PropType } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi, type UserInfo } from '@/api/user'
import { useUserStore } from '@/store/modules/user'
import UserAvatar from '@/components/UserAvatar.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  user: {
    type: Object as PropType<UserInfo | null>,
    default: null
  }
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [user: UserInfo]
}>()

const userStore = useUserStore()
const submitting = ref(false)
const avatarUploading = ref(false)
const avatarPreview = ref<string | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

const form = reactive({
  nickname: '',
  avatar_url: '',
  bio: '',
  email: '',
  phone: ''
})

const syncForm = () => {
  form.nickname = props.user?.nickname || ''
  form.avatar_url = props.user?.avatar_url || ''
  form.bio = props.user?.bio || ''
  form.email = props.user?.email || ''
  form.phone = props.user?.phone || ''
  avatarPreview.value = null
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) syncForm()
  }
)

watch(
  () => props.user,
  () => {
    if (props.modelValue) syncForm()
  },
  { deep: true }
)

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileChange = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('头像文件不能超过 2MB')
    return
  }

  avatarPreview.value = URL.createObjectURL(file)
  avatarUploading.value = true
  try {
    const result = await userApi.uploadAvatar(file)
    form.avatar_url = result.avatar_url
    ElMessage.success('头像已更新')
    await userStore.fetchUserInfo()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '头像上传失败')
    avatarPreview.value = null
  } finally {
    avatarUploading.value = false
    target.value = ''
  }
}

const handleClose = () => {
  if (avatarPreview.value) {
    URL.revokeObjectURL(avatarPreview.value)
    avatarPreview.value = null
  }
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const user = await userApi.updateProfile({
      nickname: form.nickname.trim() || null,
      bio: form.bio.trim() || null,
      email: form.email.trim() || null,
      phone: form.phone.trim() || null
    })
    emit('saved', user)
    await userStore.fetchUserInfo()
    ElMessage.success('个人资料已更新')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '个人资料更新失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.ped-header {
  display: grid;
  gap: 6px;
}

.ped-eyebrow {
  font-size: 0.8rem;
  letter-spacing: 0.24em;
  color: rgba(52, 73, 94, 0.64);
}

.ped-title {
  color: var(--color-ink-dark);
  font-size: 1.4rem;
}

.ped-body {
  padding-top: 4px;
}

.ped-avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 20px;
  margin-bottom: 20px;
  border-radius: 18px;
  background:
    radial-gradient(circle at top left, rgba(217, 119, 87, 0.08), transparent 50%),
    linear-gradient(180deg, rgba(250, 249, 245, 0.96), rgba(244, 240, 232, 0.88));
  border: 1px solid rgba(176, 174, 165, 0.16);
}

.ped-avatar-wrap {
  position: relative;
  flex: 0 0 auto;
  cursor: pointer;
  border-radius: 50%;
  overflow: visible;
}

.ped-avatar-wrap :deep(.user-avatar) {
  width: 80px;
  height: 80px;
  border: 3px solid rgba(253, 254, 254, 0.9);
  box-shadow: 0 6px 16px rgba(94, 82, 72, 0.1);
}

.ped-avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(18, 17, 16, 0.42);
  color: rgba(255, 255, 255, 0.92);
  opacity: 0;
  transition: opacity 0.25s ease;
  z-index: 2;
  width: 80px;
  height: 80px;
}

.ped-avatar-wrap:hover .ped-avatar-overlay {
  opacity: 1;
}

.ped-file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 0;
  height: 0;
  overflow: hidden;
}

.ped-avatar-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.ped-avatar-hint {
  font-size: 0.94rem;
  font-weight: 600;
  color: var(--color-ink-medium);
}

.ped-avatar-limit {
  font-size: 0.82rem;
  color: rgba(107, 98, 87, 0.64);
}

.ped-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

.ped-form-grid > :first-child {
  grid-column: 1 / -1;
}

.ped-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ped-btn {
  min-width: 108px;
  min-height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform var(--transition-normal),
    box-shadow var(--transition-normal),
    background var(--transition-normal),
    color var(--transition-normal);
}

.ped-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.ped-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ped-btn--ghost {
  background: rgba(44, 62, 80, 0.08);
  color: rgba(44, 62, 80, 0.82);
}

.ped-btn--primary {
  background: linear-gradient(135deg, var(--color-vermilion), #ba392a);
  color: rgba(255, 248, 242, 0.98);
  box-shadow: 0 10px 20px rgba(192, 57, 43, 0.18);
}

@media (max-width: 640px) {
  .ped-form-grid {
    grid-template-columns: 1fr;
  }

  .ped-avatar-section {
    flex-direction: column;
    text-align: center;
  }

  .ped-avatar-upload-btn {
    align-self: center;
  }
}
</style>
