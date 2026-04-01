<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="app-toast" :class="`app-toast--${type}`" @click="dismiss">
        <div class="app-toast__icon">{{ iconGlyph }}</div>
        <span class="app-toast__text">{{ message }}</span>
        <div class="app-toast__progress" :style="{ animationDuration: `${duration}ms` }"></div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'

const props = defineProps<{
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = computed(() => props.modelValue)

const iconGlyph = computed(() => {
  const map: Record<string, string> = {
    success: '✓',
    error: '✗',
    warning: '！',
    info: '◈',
  }
  return map[props.type || 'success'] || '✓'
})

const duration = computed(() => props.duration || 2800)

let timer: ReturnType<typeof setTimeout> | null = null

function dismiss() {
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (val) => {
  if (timer) clearTimeout(timer)
  if (val) {
    timer = setTimeout(() => {
      emit('update:modelValue', false)
    }, duration.value)
  }
})
</script>

<style scoped>
.app-toast {
  position: fixed;
  bottom: 36px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 26px 14px 18px;
  border-radius: 16px;
  font-size: 0.92rem;
  font-weight: 500;
  z-index: 99999;
  cursor: pointer;
  overflow: hidden;
  backdrop-filter: blur(18px);
  box-shadow:
    0 16px 48px rgba(0,0,0,0.18),
    0 2px 8px rgba(0,0,0,0.08),
    inset 0 1px 0 rgba(255,255,255,0.08);
}

.app-toast--success {
  background: linear-gradient(135deg, rgba(44,62,80,0.94), rgba(52,73,94,0.94));
  color: rgba(255,250,243,0.95);
}

.app-toast--error {
  background: linear-gradient(135deg, rgba(192,57,43,0.92), rgba(176,48,36,0.94));
  color: rgba(255,250,243,0.97);
}

.app-toast--warning {
  background: linear-gradient(135deg, rgba(196,151,56,0.92), rgba(180,135,46,0.94));
  color: rgba(255,250,243,0.97);
}

.app-toast--info {
  background: linear-gradient(135deg, rgba(22,160,133,0.9), rgba(18,140,116,0.94));
  color: rgba(255,250,243,0.97);
}

.app-toast__icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 700;
  flex-shrink: 0;
}

.app-toast--success .app-toast__icon {
  background: rgba(39,174,96,0.28);
}

.app-toast--error .app-toast__icon {
  background: rgba(255,255,255,0.14);
}

.app-toast--warning .app-toast__icon {
  background: rgba(255,255,255,0.16);
}

.app-toast--info .app-toast__icon {
  background: rgba(255,255,255,0.16);
}

.app-toast__text {
  line-height: 1.4;
  letter-spacing: 0.02em;
}

.app-toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: rgba(255,255,255,0.28);
  border-radius: 0 0 16px 16px;
  animation: toast-shrink linear forwards;
}

@keyframes toast-shrink {
  from { width: 100%; }
  to { width: 0%; }
}

.toast-enter-active {
  animation: toast-in 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}

.toast-leave-active {
  animation: toast-out 0.26s cubic-bezier(0.55, 0, 1, 0.45) forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(18px) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateX(-50%) translateY(-8px) scale(0.96);
  }
}
</style>
