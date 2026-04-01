<template>
  <button type="button" class="app-back-button" :class="`app-back-button--${tone}`" @click="goBack">
    <span class="app-back-button__icon-wrap">
      <img :src="chainLinkIcon" class="app-back-button__icon" alt="" />
    </span>
    <span class="app-back-button__content">
      <span class="app-back-button__eyebrow">BACK</span>
      <span class="app-back-button__label">{{ label }}</span>
    </span>
  </button>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import chainLinkIcon from '@/assets/icons/relay/chain-link.svg'

const props = withDefaults(defineProps<{
  label?: string
  fallbackTo?: string
  tone?: 'dark' | 'light'
}>(), {
  label: '返回上一页',
  fallbackTo: '/',
  tone: 'dark'
})

const tone = props.tone

const router = useRouter()

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push(props.fallbackTo)
}
</script>

<style scoped>
.app-back-button {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding: 8px 16px 8px 10px;
  border-radius: 18px;
  border: 1px solid rgba(240, 210, 155, 0.22);
  background: linear-gradient(135deg, rgba(255, 246, 231, 0.12), rgba(255, 255, 255, 0.04));
  color: #fff4e1;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

.app-back-button:hover {
  transform: translateY(-1px);
  border-color: rgba(240, 210, 155, 0.42);
  background: linear-gradient(135deg, rgba(255, 246, 231, 0.2), rgba(255, 255, 255, 0.08));
  box-shadow: 0 10px 26px rgba(35, 24, 17, 0.18);
}

.app-back-button__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: rgba(240, 210, 155, 0.12);
  border: 1px solid rgba(240, 210, 155, 0.16);
  flex-shrink: 0;
}

.app-back-button__icon {
  width: 16px;
  height: 16px;
  filter: brightness(0) saturate(100%) invert(93%) sepia(17%) saturate(549%) hue-rotate(329deg) brightness(104%) contrast(96%);
}

.app-back-button__content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
}

.app-back-button__eyebrow {
  font-size: 10px;
  letter-spacing: 0.2em;
  color: rgba(255, 240, 214, 0.56);
}

.app-back-button__label {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.app-back-button--light {
  border-color: rgba(125, 87, 52, 0.14);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(247, 241, 233, 0.88));
  color: rgba(58, 50, 44, 0.86);
  box-shadow: 0 8px 18px rgba(94, 82, 72, 0.06);
}

.app-back-button--light:hover {
  border-color: rgba(217, 119, 87, 0.28);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(249, 244, 237, 0.94));
  box-shadow: 0 12px 24px rgba(94, 82, 72, 0.08);
}

.app-back-button--light .app-back-button__icon-wrap {
  background: rgba(217, 119, 87, 0.1);
  border-color: rgba(217, 119, 87, 0.14);
}

.app-back-button--light .app-back-button__icon {
  filter: brightness(0) saturate(100%) invert(40%) sepia(19%) saturate(1703%) hue-rotate(338deg) brightness(95%) contrast(86%);
}

.app-back-button--light .app-back-button__eyebrow {
  color: rgba(125, 87, 52, 0.46);
}

@media (max-width: 640px) {
  .app-back-button {
    min-height: 48px;
    padding-right: 14px;
  }

  .app-back-button__eyebrow {
    display: none;
  }
}
</style>
