<template>
  <div class="user-avatar" :class="sizeClass" @click="handleClick">
    <img v-if="resolvedAvatar" :src="resolvedAvatar" :alt="username" class="avatar-img" @error="handleAvatarError" />
    <DefaultAvatar v-else :username="username" :size="size" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import DefaultAvatar from './DefaultAvatar.vue'
import { resolveUploadUrl } from '@/utils/url'

interface Props {
  username: string
  avatar?: string | null
  size?: 'small' | 'medium' | 'large'
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  clickable: false
})

const emit = defineEmits<{
  click: []
}>()

const avatarLoadFailed = ref(false)
const resolvedAvatar = computed(() => {
  if (avatarLoadFailed.value) return null
  return resolveUploadUrl(props.avatar)
})
const sizeClass = computed(() => `avatar-${props.size}`)

watch(() => props.avatar, () => {
  avatarLoadFailed.value = false
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}

const handleAvatarError = () => {
  avatarLoadFailed.value = true
}
</script>

<style scoped>
.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.user-avatar::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  padding: 2px;
  background: linear-gradient(135deg, #c0392b, #16a085, #8e44ad);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.user-avatar:hover::before {
  opacity: 1;
  animation: rotate 3s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.user-avatar.avatar-small {
  width: 36px;
  height: 36px;
}

.user-avatar.avatar-medium {
  width: 44px;
  height: 44px;
}

.user-avatar.avatar-large {
  width: 72px;
  height: 72px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: relative;
  z-index: 1;
}

.user-avatar:hover {
  transform: scale(1.08) rotate(2deg);
  filter: brightness(1.05);
}

.user-avatar:active {
  transform: scale(0.95);
}
</style>
