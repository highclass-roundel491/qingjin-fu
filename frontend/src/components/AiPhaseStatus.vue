<template>
  <div class="ai-phase-status" :class="{ 'ai-phase-status--dense': dense }">
    <div class="ai-phase-status__head">
      <span class="ai-phase-status__dot"></span>
      <span class="ai-phase-status__title">{{ title }}</span>
      <span class="ai-phase-status__badge">{{ currentStageText }}</span>
    </div>
    <div v-if="stages.length" class="ai-phase-status__steps">
      <div
        v-for="(stage, idx) in stages"
        :key="`${stage}-${idx}`"
        class="ai-phase-status__step"
        :class="{
          'is-active': idx === current,
          'is-done': idx < current
        }"
      >
        <span class="ai-phase-status__index">{{ idx + 1 }}</span>
        <span class="ai-phase-status__label">{{ stage }}</span>
      </div>
    </div>
    <p v-if="hint" class="ai-phase-status__hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  stages?: string[]
  current?: number
  hint?: string
  dense?: boolean
}>(), {
  title: '翰林处理中',
  stages: () => [],
  current: 0,
  hint: '',
  dense: false,
})

const currentStageText = computed(() => {
  if (!props.stages.length) return '进行中'
  const idx = Math.max(0, Math.min(props.current, props.stages.length - 1))
  return props.stages[idx]
})
</script>

<style scoped>
.ai-phase-status {
  margin-top: 10px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(166, 122, 58, 0.22);
  background: linear-gradient(135deg, rgba(255, 249, 239, 0.92), rgba(248, 238, 220, 0.88));
}

.ai-phase-status--dense {
  margin-top: 8px;
  padding: 10px;
}

.ai-phase-status__head {
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1;
}

.ai-phase-status__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #b7791f;
  box-shadow: 0 0 0 6px rgba(183, 121, 31, 0.12);
}

.ai-phase-status__title {
  font-size: 13px;
  font-weight: 700;
  color: #6d4b1f;
}

.ai-phase-status__badge {
  margin-left: auto;
  font-size: 12px;
  color: #8a642d;
  background: rgba(255, 255, 255, 0.72);
  padding: 4px 8px;
  border-radius: 999px;
}

.ai-phase-status__steps {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.ai-phase-status__step {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9a7a49;
}

.ai-phase-status__step.is-active {
  color: #6d4b1f;
}

.ai-phase-status__step.is-done {
  color: #7a5c2f;
}

.ai-phase-status__index {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  background: rgba(166, 122, 58, 0.16);
}

.ai-phase-status__step.is-active .ai-phase-status__index {
  background: rgba(166, 122, 58, 0.32);
}

.ai-phase-status__label {
  font-size: 12px;
}

.ai-phase-status__hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #8e6f41;
}
</style>
