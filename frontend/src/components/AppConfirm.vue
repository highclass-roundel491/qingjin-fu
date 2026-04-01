<template>
  <Teleport to="body">
    <Transition name="confirm">
      <div v-if="modelValue" class="confirm-overlay" @click.self="handleCancel">
        <div class="confirm-dialog">
          <div class="confirm-dialog__wash"></div>

          <div class="confirm-dialog__header">
            <div class="confirm-dialog__icon" :class="`confirm-dialog__icon--${variant}`">
              {{ iconGlyph }}
            </div>
            <h3 class="confirm-dialog__title">{{ title }}</h3>
          </div>

          <p class="confirm-dialog__message">{{ message }}</p>

          <div class="confirm-dialog__actions">
            <button class="confirm-btn confirm-btn--cancel" @click="handleCancel">
              {{ cancelText }}
            </button>
            <button
              class="confirm-btn confirm-btn--confirm"
              :class="`confirm-btn--${variant}`"
              @click="handleConfirm"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'default'
}>(), {
  title: '确认操作',
  message: '确定要执行此操作吗？',
  confirmText: '确定',
  cancelText: '取消',
  variant: 'default'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

const iconGlyph = computed(() => {
  const map: Record<string, string> = {
    danger: '⚠',
    warning: '？',
    default: '◉',
  }
  return map[props.variant] || '◉'
})

function handleConfirm() {
  emit('update:modelValue', false)
  emit('confirm')
}

function handleCancel() {
  emit('update:modelValue', false)
  emit('cancel')
}
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 99998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(22,28,36,0.42);
  backdrop-filter: blur(6px);
}

.confirm-dialog {
  position: relative;
  width: 92%;
  max-width: 400px;
  padding: 32px 30px 26px;
  border-radius: 24px;
  overflow: hidden;
  background:
    radial-gradient(ellipse at top left, rgba(246,241,232,0.98), transparent 55%),
    linear-gradient(180deg, rgba(253,249,240,0.99), rgba(246,241,232,0.99));
  border: 1px solid rgba(44,62,80,0.08);
  box-shadow:
    0 32px 72px rgba(44,62,80,0.2),
    0 4px 16px rgba(44,62,80,0.08);
}

.confirm-dialog__wash {
  position: absolute;
  top: -40px;
  right: -30px;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(192,57,43,0.08), transparent 70%);
  pointer-events: none;
}

.confirm-dialog__header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.confirm-dialog__icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.confirm-dialog__icon--danger {
  background: rgba(231,76,60,0.1);
  color: var(--color-error);
}

.confirm-dialog__icon--warning {
  background: rgba(243,156,18,0.12);
  color: var(--color-warning);
}

.confirm-dialog__icon--default {
  background: rgba(44,62,80,0.07);
  color: var(--color-ink-medium);
}

.confirm-dialog__title {
  font-family: var(--font-title);
  font-size: 1.15rem;
  color: var(--color-ink-dark);
  letter-spacing: 0.04em;
}

.confirm-dialog__message {
  font-size: 0.92rem;
  line-height: 1.7;
  color: rgba(44,62,80,0.7);
  margin-bottom: 26px;
  padding-left: 58px;
}

.confirm-dialog__actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.confirm-btn {
  height: 40px;
  padding: 0 22px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 180ms cubic-bezier(0.4, 0, 0.2, 1);
}

.confirm-btn:active {
  transform: scale(0.97);
}

.confirm-btn--cancel {
  background: rgba(44,62,80,0.06);
  color: var(--color-ink-medium);
}

.confirm-btn--cancel:hover {
  background: rgba(44,62,80,0.1);
}

.confirm-btn--confirm.confirm-btn--danger {
  background: linear-gradient(135deg, var(--color-error), #c0392b);
  color: #fff;
  box-shadow: 0 4px 14px rgba(231,76,60,0.22);
}

.confirm-btn--confirm.confirm-btn--danger:hover {
  box-shadow: 0 6px 20px rgba(231,76,60,0.32);
  transform: translateY(-1px);
}

.confirm-btn--confirm.confirm-btn--warning {
  background: linear-gradient(135deg, var(--color-warning), #d4930e);
  color: #fff;
  box-shadow: 0 4px 14px rgba(243,156,18,0.22);
}

.confirm-btn--confirm.confirm-btn--warning:hover {
  box-shadow: 0 6px 20px rgba(243,156,18,0.32);
  transform: translateY(-1px);
}

.confirm-btn--confirm.confirm-btn--default {
  background: linear-gradient(135deg, var(--color-ink-dark), var(--color-ink-medium));
  color: #fff;
  box-shadow: 0 4px 14px rgba(44,62,80,0.2);
}

.confirm-btn--confirm.confirm-btn--default:hover {
  box-shadow: 0 6px 20px rgba(44,62,80,0.3);
  transform: translateY(-1px);
}

.confirm-enter-active {
  animation: overlay-in 0.28s ease;
}

.confirm-leave-active {
  animation: overlay-out 0.22s ease forwards;
}

.confirm-enter-active .confirm-dialog {
  animation: dialog-in 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}

.confirm-leave-active .confirm-dialog {
  animation: dialog-out 0.2s ease forwards;
}

@keyframes overlay-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes overlay-out {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes dialog-in {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(16px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes dialog-out {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.95) translateY(-6px);
  }
}
</style>
