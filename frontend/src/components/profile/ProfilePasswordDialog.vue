<template>
  <el-dialog
    :model-value="modelValue"
    width="520px"
    align-center
    @close="handleClose"
  >
    <template #header>
      <div class="profile-password-dialog__header">
        <p class="profile-password-dialog__eyebrow">SECURITY SETTINGS</p>
        <h3 class="profile-password-dialog__title">修改登录密码</h3>
      </div>
    </template>

    <div class="profile-password-dialog__body">
      <el-form label-position="top" class="profile-password-dialog__form">
        <el-form-item label="原密码">
          <el-input
            v-model="form.old_password"
            type="password"
            show-password
            placeholder="输入当前登录密码"
          />
        </el-form-item>

        <el-form-item label="新密码">
          <el-input
            v-model="form.new_password"
            type="password"
            show-password
            placeholder="至少 6 位字符"
          />
        </el-form-item>

        <el-form-item label="确认新密码">
          <el-input
            v-model="form.confirm_password"
            type="password"
            show-password
            placeholder="再次输入新密码"
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="profile-password-dialog__footer">
        <button
          type="button"
          class="profile-password-dialog__button profile-password-dialog__button--ghost"
          :disabled="submitting"
          @click="handleClose"
        >
          取消
        </button>
        <button
          type="button"
          class="profile-password-dialog__button profile-password-dialog__button--primary"
          :disabled="submitting"
          @click="handleSubmit"
        >
          {{ submitting ? '提交中…' : '确认修改' }}
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '@/api/user'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const submitting = ref(false)
const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const resetForm = () => {
  form.old_password = ''
  form.new_password = ''
  form.confirm_password = ''
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      resetForm()
    }
  }
)

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!form.old_password || !form.new_password || !form.confirm_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }

  if (form.new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }

  if (form.new_password !== form.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  submitting.value = true
  try {
    await userApi.changePassword({
      old_password: form.old_password,
      new_password: form.new_password
    })
    ElMessage.success('密码修改成功，请牢记新密码')
    emit('saved')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '密码修改失败')
  } finally {
    submitting.value = false
  }
 }
</script>

<style scoped>
.profile-password-dialog__header {
  display: grid;
  gap: 6px;
}

.profile-password-dialog__eyebrow {
  font-size: 0.8rem;
  letter-spacing: 0.24em;
  color: rgba(52, 73, 94, 0.64);
}

.profile-password-dialog__title {
  color: var(--color-ink-dark);
  font-size: 1.4rem;
}

.profile-password-dialog__body {
  padding-top: 4px;
}

.profile-password-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.profile-password-dialog__button {
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

.profile-password-dialog__button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.profile-password-dialog__button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.profile-password-dialog__button--ghost {
  background: rgba(44, 62, 80, 0.08);
  color: rgba(44, 62, 80, 0.82);
}

.profile-password-dialog__button--primary {
  background: linear-gradient(135deg, var(--color-vermilion), #ba392a);
  color: rgba(255, 248, 242, 0.98);
  box-shadow: 0 10px 20px rgba(192, 57, 43, 0.18);
}
</style>
